# Browse the NEMO zinc-finger tutorial results

This walkthrough starts with the simulation files in the core package's NEMO
tutorial and ends with a self-contained HTML report. The core package performs
the analysis. The interactive package reads the completed result directory.

The fixture is a 1,000-frame subset of a published Salsbury-group simulation of
the 28-residue NEMO zinc-finger domain. It contains the protein, its hydrogens,
and one zinc ion. This small run checks the software and teaches the workflow;
it cannot establish convergence, equilibrium populations, rare-state sampling,
zinc affinity, or a biological mechanism.

## 1. Get the teaching files

Clone or download the core repository, which contains the PDB, PSF, DCD,
configuration, and provenance record used here:

```bash
git clone https://github.com/salsburygroup/salsbury-md-analysis.git
cd salsbury-md-analysis
```

You need the core source checkout for these teaching files. People analyzing
their own trajectories can install both commands from GitHub without cloning
either repository.

## 2. Create the full tutorial environment

The full Conda environment includes NumPy, SciPy, scikit-learn, HDBSCAN, and
`mkdssp` 4.6.1:

```bash
micromamba create --prefix ./.venv --file environment.yml \
  --override-channels --channel conda-forge --strict-channel-priority
./.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
./.venv/bin/python -m pip install \
  "salsbury-md-analysis-interactive @ git+https://github.com/salsburygroup/salsbury-md-analysis-interactive.git@main"
```

Check that the secondary-structure executable is available:

```bash
./.venv/bin/mkdssp --version
```

People using their own trajectories can install both commands with the two
GitHub requirements shown in the main README. The source checkout in this
walkthrough supplies the NEMO data and the reviewed Conda environment. Pip
cannot install `mkdssp`. Without that executable, preparation records the DSSP
module as deferred and continues with the remaining applicable analyses.

## 3. Prepare the core analysis

Run this command from the core repository root:

```bash
./.venv/bin/salsbury-md-analysis prepare-analysis \
  --pdb tutorials/nemo_zinc_finger/data/nemo_zinc_finger.pdb \
  --psf tutorials/nemo_zinc_finger/data/nemo_zinc_finger.psf \
  --trajectory tutorials/nemo_zinc_finger/data/nemo_zinc_finger_1000_frames.dcd \
  --frame-interval-ps 0.2 \
  --project-id nemo-zinc-finger-interactive-tutorial \
  --config tutorials/nemo_zinc_finger/analysis-config.json \
  --output nemo-zinc-finger-interactive-tutorial-run
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

With `mkdssp` available, `secondary_structure` should appear as automatic in
`module-coverage.json`. If it is deferred, confirm that the environment was
active during preparation. You can also add this option to the preparation
command before `--output`:

```bash
--dssp-executable "$PWD/.venv/bin/mkdssp"
```

Use a new output directory when you repeat preparation. The command never
overwrites a nonempty run.

## 4. Run the analysis

```bash
cd nemo-zinc-finger-interactive-tutorial-run
./run-local.sh
cd ..
```

Wait for the local workflow to finish. Use the core workflow to launch or resume
calculations; the interactive command reads the completed reports. Before
building the browser, check the newest record under `local-execution-status/`
and confirm that the expected module reports completed.

## 5. Build the interactive report

```bash
./.venv/bin/salsbury-md-analysis-interactive \
  nemo-zinc-finger-interactive-tutorial-run
```

Open this file in a current browser:

```text
nemo-zinc-finger-interactive-tutorial-run/interactive-report/index.html
```

The report is self-contained. It does not need a web server, send results to an
external service, or download JavaScript after it opens.

## 6. Read the report

Read the QC panel first. Then review the prioritized findings, FES and
clustering views, representative zinc-finger structures, and the resources and
sampling table. The **All analyses** section keeps every completed module in
view, including reports that the automatic picker did not rank near the top.

The automatic ranking helps you decide where to look. It does not establish
convergence, causality, mechanism, biological importance, statistical
significance, or scientific validity. Open the linked source report whenever a
finding needs its full settings, warnings, frame selection, or provenance.

## Rebuild with different viewer limits

Report generation is immutable. Use a new output name when changing the title
or inline asset limits:

```bash
./.venv/bin/salsbury-md-analysis-interactive \
  nemo-zinc-finger-interactive-tutorial-run \
  --output-name interactive-report-compact \
  --maximum-inline-structures 10
```

This changes only the browser. The scientific outputs remain unchanged.
