# Interactive result browser

Version 0.1.1 is an optional, offline front end for completed
`salsbury-md-analysis` campaigns. It is a presentation layer over the existing
JSON, CSV, structures, and figures. Those source artifacts remain the
scientific record.

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

1. QC errors and warnings plus the highest-ranked findings;
2. every highlighted finding with system, module, evidence level, effect, and
   raw report link, followed by complete picker accounting for every module;
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

The built-in viewer is deliberately dependency-free. It reads PDB atom records,
supports rotation and zoom, filters atoms, colors by element, chain, or B-factor,
and highlights atom/residue text matches. Its CA/P trace lines are visual guides,
not inferred chemical bonds. Download the linked PDB and use VMD, ChimeraX, or
another full molecular package when bond topology, surfaces, measurements, or
publication rendering are needed.

Representative structures are included in the HTML only up to explicit bounded
asset limits. Omitted structures and figures remain linked and are listed in the
provenance panel. Multi-frame state trajectories are never embedded in the HTML.

## Large reports

The finalizer never treats browser convenience as permission for unbounded
memory use. A JSON report larger than 128 MB is hash-indexed and represented by
its compact summary sidecar rather than loaded into the browser. The raw report
remains linked. This affects only the interactive preview; it does not remove,
change, or reclassify the analysis result.

## Optional installation

The core analysis package does not install or invoke this viewer. A
non-interactive installation therefore needs no configuration change:

```bash
python -m pip install "salsbury-md-analysis>=0.1.1,<0.2"
```

Install the companion and build the browser when wanted:

```bash
python -m pip install salsbury-md-analysis-interactive
salsbury-md-analysis-interactive path/to/analysis-root
```

Use `--output-name` to choose a different safe output-directory name. Asset
limits can be changed with the documented `--maximum-inline-*` options.

Generation is immutable. If the output directory already exists, its manifest
and HTML hash must validate before it is reused. A partial or changed directory
fails closed instead of being overwritten.

## Interpretation

The result browser does not promote technical completion into scientific
validity. Automated findings without a supported adjusted p-value remain
descriptive. FES basins, smoothing, clustering, silhouettes, state populations,
representatives, correlations, and ion geometry still require review of
sampling, convergence, chemistry, uncertainty, and the underlying method report.
