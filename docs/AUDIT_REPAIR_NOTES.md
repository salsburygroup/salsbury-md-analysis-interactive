# Viewer repairs awaiting release

These changes are on a repair branch; existing release tags are unchanged.

Embedded JSON now escapes markup delimiters regardless of letter case. Reusing
an existing report verifies every packaged evidence file, not just the HTML.
An internally valid old snapshot remains viewable, but source changes are
reported and require a new output name for an updated snapshot.

Experimental extensions can package reports linked from a completed main
campaign. Each external report must match the extension contract's exact
upstream path and content hash. Unlisted external symlinks and changed upstream
reports are rejected. The resulting dashboard contains local copies and does
not need the original main campaign to remain available.

The dependency range covers the tested stable and experimental core versions.
Both combinations are installed with dependency resolution and checked with
`pip check`. Browser tests exercise controls, figure targets, molecular views,
and evidence links. They also check that report text cannot introduce another
script and that offline reports make no external requests.

Opening-page wording now describes the picker's within-family effect ranking
and statistical evidence. The viewer does not infer biological importance or
fill a required number of headline findings.

CI tests the installed wheel outside the checkout and runs browser checks
against both core branches. The local repair audit also opens freshly generated
NEMO reports. Those runs test software behavior, not convergence or biological
interpretation.
