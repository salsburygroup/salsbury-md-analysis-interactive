# Interactive result browser

Version 0.1.1 is an optional, offline front end for completed
`salsbury-md-analysis` campaigns. It reads the existing JSON, CSV, structures,
and figures. Those source artifacts remain the scientific record.

## Installation and run order

The packages are currently distributed from GitHub. Install both in one pip
command:

```bash
python -m pip install \
  "salsbury-md-analysis @ git+https://github.com/salsburygroup/salsbury-md-analysis.git@main" \
  "salsbury-md-analysis-interactive @ git+https://github.com/salsburygroup/salsbury-md-analysis-interactive.git@main"
```

The interactive package declares `salsbury-md-analysis>=0.1.1,<0.2` as a
dependency, but that core package is not on PyPI. Supplying both GitHub
requirements lets pip resolve the dependency without two source checkouts.

The commands remain separate after installation. The core command reads the
topology and trajectories and produces the scientific reports. The interactive
command reads a completed analysis directory and writes the HTML browser. It
will not launch the core workflow for you.

For protein secondary-structure analysis, install the external `mkdssp`
executable before preparing the core campaign. Pip cannot supply that binary.
The full Conda environment in the core repository installs the reviewed
conda-forge `dssp` package. If `mkdssp` is absent, the core initializer records
`secondary_structure` as deferred and the viewer reports that omission.

## What is generated

Running the companion command against a completed local or Slurm campaign
writes:

- `interactive-report/index.html`, the self-contained result browser;
- `interactive-report/manifest.json`, which records the generator version, HTML
  hash, source-report hashes, included assets, and the technical/scientific
  status boundary.

Open `interactive-report/index.html` in a current browser. It does not need a
web server or internet connection, and it does not send structures or results
to an external service.

The browser presents:

1. QC errors and warnings plus the configured headline findings (12 by default);
2. headline findings first, secondary highlights second, and every additional
   ranked candidate through searchable tier, system, category, and text
   filters, with raw report links and complete picker accounting;
3. FES surfaces at every retained smoothing level and per-system surface;
4. clustering populations and silhouette evidence;
5. RMSF and affordable DCCM views plus pre-rendered figures;
6. interactive representative PDB structures;
7. every module report, including its picker disposition and modules that
   produced no ranked finding;
8. measured CPU, memory, frame selection, and observation accounting; and
9. resolved configuration, chemical context, conformational views, QC, and
   provenance. Picker QC records have their own section and are not promoted
   into the scientific ranking.

## Molecular viewer boundary

The built-in viewer reads PDB atom records with project-owned JavaScript. It
supports rotation and zoom, filters atoms, colors by element, chain, or B-factor,
and highlights atom/residue text matches. Its CA/P trace lines are visual guides
without inferred bond topology. Download the linked PDB and use VMD, ChimeraX,
or another full molecular package when bond topology, surfaces, measurements,
or publication rendering are needed.

Representative structures are included in the HTML only up to explicit bounded
asset limits. Omitted structures and figures remain linked and are listed in the
provenance panel. Multi-frame state trajectories are never embedded in the HTML.

## Large reports

The finalizer never treats browser convenience as permission for unbounded
memory use. A JSON report larger than 128 MB is hash-indexed and represented by
its compact summary sidecar rather than loaded into the browser. The raw report
remains linked. This affects only the interactive preview; it does not remove,
change, or reclassify the analysis result.

## Build the browser

After the core campaign finishes, run:

```bash
salsbury-md-analysis-interactive path/to/analysis-root
```

Use `--output-name` to choose a different safe output-directory name. Asset
limits can be changed with the documented `--maximum-inline-*` options.

Generation is immutable. If the output directory already exists, its manifest
and HTML hash must validate before it is reused. A partial or changed directory
fails closed instead of being overwritten.

The companion accepts an analysis root, not a PDB, PSF, PRMTOP, trajectory, or
analysis config. Follow the
[NEMO zinc-finger walkthrough](../tutorials/nemo_zinc_finger/README.md) for the
complete sequence from simulation files to an interactive report.

## Interpretation

Treat technical completion and scientific validity as separate judgments.
Automated findings without a supported adjusted p-value remain descriptive.
FES basins, smoothing, clustering, silhouettes, state populations,
representatives, correlations, and ion geometry still require review of
sampling, convergence, chemistry, uncertainty, and the underlying method report.
