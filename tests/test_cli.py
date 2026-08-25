import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from salsbury_md_analysis_interactive.cli import main


class InteractiveCliTests(unittest.TestCase):
    def test_cli_builds_named_output_and_prints_machine_readable_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_directory = root / "results" / "example"
            report_directory.mkdir(parents=True)
            (report_directory / "report.json").write_text(
                json.dumps({
                    "module_id": "example",
                    "technical_status": "complete",
                    "scientific_status": "not evaluated",
                    "issues": [],
                }),
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([str(root), "--output-name", "viewer"])
            summary = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["technical_status"], "complete")
            self.assertTrue((root / "viewer" / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
