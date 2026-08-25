# Contributing

Please open an issue before beginning a substantial interface or report-schema
change. Contributions should preserve immutable output, source-report hashes,
the technical-versus-scientific status boundary, offline operation, and bounded
memory use. Add or update tests for every behavior change.

Run the local checks with:

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
python -m build
```

