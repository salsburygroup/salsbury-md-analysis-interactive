import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from salsbury_md_analysis_interactive.reader import reader_panel
from salsbury_md_analysis_interactive.report import _render_html


class ReaderPanelTests(unittest.TestCase):
    def fixture(self, root, body):
        path = root / "prioritized_findings.html"
        path.write_text('<html><body>' + body + '</body></html>')
        (root / "finding_reader_report_checks.json").write_text(json.dumps({
            "generated_files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}))

    def test_only_verified_report_opens_as_science_panel_and_links_stay_portable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a b.csv").write_text('state,fraction\n1,.5\n')
            self.fixture(root, '<h1>State populations</h1><p id="figure-1">Population</p>'
                         '<a href="a%20b.csv">Table</a><a href="#figure-1">Figure 1</a>')
            panel = reader_panel(root)
            self.assertIn('href="evidence/a%20b.csv"', panel)
            self.assertIn('id="reader-figure-1"', panel)
            self.assertIn('href="#reader-figure-1"', panel)
            page = _render_html({"title": "Test", "technical_status": "complete", "reader_report_html": panel})
            self.assertIn('data-view="reader">Scientific report', page)
            self.assertIn('id="view-reader"', page)
            (root / "prioritized_findings.html").write_text('changed')
            self.assertIsNone(reader_panel(root))

    def test_external_urls_handlers_and_executable_markup_are_never_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, '<script>alert(1)</script><iframe src="https://example.com"></iframe>'
                         '<p onclick="alert(2)" style="color:red">Kept</p>'
                         '<a href="javascript:alert(3)">Bad</a><img src="https://example.com/x" onerror="alert(4)">'
                         '<a href="../outside">No</a><svg><script>alert(5)</script></svg>')
            panel = reader_panel(root)
            self.assertIn('<p>Kept</p>', panel)
            for text in ('script', 'alert', 'iframe', 'onclick', 'style=', 'onerror', 'https:', '../outside', '<svg'):
                self.assertNotIn(text, panel)

    def test_legacy_dashboard_keeps_existing_opening(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(reader_panel(Path(tmp)))
        page = _render_html({"title": "Legacy", "technical_status": "complete"})
        self.assertNotIn('data-view="reader">Scientific report', page)
        self.assertIn('data-view="overview">Overview', page)
