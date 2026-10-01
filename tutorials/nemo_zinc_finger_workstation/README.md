# Build and browse the NEMO results on a workstation

Read [Report resource limits](../REPORT_RESOURCES.md) before building the
browser. Core budget and recovery guidance is in
[Resource settings and planning limits](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/RESOURCE_PLANNING.md).

This tutorial continues the core repository's
[NEMO workstation tutorial](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/nemo_zinc_finger_workstation/README.md).

The commands below use both current `main` branches and record their exact
commits. To run the same example through Slurm, use the core repository's
[generic cluster tutorial](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/nemo_zinc_finger_cluster/README.md)
or the separate
[WFU DEAC tutorial](https://github.com/salsburygroup/salsbury-md-analysis/blob/main/tutorials/nemo_zinc_finger_deac/README.md).

To add coordinate-derived illustrations beside reader findings after the
analysis, follow [Molecular panels](../../docs/MOLECULAR_PANELS.md). Use the
saved NEMO state assignments to select frames, retain their source identities,
and include only Zn ions supported by the state-specific ion-stability result.
This optional rendering step uses existing results; it does not run the
trajectory analysis again.

This walkthrough starts with the simulation files in the core package's NEMO
tutorial and ends with a self-contained HTML report. The core package performs
the analysis. The interactive package reads the completed result directory.

The fixture is a 1,000-frame subset of a published Salsbury-group simulation of
the 28-residue NEMO zinc-finger domain. It contains the protein, its hydrogens,
and one zinc ion. This small run checks the software and teaches the workflow;
it cannot establish convergence, equilibrium populations, rare-state sampling,
zinc affinity, or a biological mechanism.

## 1. Get both current main branches

Create a workspace, clone both repositories, and save the exact revisions used:

```bash
mkdir salsbury-md-analysis-workstation
cd salsbury-md-analysis-workstation
git clone --branch main --single-branch \
  https://github.com/salsburygroup/salsbury-md-analysis.git core
git clone --branch main --single-branch \
  https://github.com/salsburygroup/salsbury-md-analysis-interactive.git interactive
git -C core rev-parse HEAD | tee CORE_MAIN_COMMIT.txt
git -C interactive rev-parse HEAD | tee INTERACTIVE_MAIN_COMMIT.txt
cd core
```

The core checkout supplies the teaching files. Do not update either checkout
inside a prepared campaign; start a new recorded run when changing revisions.

## 2. Create the full tutorial environment

The full Conda environment includes NumPy, SciPy, scikit-learn, HDBSCAN, and
`mkdssp` 4.6.1:

```bash
micromamba create --prefix ./.venv --file environment.yml \
  --override-channels --channel conda-forge --strict-channel-priority
./.venv/bin/python -m pip install --no-build-isolation -e .
./.venv/bin/python -m pip install --no-build-isolation -e ../interactive
```

Check that the environment is consistent and the secondary-structure executable is available:

```bash
./.venv/bin/python -m pip check
./.venv/bin/mkdssp --version
export PATH="$PWD/.venv/bin:$PATH"
```

People using their own trajectories can install both commands with the two
GitHub requirements shown in the main README. The source checkout in this
walkthrough supplies the NEMO data and the reviewed Conda environment. Pip
cannot install `mkdssp`. Without that executable, preparation records the DSSP
module as deferred and continues with the remaining applicable analyses.

## 3. Prepare the core analysis

Run this command from the core repository root:

```bash
export NEMO_ANALYSIS="$PWD/nemo-zinc-finger-interactive-tutorial-run"

./.venv/bin/salsbury-md-analysis prepare-analysis \
  --pdb tutorials/nemo_zinc_finger_workstation/data/nemo_zinc_finger.pdb \
  --psf tutorials/nemo_zinc_finger_workstation/data/nemo_zinc_finger.psf \
  --trajectory tutorials/nemo_zinc_finger_workstation/data/nemo_zinc_finger_1000_frames.dcd \
  --frame-interval-ps 0.2 \
  --project-id nemo-zinc-finger-interactive-tutorial \
  --config tutorials/nemo_zinc_finger_workstation/analysis-config.json \
  --dssp-executable "$PWD/.venv/bin/mkdssp" \
  --output "$NEMO_ANALYSIS"
```

Preparation infers the protein-plus-zinc composition, chooses applicable
modules, plans integer frame strides, estimates CPU and memory use, and writes
the local execution scripts. Inspect these files before launching the run:

- `module-coverage.json` lists every automatic, deferred, disabled, and
  inapplicable module;
- `sampling-plan.json` records the selected frames and integer strides;
- `campaign-resource-plan.json` records the shared CPU, time, memory, and
  scratch plan; and
- `automatic-chemical-context.json` records the inferred protein and zinc
  selections.

The core tutorial config allows two CPUs, two elapsed hours, and 32 GiB
aggregate memory, using built-in planner models. These are campaign ceilings,
not measured requirements. Require successful preparation and a feasible plan.
If time is insufficient, repeat preparation with the reviewed
`--target-wall-hours` recommendation and a new `NEMO_ANALYSIS` directory;
preserve the failed attempt. Keep that path for execution and report building.

The explicit `--dssp-executable` uses the full environment installed above.
`secondary_structure` should appear as automatic in `module-coverage.json`.
If using an intentionally DSSP-free environment, omit that option and verify
that the deferred module is recorded. Do not claim full-module coverage then.

## 4. Run the analysis

```bash
(cd "$NEMO_ANALYSIS" && ./run-local.sh)
```

Wait for the local workflow to finish. Use the core workflow to launch or resume
calculations; the interactive command reads the completed reports. Before
building the browser, check the newest record under `local-execution-status/`
and confirm that the expected module reports completed.

## 5. Build the interactive report

```bash
./.venv/bin/salsbury-md-analysis-interactive \
  "$NEMO_ANALYSIS"
```

Open this file in a current browser:

```text
$NEMO_ANALYSIS/interactive-report/index.html
```

The report is self-contained. It does not need a web server, send results to an
external service, or download JavaScript after it opens.

## 6. Read the report

Read the prioritized findings, then open their linked analysis tabs, figures,
or representative structures. The molecular-states tab places the FES first
and then shows one primary clustering partition per comparable view. Expand
alternatives to inspect other methods. Older reports without comparable
evaluation evidence remain unranked. Silhouette is a partition diagnostic,
not a physical finding. The population tables show
how the NEMO frames are distributed across clusters. The structure viewer keeps
the protein and zinc ion while excluding solvent. If the core report includes
state-conditioned ion stability, a state representative shows zinc only when
it belongs to an occupied, low-RMSF site in that state.

QC has its own tab. Clustering review notes remain under Clustering rather than
appearing as structural QC. Use the separate analysis tabs to move through
RMSD/Rg, RMSF, SASA, ions, correlations, and the other completed analyses. The
**All reports** tab is the complete index.

Radius of gyration opens as a Scott-rule histogram. Its time series is a
secondary view in the same tab. FES findings open the configured primary
surface, and population findings open the matching per-system table or chart.
The report keeps smoothing sensitivity in a separate table instead of showing
every smoothing level as another primary FES.

The `interactive-report/evidence/` directory contains the JSON, CSV, PDB, and
figure files opened by report links. Move or zip the whole
`interactive-report/` directory so those links remain intact.

## Rebuild with different viewer limits

Report generation is immutable. Use a new output name when changing the title
or inline asset limits:

```bash
./.venv/bin/salsbury-md-analysis-interactive \
  "$NEMO_ANALYSIS" \
  --output-name interactive-report-compact \
  --maximum-inline-structures 10
```

This changes only the browser. The scientific outputs remain unchanged.

The repaired picker may show fewer than ten headlines when fewer candidates
qualify. Check each finding's effect and supporting figure; headline placement
does not establish physical importance. PCA has variance plots, tICA has
labeled timescales, and ESS has its own panel. Keep the two recorded commit
files with the report so the current-main run remains reproducible.
