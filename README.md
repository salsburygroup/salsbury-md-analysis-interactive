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

## What is highlighted

The browser shows the picker’s prioritized findings first and retains the
remaining modules. Every completed module is accounted for as a ranked
candidate, QC result, technical support, interpretive context, or a reviewed
result without an automatic highlight. QC records remain separate from the
scientific ranking.

Automated ranking is a navigation aid. It does not establish convergence,
causality, mechanism, biological importance, statistical significance, or
scientific validity.

See [the detailed viewer guide](docs/INTERACTIVE_REPORT.md) and
[the NEMO zinc-finger walkthrough](tutorials/nemo_zinc_finger/README.md). See
[dependency and license information](DEPENDENCIES_AND_LICENSES.md).

## License

The software is released under the BSD 3-Clause License. See [LICENSE](LICENSE).
