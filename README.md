# pipoe

The objective of this project is to make creating OpenEmbedded python recipes just a bit easier. `pipoe` will take either a single package name or a requirements file and recursively generate bitbake recipes for every pypi package listed. It is not guaranteed that it will work for every package. Additionally, many recipes will still require additional modification after generation (patches, overrides, appends, etc.). In those cases it is recommended that the user add these modifications in a bbappend file.

## Licenses

Licensing within OE is typically pretty strict. `pipoe` contains a license map which will attempt to map a packages license to one that will be accepted by the OE framework. If a license string is found which cannot be mapped, the user will be prompted to enter a valid license name. This name will be saved and the updated map will be saved to `./licenses.py` It is recommended that this file be PR'ed to this repository when generally useful changes are made.

## Extras
`pipoe` supports generating "extra" recipes based on the extra feature declarations in the packages `requires_dist` field (i.e. urllib3\[secure\]). These recipes are generated as packagegroups which rdepend on the base package.


## Versions
By default `pipoe` will generate a recipe for the newest version of a package. Supplying the `--version` argument will override this behavior. Additionally, `pipoe` will automatically parse versions from requirements files.

## Example

```
> pipoe --help
usage: pipoe [-h] [--package PACKAGE] [--version VERSION]
             [--requirements REQUIREMENTS] [--extras] [--outdir OUTDIR]
             [--python {python,python3}] [--licenses]
             [--default-license DEFAULT_LICENSE]

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
  --licenses, -l        Output an updated license map upon completion.
  --default-license DEFAULT_LICENSE, -d DEFAULT_LICENSE
                        The default license to use when the package license
                        cannot be mapped.
> pipoe -p requests
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
