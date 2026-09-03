# Changelog

## 0.1.2 - 2026-09-03

- Keep structural and preparation problems in QC while placing method review
  notes in their own analysis tabs.
- Add a separate tab for every analysis class found in the campaign.
- Put FES results first and order named clustering methods by silhouette score.
- Show per-system cluster populations and linked structure previews.
- Package working JSON, PDB, and figure links under `interactive-report/evidence/`.
- Render all non-solvent structure atoms with the bundled 3Dmol.js viewer:
  polymer ribbons, bonded ligands and cofactors, and space-filling ions.
- Stream visualization fields from large FES and clustering reports with
  bounded memory.
- Use Wake Forest Old Gold and black throughout the browser, with red reserved
  for scientific emphasis, selections, and items requiring attention.

## 0.1.1 - 2026-08-25

- Split the offline interactive browser from the core analysis package.
- Preserve complete picker accounting and a separate QC lane.
- Render FES, clustering, RMSF, DCCM, resource, sampling, and provenance views.
- Embed bounded representative PDB structures without network dependencies.
- Validate the companion package against the 1,000-frame NEMO zinc-finger fixture.
- Document the GitHub installation and the separate analysis and report commands.
- Add a NEMO walkthrough that includes the reviewed `mkdssp` environment.
