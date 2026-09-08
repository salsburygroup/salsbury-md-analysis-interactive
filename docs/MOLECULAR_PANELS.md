# Molecular illustrations for reader findings

The optional renderer makes a PNG and a reopenable offline 3D view from one to
four explicitly selected, already-aligned PDBs. It does not select frames,
fit states, calculate fluctuations, or run the analysis package first.

Install it in the viewer environment:

```bash
python -m pip install '.[render]'
python -m playwright install chromium
python -m salsbury_md_analysis_interactive.molecular_panels panel.json new-panel
```

Alternatively, use an installed Chrome with `--browser-channel chrome`. Browser
installation may need internet access; rendering itself uses the bundled
3Dmol.js library offline. Playwright is an optional Apache-2.0 dependency.
It is not required to browse existing reports or run trajectory analyses.

## Example specification

Replace the filenames, hashes, source identities, and selection rule with
values from your analysis. Frame indices are zero-based. `pdb_sha256` is the
SHA-256 of the exact file; `shasum -a 256 sample.pdb` prints it on macOS/Linux.

```json
{
  "schema": "salsbury-molecular-panel-v1",
  "title": "State 1 in the control ensemble",
  "caption": "Observed state-1 member nearest the fitted center in the reported feature space.",
  "alignment_description": "Already aligned on the common protein backbone to the shared reference.",
  "panels": [{
    "label": "Control",
    "pdb_path": "sample.pdb",
    "pdb_sha256": "REPLACE_WITH_FILE_SHA256",
    "selection_rule": "Minimum recorded distance to the state-1 fitted center among control observations.",
    "source_identity": {"system_id": "control", "replica_id": "rep1", "segment_id": "production", "source_frame_index": 250},
    "visible_ion_serials": [],
    "highlights": [{"selection": {"chain": "A", "resi": 42}, "label": "Site 42"}]
  }]
}
```

Use the same alignment reference across compared panels. The renderer uses
one camera and scale for the aligned coordinates; it does not align them.
An optional top-level `zoom` multiplier defaults to 1. Inspect the resulting
PNG for clipping whenever you change it (allowed range 0.25–3).
`panel_height` defaults to 380 pixels and can be set from 240 to 800. Use a
shorter panel and a matched zoom for compact molecules; keep the same values
across directly compared panels.
`panel_width` defaults to 480 pixels (range 320–800).
Highlight selectors accept exact `serial`, `chain`, `resi`, and `atom` fields.
An unmatched annotation fails rather than labeling another atom.

The source PDBs retain every supplied atom. The figure hides water and hydrogen
atoms and shows polymer cartoons with bonded context. Ions are hidden unless
their serials are listed explicitly. Use a state-specific stability result to
choose that list; a low overall ion fluctuation is not evidence of stability
within each state. Keep the criterion and state identity in the caption.

For measured atom values, provide `atom_values` rows with `serial` and `value`
on each panel, plus one increasing `color_range` and `color_label` for the whole
figure. Colored spheres mark only those atoms. Do not describe an atom-level
RMSF measurement as a residue average. A sampled structure carrying an RMSF
overlay is still a sampled structure, not a mean conformation.

## Attach to a finding

Work in a reporting copy. Keep its original analysis and candidate files.
Register `figure.png`, each `structure-N.pdb`, and `view.html` in the core
presentation manifest with file hashes. The figure uses purpose
`structural_figure`; the PDBs use artifact type `structure`; the saved view uses
type `table` and purpose `molecular_saved_view`.

`molecular_evidence_metadata(render_directory, finding, coordinate_ids,
saved_view_id)` returns the figure's `molecular_evidence` field after checking
the renderer outputs. Set `finding_context[finding_id].structural_artifact_ids`
to those manifest IDs, then regenerate the reader report. The core checks the
finding signature, coordinate hashes, and saved-view hash before accepting the
panel as structural evidence. See the core `docs/FINDING_PICKER.md` for context
configuration. This check establishes file identity; review whether the
illustration supports the stated finding.

The output directory must be new. Failed render evidence is preserved. Copy
the whole panel directory to keep its PDBs and saved view with the PNG.
