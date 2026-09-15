# Build and transfer an interactive report from a Slurm cluster

This how-to guide continues the core repository's
[Slurm cluster guide](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/cluster/README.md).
It assumes that `/shared/path/my-study/analysis` is complete and that the
compatible viewer is installed in the same recorded environment used by the
core campaign.

## Confirm the core result

On the login or submission host, check the scheduler and accepted reports:

```bash
squeue --me
salsbury-md-analysis status /shared/path/my-study/analysis
salsbury-md-analysis status /shared/path/my-study/analysis --json
```

Do not build the browser while analysis tasks remain active. Resolve failed,
missing, or hash-invalid reports through the core recovery workflow first.

## Build the report on shared storage

```bash
salsbury-md-analysis-interactive /shared/path/my-study/analysis
```

This writes
`/shared/path/my-study/analysis/interactive-report/`. The viewer reads accepted
reports and packages their linked evidence. It does not read the trajectories
again or submit Slurm jobs.

Generation is immutable. An existing complete report is reused only after its
manifest, HTML, and evidence hashes validate. Use `--output-name` for a new
snapshot after accepted source reports change.

## Transfer and inspect it

Create one archive:

```bash
tar -C /shared/path/my-study/analysis -czf \
  /shared/path/my-study/interactive-report.tar.gz \
  interactive-report
```

Download and extract the archive, then open `interactive-report/index.html` in
a current browser. The report does not need a web server or internet connection.
Copying only the HTML file breaks its evidence links.

Start with the scientific report when present, then inspect structural QC,
sampling and resources, the relevant analysis tabs, and the exact figures,
tables, and structures behind each finding. The browser presents completed
evidence; scientific interpretation still requires review of chemistry,
sampling, convergence, uncertainty, and method assumptions.
