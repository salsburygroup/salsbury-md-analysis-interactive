import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InteractiveTutorialTests(unittest.TestCase):
    def test_matching_core_paths_have_interactive_pages_and_reciprocal_links(self):
        index = (ROOT / "tutorials" / "README.md").read_text(encoding="utf-8")
        core_base = (
            "https://github.com/salsburygroup/"
            "salsbury-md-analysis/blob/main/tutorials/"
        )
        for path in (
            "nemo_zinc_finger_workstation",
            "nemo_zinc_finger_cluster",
            "nemo_zinc_finger_deac",
            "workstation",
            "cluster",
        ):
            relative = f"{path}/README.md"
            self.assertIn(relative, index)
            page_path = ROOT / "tutorials" / relative
            self.assertTrue(page_path.is_file())
            page = page_path.read_text(encoding="utf-8")
            self.assertIn(f"{core_base}{path}/README.md", page)
            self.assertIn("salsbury-md-analysis-interactive", page)
            self.assertIn("interactive-report", page)

    def test_cluster_pages_preserve_submission_and_transfer_boundaries(self):
        generic = (
            ROOT / "tutorials" / "nemo_zinc_finger_cluster" / "README.md"
        ).read_text(encoding="utf-8")
        deac = (
            ROOT / "tutorials" / "nemo_zinc_finger_deac" / "README.md"
        ).read_text(encoding="utf-8")
        cluster = (ROOT / "tutorials" / "cluster" / "README.md").read_text(
            encoding="utf-8"
        )
        for page in (generic, deac, cluster):
            self.assertIn("status", page)
            self.assertIn("tar -C", page)
            self.assertIn("submit", page.lower())
            self.assertIn("Copying only", page)
        self.assertIn("CLUSTER_WORK", generic)
        self.assertIn("DEAC_WORK", deac)
        self.assertIn("/shared/path/my-study/analysis", cluster)

    def test_readme_links_the_interactive_index(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("tutorials/README.md", readme)


if __name__ == "__main__":
    unittest.main()
