# Salsbury MD Analysis Interactive

Reports with a hash-verified scientific summary open on that summary: the
question, systems, quantitative findings, and supporting figures. Use the
sidebar to inspect secondary findings, every candidate, all analysis classes,
structures, QC, and resource accounting. The selective opening does not prune
the supporting archive. Older reports without a reader summary retain the
overview screen.

The viewer imports only non-executable report markup and local evidence links.
`finding_reader_review.md`, under QC and provenance, lists missing reporting
context or structural evidence separately from the scientific narrative.

`salsbury-md-analysis-interactive` is the optional results browser for
[`salsbury-md-analysis`](https://github.com/salsburygroup/salsbury-md-analysis).
It turns a completed analysis directory into a self-contained HTML report with
prioritized findings, complete module accounting, QC, FES and clustering views,
resource and sampling tables, and representative molecular structures.

The analysis package and viewer have separate commands. Use
`salsbury-md-analysis` to analyze trajectories. Use this package after that run
finishes to browse its results.

## Install

For coordinate-derived figures beside selected findings, see the optional
[molecular-panel renderer](docs/MOLECULAR_PANELS.md). It renders specified PDBs
and saves their source identities and an offline view; it does not rerun analyses.

The unreleased 0.1.4rc1 candidate uses the core candidate's shared clustering
selection. Install its wheel alongside main 0.1.3rc1 or experimental 0.2.0a3.
For a local candidate checkout, install the core checkout first, then run
`python -m pip install .` here. The published-release commands below install
the older releases, not these candidate changes.

The candidate has installed-package tests on Linux and macOS, plus offline
Chrome checks on macOS. WSL2 testing is deferred because no Windows test host
is available; native Windows execution is unsupported.

Current releases are GitHub source distributions. This command installs both
without making source checkouts:

```bash
python -m pip install \
  "salsbury-md-analysis @ git+https://github.com/salsburygroup/salsbury-md-analysis.git@v0.1.2" \
  "salsbury-md-analysis-interactive @ git+https://github.com/salsburygroup/salsbury-md-analysis-interactive.git@v0.1.3"
```

The interactive package declares `salsbury-md-analysis>=0.1.2,<0.3` as a
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
HTML checksum, and every packaged evidence hash must validate before reuse. Changed or partial output
fails closed instead of being overwritten.

## What the report shows

When the core run includes the figure-led findings summary, the opening page
links to it. The viewer packages that summary, its secondary findings, complete
artifact index, and full candidate CSV beside the figures, tables, and structures.
These links work after downloading and extracting the interactive report.
Summary formatting does not change the ranking or remove any candidate or
analysis artifact. Older runs without this summary keep the existing dashboard.

The browser opens with the picker’s prioritized findings. A finding links to
its analysis tab and, when available, to a figure or representative structure.
Free-energy surfaces come first in the molecular-states view. One primary
clustering partition follows for each comparable view, with method names,
per-system populations, and representative structures. Expand alternatives
to inspect the rest. The viewer uses the core picker's decision; it does not
rank incompatible scores or choose a different winner. Legacy reports without
a common evaluation remain unranked. A silhouette score is method information,
not a scientific headline.

Each analysis class has its own tab. QC errors and warnings stay in the QC tab;
review notes from clustering or another scientific method stay with that
method. Internal view identifiers are replaced by readable names.

The molecular viewer packages complete non-solvent structures. Its bundled
3Dmol.js renderer draws polymers as a NewCartoon-style ribbon, ligands and
cofactors as bonded atoms, and ions as space-filling spheres. The underlying
PDB remains available beside the viewer.

The picker targets 10–12 headline findings and can show fewer when fewer
qualify. It uses within-family effect ranks and available statistical evidence,
without category quotas. Secondary findings bring the highlighted total to
50 when enough eligible candidates exist. Every other candidate remains available in
the searchable browser and the core JSON and CSV files.

The report copies the JSON, CSV, PDB, and figure files needed by its links into an
`evidence/` directory. The result remains portable when the whole
`interactive-report/` directory is moved or zipped.

With a current core report, every completed analysis has at least one labeled
figure and a CSV table when tabular values are available. Findings open the
exact matching artifact. Radius of gyration opens a Scott-rule histogram first,
with the replica time series in the same analysis tab. State representatives
contain the complete non-solvent molecular system and, when the state-ion
calculation is available, only ions retained as stable within that state.

See [the detailed viewer guide](docs/INTERACTIVE_REPORT.md) and
[the NEMO zinc-finger walkthrough](tutorials/nemo_zinc_finger/README.md). See
[dependency and license information](DEPENDENCIES_AND_LICENSES.md).

## License

The software is released under the BSD 3-Clause License. See [LICENSE](LICENSE).
