# Build and download the NEMO report from WFU DEAC

This tutorial continues the core repository's
[NEMO DEAC tutorial](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/nemo_zinc_finger_deac/README.md).
Complete its Slurm run and final `status` check first. That tutorial installs
both current `main` checkouts in one DEAC environment and defines `DEAC_WORK`,
`NEMO_STUDY`, and `CORE_CMD`.

Building the browser reads completed reports on group storage. It does not read
the raw trajectory again or submit a DEAC job.

## 1. Confirm completion on DEAC

```bash
source "$DEAC_WORK/.venv/bin/activate"
"$CORE_CMD" status "$NEMO_STUDY/analysis"
"$CORE_CMD" status "$NEMO_STUDY/analysis" --json
```

Wait until every scheduled task is complete. Use the core recovery workflow for
failed, missing, or hash-invalid reports before building the browser.

## 2. Build the offline browser

Run the companion command on the DEAC login node:

```bash
"$DEAC_WORK/.venv/bin/salsbury-md-analysis-interactive" \
  "$NEMO_STUDY/analysis"
```

The browser is written to:

```text
nemo-zinc-finger-deac/analysis/interactive-report/
```

That directory contains `index.html`, its manifest, and the packaged evidence.
Generation is immutable. A complete existing report is reused only after its
HTML and evidence hashes validate. Partial or changed output is not overwritten.

## 3. Download the complete report

Create one archive:

```bash
tar -C "$NEMO_STUDY/analysis" -czf \
  "$NEMO_STUDY/nemo-interactive-report.tar.gz" \
  interactive-report
```

Download it through DEAC Open OnDemand or another file-transfer client. Extract
the archive on your computer and open `interactive-report/index.html`. The
browser needs neither a web server nor an internet connection. Copying only the
HTML file breaks the relative evidence links.

## 4. Review the NEMO result

Open the scientific report when present, then review structural QC, sampling
and resources, molecular states, zinc geometry, ion results, and the source
figures, tables, and representative structures behind each finding.

The viewer reports what the completed core campaign produced. It does not
establish convergence, equilibrium populations, rare-state sampling, zinc
affinity, or mechanism. The NEMO fixture's `scientific_status` remains
`not evaluated`.

Keep both recorded commit files, the copied DEAC profile, core reports, and the
complete browser with any accepted use of the run.
