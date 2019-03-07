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
from functools import partial
from collections import namedtuple


PYPI_TEMPLATE = """
SUMMARY = "{summary}"
HOMEPAGE = "{homepage}"
AUTHOR = "{author} <{author_email}>"
LICENSE = "{license}"
LIC_FILES_CHKSUM = "file://{license_file};md5={license_md5sum}"

SRC_URI = "{src_uri}"
SRC_URI[md5sum] = "{md5sum}"
SRC_URI[sha256sum] = "{sha256sum}"

S = "${{WORKDIR}}/{src_dir}"

RDEPENDS_${{PN}} = "{dependencies}"

inherit setuptools{setuptools}
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
        "license_md5sum",
        "src_dir",
        "src_uri",
        "src_md5sum",
        "src_sha256sum",
        "dependencies",
    ],
)


def compute_md5(path):
    with open(path, mode="rb") as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b""):
            d.update(buf)
    return d.hexdigest()


def compute_sha256(path):
    with open(path, mode="rb") as f:
        d = hashlib.sha256()
        for buf in iter(partial(f.read, 128), b""):
            d.update(buf)
    return d.hexdigest()


def package_to_bb_name(package):
    return package.lower().replace("_", "-").replace(".", "-")


def unpack_package(file):
    tmpdir = "{}.d".format(file)

    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)

    os.mkdir(tmpdir)

    if ".tar." in file:
        with tarfile.open(file, "r") as infile:
            infile.extractall(path=tmpdir)
    elif ".zip" in file:
        with zipfile.ZipFile.open(file, "r") as infile:
            infile.extractall(path=tmpdir)
    else:
        raise Exception("Cannot process: {}".format(file))

    return tmpdir


def get_package_file_info(package, version, uri):
    output = "/tmp/{}_{}.tar.gz".format(package, version)

    if os.path.exists(output):
        os.remove(output)

    urllib.request.urlretrieve(uri, output)

    tmpdir = unpack_package(output)
    src_dir = os.listdir(tmpdir)[0]

    src_files = os.listdir("{}/{}".format(tmpdir, src_dir))

    try:
        license_file = [
            f for f in src_files if "license" in f.lower() or "copying" in f.lower()
        ][0]
    except:
        license_file = "setup.py"

    license_path = os.path.join(tmpdir, src_dir, license_file)
    license_md5sum = compute_md5(license_path)

    return (
        compute_md5(output),
        compute_sha256(output),
        src_dir,
        license_file,
        license_md5sum,
    )


def get_package_dependencies(info):
    deps = []

    requires_dist = info["info"]["requires_dist"]

    if requires_dist:
        for dep in requires_dist:
            if "extra ==" in dep:
                continue

            version_search = re.findall("\((>=|==|<=)(.+)\)", dep)
            package = dep.split(" ")[0]
            version = None
            if version_search:
                version = version_search[0][1]

            deps.append((package, version))

    return deps


def get_package_info(package, version=None, packages=None):
    print("  {}{}".format(package, "=={}".format(version) if version else ""))

    if not packages:
        packages = [[]]
    elif package in [package.name for package in packages[0]]:
        return packages[0]

    try:
        if version:
            url = "https://pypi.org/pypi/{}/{}/json".format(package, version)
        else:
            url = "https://pypi.org/pypi/{}/json".format(package)

        response = urllib.request.urlopen(url).read().decode(encoding='UTF-8')
        info = json.loads(response)

        name = package
        version = info["info"]["version"]
        summary = info["info"]["summary"]
        homepage = info["info"]["home_page"]
        author = info["info"]["author"]
        author_email = info["info"]["author_email"]
        license = info["info"]["license"].replace(" ", "-")

        version_info = next(
            i for i in info["releases"][version] if i["packagetype"] == "sdist"
        )

        src_uri = version_info["url"]
        src_md5sum, src_sha256sum, src_dir, license_file, license_md5sum = get_package_file_info(
            package, version, src_uri
        )

        dependencies = get_package_dependencies(info)

        package = Package(
            name,
            version,
            summary,
            homepage,
            author,
            author_email,
            license,
            license_file,
            license_md5sum,
            src_dir,
            src_uri,
            src_md5sum,
            src_sha256sum,
            dependencies,
        )

        packages[0].append(package)

        for dependency in dependencies:
            get_package_info(dependency[0], version=dependency[1], packages=packages)

    except Exception as e:
        print("  Failed to gather {} ({})".format(package, str(e)))

    return packages[0]


def generate_recipe(package, outdir, python):
    basename = "{}-{}_{}.bb".format(
        python, package_to_bb_name(package.name), package.version
    )
    bbfile = os.path.join(outdir, basename)

    print("  {}".format(basename))

    output = PYPI_TEMPLATE.format(
        summary=package.summary,
        md5sum=package.src_md5sum,
        sha256sum=package.src_sha256sum,
        src_uri=package.src_uri,
        src_dir=package.src_dir,
        license=package.license,
        license_file=package.license_file,
        license_md5sum=package.license_md5sum,
        homepage=package.homepage,
        author=package.author,
        author_email=package.author_email,
        dependencies=" ".join(
            ["{}-{}".format(python, dep[0]) for dep in package.dependencies]
        ),
        setuptools="3" if python == "python3" else "",
    )

    with open(bbfile, "w") as outfile:
        outfile.write(output)


def parse_requirements(requirements_file):
    packages = []

    with open(requirements_file, "r") as infile:
        for package in infile.read().split("\n"):
            package = package.strip()
            if package:
                if not (package.startswith("-e") or package.startswith(".")):
                    parts = [part.strip() for part in package.split("==")]
                    if len(parts) == 2:
                        packages += get_package_info(parts[0], parts[1])
                    elif len(parts) == 1:
                        packages += get_package_info(parts[0], None)
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


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--package", "-p", help="The package to process.")
        parser.add_argument(
            "--version", "-v", help="The package version.", default=None
        )
        parser.add_argument("--requirements", "-r", help="The pypi requirements file.")
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
        args = parser.parse_args()

        print("Gathering info:")
        packages = []
        if args.requirements:
            packages = parse_requirements(args.requirements)
        elif args.package:
            packages = get_package_info(args.package, args.version)
        else:
            raise Exception("No packages provided!")

        print("Generating recipes:")
        for package in packages:
            generate_recipe(package, args.outdir, args.python)

        version_file = os.path.join(args.outdir, "{}-versions.inc".format(args.python))
        write_preferred_versions(packages, version_file, args.python)

        print("\nPREFERRED_VERSIONS are available in: {}".format(version_file))

    except Exception as e:
        print(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        os._exit(1)


if __name__ == "__main__":
    main()
