# Dependencies and licenses

The interactive package uses these third-party components:

| Dependency | Supported version | License | Purpose |
|---|---|---|---|
| `ijson` | `>=3.2,<4` | BSD 3-Clause | Reads the display fields from large FES and clustering reports without loading their assignments into memory |
| `salsbury-md-analysis` | `>=0.1.2,<0.2` | BSD 3-Clause | Produces the analysis reports consumed by this viewer |
| `3Dmol.js` | `2.5.5` (bundled) | BSD 3-Clause | Renders offline molecular cartoons, bonded ligands and cofactors, and space-filling ions |

The report bundles 3Dmol.js so molecular views work offline. The upstream
license is retained in `third_party/3Dmol-LICENSE.txt`. The report does not
download a font, analytics service, or runtime JavaScript.

The core package is not on PyPI. The installation examples therefore supply
the core and interactive GitHub requirements together. External executables
remain separate. In particular, pip does not install `mkdssp`; protein
secondary-structure analysis requires the conda-forge `dssp` package or another
compatible DSSP installation.

Dependencies of the core analysis package are documented in that package’s
[`DEPENDENCIES_AND_LICENSES.md`](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/DEPENDENCIES_AND_LICENSES.md).
