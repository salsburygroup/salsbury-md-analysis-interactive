# Build and review the NEMO report from a Slurm cluster

Read [Report resource limits](../REPORT_RESOURCES.md) before building the
browser. Core budget and recovery guidance is in
[Resource settings and planning limits](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/RESOURCE_PLANNING.md).

This tutorial continues the core repository's
[NEMO generic Slurm tutorial](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/nemo_zinc_finger_cluster/README.md).
Complete that tutorial through the final `status` check before continuing here.
The core tutorial installs both current `main` checkouts in one recorded
environment and defines `CLUSTER_WORK`, `NEMO_STUDY`, `NEMO_ANALYSIS`, and `CORE_CMD`.

The viewer reads accepted reports. It does not inspect the raw trajectory,
rerun an analysis, or submit a Slurm job.

Keep `NEMO_ANALYSIS` set to the successful core attempt, including
`analysis-replanned` if you used budget recovery. In a new shell, restore all
four variables with the recorded paths before continuing. Do not reset the
analysis path to the failed original attempt.

## 1. Confirm that the core campaign completed

On the login or submission host, activate the recorded environment and read the
core status again:

```bash
source "$CLUSTER_WORK/.venv/bin/activate"
: "${NEMO_ANALYSIS:?Set the successful prepared analysis path}"
"$CORE_CMD" status "$NEMO_ANALYSIS"
"$CORE_CMD" status "$NEMO_ANALYSIS" --json
```

Do not build the browser while tasks remain queued or running. Resolve failed,
missing, or hash-invalid reports through the core recovery workflow first.

## 2. Build the offline browser

Use an approved compute allocation or a suitable workstation. Login-node use
requires site permission for the measured workload.

```bash
"$CLUSTER_WORK/.venv/bin/salsbury-md-analysis-interactive" \
  "$NEMO_ANALYSIS"
```

The command writes:

```text
$NEMO_ANALYSIS/interactive-report/
```

The directory contains `index.html`, a manifest, and the evidence files used by
the report. Generation is immutable. An existing complete report is reused only
after its HTML and evidence hashes validate. A partial or changed directory
fails closed instead of being overwritten.

## 3. Transfer the complete report

Make one archive on shared storage:

```bash
tar -C "$NEMO_ANALYSIS" -czf \
  "$NEMO_STUDY/nemo-interactive-report.tar.gz" \
  interactive-report
```

Download the archive, extract it on your workstation, and open
`interactive-report/index.html` in a current browser. A web server and internet
connection are not required. Copying only `index.html` breaks its evidence
links.

## 4. Review the NEMO result

Start with the scientific report when it is available, then inspect structural
QC, sampling and resources, molecular states, zinc geometry, ion results, and
the source figures, tables, and representative structures behind each finding.

The viewer preserves the core picker's primary clustering choice and retains
the alternatives. It does not turn a silhouette score, a representative
structure, or a highlighted finding into a biological conclusion. The NEMO
fixture remains a software exercise with `scientific_status: not evaluated`.

Keep `CORE_MAIN_COMMIT.txt`, `INTERACTIVE_MAIN_COMMIT.txt`, the site profile,
core reports, and the complete browser with any accepted use of this run.
