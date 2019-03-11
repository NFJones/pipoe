#!/usr/bin/env python3

import argparse
import os
import re
import sys
import urllib.request
import hashlib
import shutil
import json
import tarfile
import zipfile
import platform
import parsley
from pep508_parser import parser
from pipoe import licenses
from functools import partial
from collections import namedtuple
from pprint import pformat


BB_TEMPLATE = """
SUMMARY = "{summary}"
HOMEPAGE = "{homepage}"
AUTHOR = "{author} <{author_email}>"
LICENSE = "{license}"
LIC_FILES_CHKSUM = "file://{license_file};md5={license_md5}"

SRC_URI = "{src_uri}"
SRC_URI[md5sum] = "{md5}"
SRC_URI[sha256sum] = "{sha256}"

S = "${{WORKDIR}}/{src_dir}"

RDEPENDS_${{PN}} = "{dependencies}"

inherit setuptools{setuptools}
"""

BB_EXTRA_TEMPLATE = """
SUMMARY = "{summary}"
HOMEPAGE = "{homepage}"
AUTHOR = "{author} <{author_email}>"

RDEPENDS_${{PN}} = "{dependencies}"

inherit packagegroup
"""


Package = namedtuple(
    "Package",
    [
        "name",
        "version",
        "summary",
        "homepage",
        "author",
        "author_email",
        "license",
        "license_file",
        "license_md5",
        "src_dir",
        "src_uri",
        "src_md5",
        "src_sha256",
        "dependencies",
    ],
)

Dependency = namedtuple("Dependency", ["name", "version", "extra"])


def md5sum(path):
    with open(path, mode="rb") as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b""):
            d.update(buf)
    return d.hexdigest()


def sha256sum(path):
    with open(path, mode="rb") as f:
        d = hashlib.sha256()
        for buf in iter(partial(f.read, 128), b""):
            d.update(buf)
    return d.hexdigest()


def package_to_bb_name(package):
    return package.lower().replace("_", "-").replace(".", "-")


def translate_license(license, default_license):
    try:
        return licenses.LICENSES[license]
    except:
        if default_license:
            return default_license

        print("Failed to translate license: {}".format(license))
        mapping = input("Please enter a valid license name: ")
        licenses.LICENSES[license] = mapping
        return mapping


def unpack_package(file):
    tmpdir = "{}.d".format(file)

    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)

    os.mkdir(tmpdir)
    shutil.unpack_archive(file, extract_dir=tmpdir)

    return tmpdir


def get_file_extension(uri):
    extensions = ["tar", "tar.gz", "tar.bz2", "tar.xz", "zip"]
    for extension in extensions:
        if uri.endswith(extension):
            return extension
    raise Exception("Extension not supported: {}".format(uri))


def get_package_file_info(package, version, uri):
    extension = get_file_extension(uri)
    output = "/tmp/{}_{}.{}".format(package, version, extension)

    if os.path.exists(output):
        os.remove(output)

    urllib.request.urlretrieve(uri, output)

    tmpdir = unpack_package(output)
    src_dir = os.listdir(tmpdir)[0]

    src_files = os.listdir("{}/{}".format(tmpdir, src_dir))

    try:
        license_file = next(
            f
            for f in src_files
            if ("license" in f.lower() or "copying" in f.lower())
            and not os.path.isdir(os.path.join(tmpdir, src_dir, f))
        )
    except:
        license_file = "setup.py"

    license_path = os.path.join(tmpdir, src_dir, license_file)
    license_md5 = md5sum(license_path)
    src_md5 = md5sum(output)
    src_sha256 = sha256sum(output)

    os.remove(output)
    shutil.rmtree(tmpdir)

    return (src_md5, src_sha256, src_dir, license_file, license_md5)


def decide_version(spec):
    version = spec[2]
    if version:
        version = version[0]
        relation = version[0]
        version = version[1]

        if relation == "==":
            return version
        elif relation == ">=":
            return None
        elif relation == "<=":
            return version
        else:
            return None
    else:
        return None


def decide_extra(spec):
    extra = spec[3]
    if extra:
        if extra[0] == "and":
            return extra[2][2]
        else:
            return extra[2]
    else:
        return None


def parse_requires_dist(requires_dist):
    spec = parser.parse(requires_dist)
    ret = Dependency(spec[0], decide_version(spec), decide_extra(spec))
    return ret


def get_package_dependencies(info, follow_extras=False):
    deps = []

    requires_dist = info["info"]["requires_dist"]

    if requires_dist:
        for dep in requires_dist:
            d = parse_requires_dist(dep)
            if d.extra and not follow_extras:
                continue
            deps.append(d)

    return deps


PROCESSED_PACKAGES = []


def get_package_info(
    package,
    version=None,
    packages=None,
    indent=0,
    extra=None,
    follow_extras=False,
    default_license=None,
):
    global PROCESSED_PACKAGES

    if not packages:
        packages = [[]]
    elif package in [package.name for package in PROCESSED_PACKAGES] or package in [
        package.name for package in packages[0]
    ]:
        return packages[0]

    indent_str = ""
    if indent:
        indent_str = "|" + (indent - 2) * "-" + " "

    extra_str = ""
    if extra:
        extra_str = "[{}]".format(extra)

    print(
        "  {}{}{}{}".format(
            indent_str, package, extra_str, "=={}".format(version) if version else ""
        )
    )

    try:
        if version:
            url = "https://pypi.org/pypi/{}/{}/json".format(package, version)
        else:
            url = "https://pypi.org/pypi/{}/json".format(package)

        response = urllib.request.urlopen(url).read().decode(encoding="UTF-8")
        info = json.loads(response)

        name = package
        version = info["info"]["version"]
        summary = info["info"]["summary"]
        homepage = info["info"]["home_page"]
        author = info["info"]["author"]
        author_email = info["info"]["author_email"]
        license = translate_license(info["info"]["license"], default_license)

        try:
            version_info = next(
                i for i in info["releases"][version] if i["packagetype"] == "sdist"
            )
        except:
            raise Exception("No sdist package can be found.")

        src_uri = version_info["url"]
        src_md5, src_sha256, src_dir, license_file, license_md5 = get_package_file_info(
            package, version, src_uri
        )

        dependencies = get_package_dependencies(info, follow_extras=follow_extras)

        package = Package(
            name,
            version,
            summary,
            homepage,
            author,
            author_email,
            license,
            license_file,
            license_md5,
            src_dir,
            src_uri,
            src_md5,
            src_sha256,
            dependencies,
        )

        packages[0].append(package)
        PROCESSED_PACKAGES.append(package)

        for dependency in dependencies:
            get_package_info(
                dependency.name,
                version=dependency.version,
                packages=packages,
                indent=indent + 2,
                extra=dependency.extra,
                follow_extras=follow_extras,
                default_license=default_license,
            )

    except Exception as e:
        print(
            "  {} [ERROR] Failed to gather {} ({})".format(indent_str, package, str(e))
        )

    return packages[0]


def generate_recipe(package, outdir, python, is_extra=False):
    basename = "{}-{}_{}.bb".format(
        python, package_to_bb_name(package.name), package.version
    )
    bbfile = os.path.join(outdir, basename)

    print("  {}".format(basename))

    if is_extra:
        output = BB_EXTRA_TEMPLATE.format(
            summary=package.summary,
            homepage=package.homepage,
            author=package.author,
            author_email=package.author_email,
            dependencies=" ".join(
                [
                    "{}-{}".format(python, package_to_bb_name(dep.name))
                    for dep in package.dependencies
                ]
            ),
        )
    else:
        output = BB_TEMPLATE.format(
            summary=package.summary,
            md5=package.src_md5,
            sha256=package.src_sha256,
            src_uri=package.src_uri,
            src_dir=package.src_dir,
            license=package.license,
            license_file=package.license_file,
            license_md5=package.license_md5,
            homepage=package.homepage,
            author=package.author,
            author_email=package.author_email,
            dependencies=" ".join(
                [
                    "{}-{}".format(python, package_to_bb_name(dep.name))
                    for dep in package.dependencies
                ]
            ),
            setuptools="3" if python == "python3" else "",
        )

    with open(bbfile, "w") as outfile:
        outfile.write(output)


def parse_requirements(requirements_file, follow_extras=False, default_license=None):
    packages = []

    with open(requirements_file, "r") as infile:
        for package in infile.read().split("\n"):
            package = package.strip()
            if package:
                if not (package.startswith("-e") or package.startswith(".")):
                    parts = [part.strip() for part in package.split("==")]
                    if len(parts) == 2:
                        packages += get_package_info(
                            parts[0],
                            parts[1],
                            follow_extras=follow_extras,
                            default_license=default_license,
                        )
                    elif len(parts) == 1:
                        packages += get_package_info(
                            parts[0],
                            None,
                            follow_extras=follow_extras,
                            default_license=default_license,
                        )
                    else:
                        print("    Unparsed package: {}".format(package))
                else:
                    print("    Skipping: {}".format(package))

    return packages


def write_preferred_versions(packages, outfile, python):
    versions = []
    for package in packages:
        versions.append(
            'PREFERRED_VERSION_{}-{} = "{}"'.format(
                python, package_to_bb_name(package.name), package.version
            )
        )

    with open(outfile, "w") as outfile:
        outfile.write("\n".join(versions))


def generate_recipes(packages, outdir, python, follow_extras=False):
    for package in packages:
        generate_recipe(package, outdir, python)

        if follow_extras:
            extras = [dep for dep in package.dependencies if dep.extra]
            processed = []
            for extra in extras:
                if extra.extra in processed:
                    continue

                processed.append(extra.extra)
                extra_package = package
                extra_package = extra_package._replace(
                    name=package.name + "-{}".format(extra.extra)
                )
                extra_package = extra_package._replace(
                    dependencies=[Dependency(package.name, package.version, None)]
                    + [
                        Dependency(e.name, e.version, None)
                        for e in extras
                        if e.extra == extra.extra
                    ]
                )
                generate_recipe(extra_package, outdir, python, is_extra=True)


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--package", "-p", help="The package to process.")
        parser.add_argument(
            "--version", "-v", help="The package version.", default=None
        )
        parser.add_argument("--requirements", "-r", help="The pypi requirements file.")
        parser.add_argument(
            "--extras", "-e", action="store_true", help="Generate recipes for extras."
        )
        parser.add_argument(
            "--outdir", "-o", help="The recipe directory.", default="./"
        )
        parser.add_argument(
            "--python",
            "-y",
            help="The python version to use.",
            default="python",
            choices=["python", "python3"],
        )
        parser.add_argument(
            "--licenses",
            "-l",
            action="store_true",
            help="Output an updated license map upon completion.",
        )
        parser.add_argument(
            "--default-license",
            "-d",
            help="The default license to use when the package license cannot be mapped.",
            default=None,
        )
        args = parser.parse_args()

        print("Gathering info:")
        packages = []
        if args.requirements:
            packages = parse_requirements(
                args.requirements,
                follow_extras=args.extras,
                default_license=args.default_license,
            )
        elif args.package:
            packages = get_package_info(
                args.package,
                args.version,
                follow_extras=args.extras,
                default_license=args.default_license,
            )
        else:
            raise Exception("No packages provided!")

        print("Generating recipes:")
        generate_recipes(packages, args.outdir, args.python, args.extras)

        version_file = os.path.join(args.outdir, "{}-versions.inc".format(args.python))
        write_preferred_versions(packages, version_file, args.python)

        print()
        if args.licenses:
            license_file = os.path.join(args.outdir, "licenses.py")
            with open(license_file, "w") as outfile:
                outfile.write("LICENSES = " + pformat(licenses.LICENSES))

            print("License mappings are available in: {}".format(license_file))

        print("PREFERRED_VERSIONS are available in: {}".format(version_file))

    except Exception as e:
        print(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        os._exit(1)


if __name__ == "__main__":
    main()
