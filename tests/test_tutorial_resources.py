import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("nemo_zinc_finger_workstation", "nemo_zinc_finger_cluster",
         "nemo_zinc_finger_deac", "workstation", "cluster")


class TutorialResourceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("bash"), "bash is required for shell syntax checks")
    def test_tutorial_bash_syntax(self):
        for path in (ROOT / "tutorials").rglob("*.md"):
            for number, block in enumerate(re.findall(r"```bash\n(.*?)\n```", path.read_text(), re.S)):
                with self.subTest(path=path.name, block=number):
                    self.assertNotRegex(block, r"(?m)^\+  --")
                    result = subprocess.run(["bash", "-n"], input=block, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_routes_explain_separate_report_cost(self):
        for page in PAGES:
            text = (ROOT / "tutorials" / page / "README.md").read_text()
            self.assertIn("../REPORT_RESOURCES.md", text)
            self.assertIn("salsbury-md-analysis/blob/main/tutorials/RESOURCE_PLANNING.md", text)
        guide = (ROOT / "tutorials/REPORT_RESOURCES.md").read_text()
        self.assertIn("no calibrated viewer resource recommendation", guide)
        self.assertIn("workload-based estimates", guide)
        self.assertIn("ORCHESTRATION_RESOURCE_ESTIMATES.md", guide)

    def test_nemo_cluster_paths_follow_successful_attempt(self):
        for page in ("nemo_zinc_finger_deac", "nemo_zinc_finger_cluster"):
            text = (ROOT / "tutorials" / page / "README.md").read_text()
            self.assertNotIn('"$NEMO_STUDY/analysis"', text)
            self.assertIn('status "$NEMO_ANALYSIS"', text)
            self.assertIn('tar -C "$NEMO_ANALYSIS"', text)
            self.assertIn("${NEMO_ANALYSIS:?", text)
            self.assertIn("approved compute allocation", text)

    def test_full_workstation_environment_is_explicit(self):
        text = (ROOT / "tutorials/nemo_zinc_finger_workstation/README.md").read_text()
        self.assertIn('--dssp-executable "$PWD/.venv/bin/mkdssp"', text)
        self.assertIn('export PATH="$PWD/.venv/bin:$PATH"', text)
        self.assertIn('--output "$NEMO_ANALYSIS"', text)
        self.assertIn("two elapsed hours", text)


if __name__ == "__main__":
    unittest.main()
