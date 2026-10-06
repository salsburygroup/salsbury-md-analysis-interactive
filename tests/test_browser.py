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
    def test_filter_computed_visibility_and_noninline_pdb_fallback(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as temporary:
            fixture = test_report.InteractiveReportTests()
            root = fixture._root(temporary)
            fixture._add_presentation_artifacts(root)
            build_interactive_report(root, maximum_inline_structures=0)
            with sync_playwright() as pw:
                launch = {"headless": True}
                if os.environ.get("SALSBURY_BROWSER_EXECUTABLE"):
                    launch["executable_path"] = os.environ["SALSBURY_BROWSER_EXECUTABLE"]
                browser = pw.chromium.launch(**launch)
                page = browser.new_page()
                page.goto((root / "interactive-report/index.html").as_uri())
                page.locator('button[data-view="findings"]').click()
                rows = page.locator('#findings-list .finding')
                count = rows.count()
                self.assertGreater(count, 0)
                for query in ('__no_finding_matches__', '', 'Basin', ''):
                    page.locator('#finding-search').fill(query)
                    state = rows.evaluate_all('els=>els.map(e=>({hidden:e.hidden,display:getComputedStyle(e).display,height:e.getBoundingClientRect().height}))')
                    for row in state:
                        self.assertEqual(row['display'] == 'none', row['hidden'])
                        self.assertEqual(row['height'] == 0, row['hidden'])
                    if query == '__no_finding_matches__':
                        self.assertTrue(all(row['hidden'] for row in state))
                    self.assertEqual(rows.count(), count)
                # Exercise each selector and combinations; test real computed
                # visibility rather than accepting a changed result count alone.
                for control in ('finding-tier', 'finding-system', 'finding-category'):
                    selector = page.locator('#' + control)
                    for value in selector.locator('option').evaluate_all('els=>els.map(e=>e.value)'):
                        selector.select_option(value)
                        states = rows.evaluate_all('els=>els.map(e=>({hidden:e.hidden,display:getComputedStyle(e).display,height:e.getBoundingClientRect().height}))')
                        for row in states:
                            self.assertEqual(row['display'] == 'none', row['hidden'])
                            self.assertEqual(row['height'] == 0, row['hidden'])
                    selector.select_option('')
                self.assertEqual(page.locator('#findings-list .finding:visible').count(), count)
                page.evaluate("go('states')")
                self.assertEqual(page.locator('[data-structure-id]').count(), 0)
                links = page.get_by_role('link', name='Open representative PDB (not embedded)')
                self.assertGreater(links.count(), 0)
                for href in links.evaluate_all('els=>els.map(e=>e.href)'):
                    self.assertTrue(Path(unquote(urlparse(href).path)).is_file())
                browser.close()

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
