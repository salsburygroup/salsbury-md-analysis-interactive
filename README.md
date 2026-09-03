# Salsbury MD Analysis Interactive

`salsbury-md-analysis-interactive` is the optional results browser for
[`salsbury-md-analysis`](https://github.com/salsburygroup/salsbury-md-analysis).
It turns a completed analysis directory into a self-contained HTML report with
prioritized findings, complete module accounting, QC, FES and clustering views,
resource and sampling tables, and representative molecular structures.

The analysis package and viewer have separate commands. Use
`salsbury-md-analysis` to analyze trajectories. Use this package after that run
finishes to browse its results.

## Install

Current releases are GitHub source distributions. This command installs both
without making source checkouts:

```bash
python -m pip install \
  "salsbury-md-analysis @ git+https://github.com/salsburygroup/salsbury-md-analysis.git@main" \
  "salsbury-md-analysis-interactive @ git+https://github.com/salsburygroup/salsbury-md-analysis-interactive.git@main"
```

The interactive package declares `salsbury-md-analysis>=0.1.1,<0.2` as a
dependency. Both GitHub requirements appear above because that dependency is
not published on PyPI. A source checkout is needed only for development or for
bundled teaching files such as the NEMO tutorial trajectory.

`mkdssp` is an external executable, so pip cannot install it with the Python
packages. Protein secondary-structure analysis requires the `dssp` package
from conda-forge or another working `mkdssp` installation. The core repository's
[`environment.yml`](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/environment.yml)
installs the reviewed DSSP version.

## Run the analysis, then build the report

The interactive command does not analyze raw trajectories. Run the core
workflow first and wait for it to finish. Then point the viewer at the completed
analysis directory:

```bash
salsbury-md-analysis-interactive path/to/completed-analysis
```

Open `path/to/completed-analysis/interactive-report/index.html` in a current
browser. The report does not need a web server or internet connection and does
not send structures or results to an external service.

Generation is immutable. If an interactive report already exists, its manifest
and HTML checksum must validate before it is reused. Changed or partial output
fails closed instead of being overwritten.

## What the report shows

The browser opens with the picker’s prioritized findings. A finding links to
its analysis tab and, when available, to a figure or representative structure.
Free-energy surfaces come first in the molecular-states view. Clustering
methods follow from highest to lowest silhouette score, with each method named,
each system’s cluster populations tabulated, and exported cluster structures
shown beside the result.

Each analysis class has its own tab. QC errors and warnings stay in the QC tab;
review notes from clustering or another scientific method stay with that
method. Internal view identifiers are replaced by readable names.

The molecular viewer packages complete non-solvent structures. Its bundled
3Dmol.js renderer draws polymers as a NewCartoon-style ribbon, ligands and
cofactors as bonded atoms, and ions as space-filling spheres. The underlying
PDB remains available beside the viewer.

The opening page shows 10–12 headline findings. Ten are always shown; the
picker adds an eleventh or twelfth only when supported statistical significance
reaches that ranking boundary. Secondary findings bring the highlighted total
to 50 when enough candidates exist. Every other candidate remains available in
the searchable browser and the core JSON and CSV files.

The report copies the JSON, PDB, and figure files needed by its links into an
`evidence/` directory. The result remains portable when the whole
`interactive-report/` directory is moved or zipped.

See [the detailed viewer guide](docs/INTERACTIVE_REPORT.md) and
[the NEMO zinc-finger walkthrough](tutorials/nemo_zinc_finger/README.md). See
[dependency and license information](DEPENDENCIES_AND_LICENSES.md).

## License

The software is released under the BSD 3-Clause License. See [LICENSE](LICENSE).
