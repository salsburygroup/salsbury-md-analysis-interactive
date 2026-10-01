# Build and download the NEMO report from WFU DEAC

Read [Report resource limits](../REPORT_RESOURCES.md) before building the
browser. Core budget and recovery guidance is in
[Resource settings and planning limits](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/RESOURCE_PLANNING.md).

This tutorial continues the core repository's
[NEMO DEAC tutorial](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/nemo_zinc_finger_deac/README.md).
Complete its Slurm run and final `status` check first. That tutorial installs
both current `main` checkouts in one DEAC environment and defines `DEAC_WORK`,
`NEMO_STUDY`, `NEMO_ANALYSIS`, and `CORE_CMD`.

Building the browser reads completed reports on group storage. It does not read
the raw trajectory again or submit a DEAC job.

Keep `NEMO_ANALYSIS` set to the successful core attempt, including
`analysis-replanned` if you used budget recovery. In a new shell, restore all
four variables with the recorded paths before continuing. Do not reset the
analysis path to the failed original attempt.

## 1. Confirm completion on DEAC

```bash
source "$DEAC_WORK/.venv/bin/activate"
: "${NEMO_ANALYSIS:?Set the successful prepared analysis path}"
"$CORE_CMD" status "$NEMO_ANALYSIS"
"$CORE_CMD" status "$NEMO_ANALYSIS" --json
```

Wait until every scheduled task is complete. Use the core recovery workflow for
failed, missing, or hash-invalid reports before building the browser.

## 2. Build the offline browser

Run the companion command in an approved compute allocation or on a suitable
workstation with the accepted campaign available. Use a login node only when
site policy permits the measured workload:

```bash
"$DEAC_WORK/.venv/bin/salsbury-md-analysis-interactive" \
  "$NEMO_ANALYSIS"
```

The browser is written to:

```text
$NEMO_ANALYSIS/interactive-report/
```

That directory contains `index.html`, its manifest, and the packaged evidence.
Generation is immutable. A complete existing report is reused only after its
HTML and evidence hashes validate. Partial or changed output is not overwritten.

## 3. Download the complete report

Create one archive:

```bash
tar -C "$NEMO_ANALYSIS" -czf \
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
