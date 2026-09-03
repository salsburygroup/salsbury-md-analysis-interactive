# Interactive result browser

Version 0.1.3 is an optional, offline front end for completed
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
- `interactive-report/evidence/`, portable copies or compact indexes for the
  JSON, CSV, PDB, and figure files linked from the browser; and
- `interactive-report/manifest.json`, which records the generator version, HTML
  hash, source-report hashes, and included assets.

Open `interactive-report/index.html` in a current browser. It does not need a
web server or internet connection, and it does not send structures or results
to an external service.

The browser presents:

1. 10–12 headline findings; the picker always shows
   10 and extends the opening section to 11 or 12 only when a
   Benjamini-Hochberg-significant finding reaches the boundary;
2. enough secondary findings to bring the highlighted total to 50 when the
   campaign has at least 50 candidates, followed by every additional
   ranked candidate through searchable tier, system, category, and text
   filters and complete picker accounting;
3. the primary FES surface at the configured smoothing level, its basin
   populations by system, and a separate smoothing-sensitivity table;
4. clustering methods in descending silhouette-score order, with each method
   named and each system's state populations shown beside linked
   representative structures;
5. a separate tab for each analysis class, including RMSF, DCCM, ions,
   hydrogen bonds, hydration, DNA geometry, kinetics, and comparisons when
   those classes are present;
6. interactive non-solvent representative structures, pre-rendered figures,
   and CSV tables from the core presentation manifest;
7. every module report, including its picker disposition and modules that
   produced no ranked finding;
8. measured CPU, memory, frame selection, and observation accounting; and
9. resolved configuration, chemical context, conformational views, QC, and
   provenance. Structural and preparation QC stay in the QC tab. Review notes
   from clustering or another analysis stay in that analysis tab.

Radius of gyration appears first as a Scott-rule histogram. Its
replica-resolved time series remains available in the same analysis tab.
Findings open the exact figure, table, or structure named by the core artifact
manifest rather than the first result from the same module.

## Molecular viewer boundary

The built-in viewer reads the packaged PDB with a bundled copy of 3Dmol.js. The
PDB retains every non-solvent atom. The default display uses a
NewCartoon-style ribbon for protein and nucleic-acid polymers, bonded atoms for
ligands and cofactors, and space-filling spheres for ions. It supports rotation,
zoom, atom filters, element/chain/B-factor colors, and atom or residue search.

When a state export includes the core state-ion stability analysis, the viewer
shows only ions assigned to occupied, low-RMSF sites in that state. The
structure still retains all protein, nucleic acid, ligand, and cofactor atoms.

The renderer is not VMD itself. Download the linked PDB and use VMD, ChimeraX,
or another full molecular package for surfaces, measurements, topology-aware
editing, or publication rendering.

Representative structures are included in the HTML only up to explicit bounded
asset limits. Omitted structures and figures remain linked and are listed in the
provenance panel. Multi-frame state trajectories are never embedded in the HTML.

## Large reports

The finalizer does not load a large result wholesale. For a JSON report larger
than 128 MB, the `ijson` reader streams the FES grids or clustering scores and
populations needed by the display while skipping frame assignments, centers,
and other large arrays. The browser receives a compact evidence index linked to
the source report hash.

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

## Scientific review

Review sampling, convergence, chemistry, uncertainty, and the underlying
method report before interpreting FES basins, clustering, silhouettes, state
populations, representatives, correlations, or ion geometry. The report helps
locate and compare evidence; it does not replace that review.
