import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import test_report
from salsbury_md_analysis_interactive.report import (
    _preview, _render_html, build_interactive_report, InteractiveReportError,
)


class DisplayIntegrityTests(unittest.TestCase):
    def test_preview_is_bounded_across_nested_containers_and_unicode_strings(self):
        data = {str(k): [{"long": "𝄞"*3000, "value": j} for j in range(80)] for k in range(80)}
        encoded = json.dumps(_preview(data))
        self.assertLess(len(encoded.encode()), 100000)
        self.assertIn("truncated", encoded)
        self.assertEqual(_preview({"value": 1.2}), {"value": 1.2})
        short = _preview(list(range(4)), _budget=[2, 1000])
        self.assertTrue(short["preview_truncated"])
        self.assertEqual(short["source_item_count"], 4)

    def test_html_budget_fails_without_changing_input_or_existing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = test_report.InteractiveReportTests()._root(tmp)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(InteractiveReportError, "maximum_html_bytes"):
                build_interactive_report(root, maximum_html_bytes=100)
            self.assertTrue(all(p.read_bytes() == value for p, value in before.items()))
            self.assertFalse((root / "interactive-report").exists())

    def test_link_only_fallback_preserves_all_candidates_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = test_report.InteractiveReportTests()
            root = fixture._root(tmp)
            fixture._add_presentation_artifacts(root)
            original = _render_html
            renders = []
            def oversized(data):
                has_inline = any(r.get("data_uri") for r in data.get("presentation_artifacts", []))
                renders.append((has_inline, len(data["findings"])))
                result = original(data)
                return result + (" "*2000000 if has_inline else "")
            with patch("salsbury_md_analysis_interactive.report._render_html", oversized):
                result = build_interactive_report(root, maximum_html_bytes=2000000)
            self.assertTrue(result["linked_assets_to_meet_html_limit"])
            self.assertEqual([r[0] for r in renders], [True, False])
            self.assertEqual(renders[0][1], renders[1][1])
            self.assertTrue(build_interactive_report(root)["reused"])

    def test_rmsf_markup_has_ticks_and_shared_scale_and_reader_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = test_report.InteractiveReportTests()._root(tmp)
            result = build_interactive_report(root)
            text = (Path(result["output_directory"]) / "index.html").read_text()
            self.assertIn("Residue RMSF with numerical axes", text)
            self.assertIn("Shared RMSF scale", text)
            self.assertIn("val.toFixed(2)", text)
            self.assertIn("flatMap(r=>r.visuals", text)
