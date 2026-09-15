# Build an interactive report for your workstation campaign

This how-to guide continues the core repository's
[workstation guide](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/workstation/README.md).
It assumes that `my-study/analysis` is complete and that the compatible
interactive package is installed in the same recorded environment.

## Confirm the core result

```bash
salsbury-md-analysis status my-study/analysis
salsbury-md-analysis status my-study/analysis --json
```

Build the browser only after every scheduled task is complete. Resolve missing,
failed, or hash-invalid reports through the core recovery workflow first.

## Build and open the report

```bash
salsbury-md-analysis-interactive my-study/analysis
```

Open:

```text
my-study/analysis/interactive-report/index.html
```

The report works without a web server or internet connection. It does not send
structures or results to an external service.

Generation is immutable. When `interactive-report/` already exists, the viewer
validates its manifest, HTML, and packaged evidence before reuse. To build a new
snapshot after accepted core results change, choose a new safe directory name:

```bash
salsbury-md-analysis-interactive my-study/analysis \
  --output-name interactive-report-updated
```

## Review and share it

Start with the scientific report when present. Then inspect structural QC,
sampling and resources, the relevant analysis tabs, and the figures, tables,
and structures linked from each finding. The viewer preserves the core
analysis and selection decisions; it does not rerun or rescore them.

Copy or archive the complete `interactive-report/` directory. Its evidence
links are relative, so `index.html` is not a standalone file. Technical
completion does not establish convergence, equilibrium populations, kinetics,
mechanism, or publication readiness.
