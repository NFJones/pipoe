# genpybb

The objective of this project is to make creating OpenEmbedded python recipes just a bit easier. `genpybb` will take either a single package name or a requirements file and recursively generate bitbake recipes for every pypi package listed. It is not guaranteed that it will work for every package. Additionally, many recipes will still require additional modification after generation (patches, overrides, appends, etc.).

# Example

```
> usage: genpybb.py [-h] [--package PACKAGE] [--version VERSION]
                  [--requirements REQUIREMENTS] [--outdir OUTDIR]
                  [--print-preferred] [--python {python,python3}]

optional arguments:
  -h, --help            show this help message and exit
  --package PACKAGE, -p PACKAGE
                        The package to process.
  --version VERSION, -v VERSION
                        The package version.
  --requirements REQUIREMENTS, -r REQUIREMENTS
                        The pypi requirements file.
  --outdir OUTDIR, -o OUTDIR
                        The recipe directory.
  --python {python,python3}, -y {python,python3}
                        The python version to use.

> genpybb --package requests --python python3
Gathering info:
  requests
  chardet
  idna
  urllib3
  certifi==2017.4.17
Generating recipes:
  python3-requests_2.21.0.bb
  python3-chardet_3.0.4.bb
  python3-idna_2.8.bb
  python3-urllib3_1.24.1.bb
  python3-certifi_2017.4.17.bb

PREFERRED_VERSIONS are available in: ./python3-versions.inc
```
