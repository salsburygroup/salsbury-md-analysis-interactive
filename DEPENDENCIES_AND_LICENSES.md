# Dependencies and licenses

The interactive package has one required third-party package:

| Dependency | Supported version | License | Purpose |
|---|---|---|---|
| `salsbury-md-analysis` | `>=0.1.1,<0.2` | BSD 3-Clause | Produces the analysis reports consumed by this viewer |

The viewer implementation itself uses only the Python standard library. Browser
rendering uses embedded JavaScript and CSS written for this project; it does not
download or bundle a JavaScript framework, molecular viewer, font, or analytics
service.

The core package is not on PyPI. The installation examples therefore supply
the core and interactive GitHub requirements together. External executables
remain separate. In particular, pip does not install `mkdssp`; protein
secondary-structure analysis requires the conda-forge `dssp` package or another
compatible DSSP installation.

Dependencies of the core analysis package are documented in that package’s
[`DEPENDENCIES_AND_LICENSES.md`](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/DEPENDENCIES_AND_LICENSES.md).
