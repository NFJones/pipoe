# genpybb

The objective of this project is to make creating OpenEmbedded python recipes just a bit easier. `genpybb` will take either a single package name or a requirements file and recursively generate bitbake recipes for every pypi package listed. It is not guaranteed that it will work for every package. Additionally, many recipes will still require additional modification after generation (patches, overrides, appends, etc.).

# Example

```
> genpybb --help
usage: genpybb [-h] [--package PACKAGE] [--version VERSION]
               [--requirements REQUIREMENTS] [--extras] [--outdir OUTDIR]
               [--python {python,python3}]

optional arguments:
  -h, --help            show this help message and exit
  --package PACKAGE, -p PACKAGE
                        The package to process.
  --version VERSION, -v VERSION
                        The package version.
  --requirements REQUIREMENTS, -r REQUIREMENTS
                        The pypi requirements file.
  --extras, -e          Generate recipes for extras.
  --outdir OUTDIR, -o OUTDIR
                        The recipe directory.
  --python {python,python3}, -y {python,python3}
                        The python version to use.
> genpybb -p requests
Gathering info:
  requests
  | chardet
  | idna
  | urllib3
  | certifi
Generating recipes:
  python-requests_2.21.0.bb
  python-chardet_3.0.4.bb
  python-idna_2.8.bb
  python-urllib3_1.24.1.bb
  python-certifi_2018.11.29.bb

License mappings are available in: ./licenses.py
PREFERRED_VERSIONS are available in: ./python-versions.inc
```
