# Salsbury MD Analysis Interactive

`salsbury-md-analysis-interactive` is the optional results browser for
[`salsbury-md-analysis`](https://github.com/salsburygroup/salsbury-md-analysis).
It turns a completed analysis directory into a self-contained HTML report with
prioritized findings, complete module accounting, QC, FES and clustering views,
resource and sampling tables, and representative molecular structures.

The analysis package and the viewer are intentionally separate. People who
want only the command-line analysis workflow install `salsbury-md-analysis`.
People who want the offline browser install both packages.

## Install

Version 0.1.1 is compatible with `salsbury-md-analysis` 0.1.x beginning with
0.1.1:

```bash
python -m pip install "salsbury-md-analysis>=0.1.1,<0.2"
python -m pip install salsbury-md-analysis-interactive
```

## Build a report

First run the core analysis workflow. Then point the viewer at its completed
output directory:

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

The browser shows the picker’s prioritized findings first, but does not silently
discard the remaining modules. Every completed module is accounted for as a
ranked candidate, QC result, technical support, interpretive context, or a
reviewed result without an automatic highlight. QC records remain separate from
the scientific ranking.

Automated ranking is a navigation aid. It does not establish convergence,
causality, mechanism, biological importance, statistical significance, or
scientific validity.

See [the detailed viewer guide](docs/INTERACTIVE_REPORT.md) and
[dependency and license information](DEPENDENCIES_AND_LICENSES.md).

## License

The software is released under the BSD 3-Clause License. See [LICENSE](LICENSE).

