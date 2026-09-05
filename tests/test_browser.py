"""Opt-in installed-package browser smoke test; no network or scientific execution."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

import test_report
from salsbury_md_analysis_interactive.report import build_interactive_report


@unittest.skipUnless(os.environ.get("SALSBURY_BROWSER_TESTS") == "1", "opt-in browser test")
class BrowserTests(unittest.TestCase):
    def test_offline_controls_links_and_markup_are_inert(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as temporary:
            fixture = test_report.InteractiveReportTests()
            root = fixture._root(temporary)
            fixture._add_presentation_artifacts(root)
            findings = root / "prioritized_findings.json"
            document = json.loads(findings.read_text())
            sentinel = '</ScRiPt><script id="injected-audit">window.injectedAudit=true</script>'
            document["metadata_audit_text"] = sentinel
            # This field is rendered, so both embedded JSON and DOM interpolation are tested.
            for key in ("findings", "headline_findings", "all_candidates"):
                for row in document.get(key, []):
                    row["statement"] += sentinel
            findings.write_text(json.dumps(document))
            build_interactive_report(root)
            with sync_playwright() as pw:
                launch = {"headless": True}
                if os.environ.get("SALSBURY_BROWSER_EXECUTABLE"):
                    launch["executable_path"] = os.environ["SALSBURY_BROWSER_EXECUTABLE"]
                browser = pw.chromium.launch(**launch)
                page = browser.new_page()
                errors, external = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda req: external.append(req.url)
                        if req.url.startswith(("https:", "http:")) else None)
                page.goto((root / "interactive-report/index.html").as_uri())
                page.wait_for_selector("#overview-findings .finding")
                self.assertEqual(page.locator("#injected-audit").count(), 0)
                self.assertFalse(page.evaluate("Boolean(window.injectedAudit)"))
                page.locator('button[data-view="findings"]').click()
                page.locator("#finding-search").fill("Basin")
                self.assertIn("Basin", page.locator("#findings-list").inner_text())
                page.locator('#findings-list [data-artifact-id="figure-pca-primary"]').first.click()
                self.assertTrue(page.locator("#artifact-figure-pca-primary").is_visible())
                page.locator('button[data-view="molecules"]').click()
                self.assertTrue(page.locator("#molecule-viewer canvas").count())
                for href in page.locator("a[href]").evaluate_all("els=>els.map(e=>e.href)"):
                    parsed = urlparse(href)
                    if parsed.scheme == "file":
                        self.assertTrue(Path(unquote(parsed.path)).is_file(), href)
                self.assertFalse(external, external)
                self.assertFalse(errors, errors)
                browser.close()
