import json
import tempfile
import unittest
import configparser
from packaging.specifiers import SpecifierSet
from html.parser import HTMLParser
from pathlib import Path
import hashlib
from salsbury_md_analysis_interactive.report import _render_html, build_interactive_report, InteractiveReportError
import test_report


class AuditRegressions(unittest.TestCase):
    def _extension(self, directory):
        extension = Path(directory) / "extension"
        extension.mkdir()
        root = test_report.InteractiveReportTests()._root(str(extension))
        upstream = Path(directory) / "upstream"
        report = next(root.glob("results/**/report.json"))
        relative = str(report.relative_to(root))
        source = upstream / relative
        source.parent.mkdir(parents=True)
        report.rename(source)
        report.symlink_to(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        contract = {
            "extension_contract_schema": "salsbury-experimental-after-main-v1",
            "technical_status": "complete", "immutable_upstream": True,
            "upstream_main_campaign": str(upstream),
            "reusable_reports": [{"report_relative_path": relative,
                "report_sha256": digest, "summary_sha256": "0" * 64}],
        }
        (root / "experimental-after-main-contract.json").write_text(json.dumps(contract))
        return root, source

    def test_extension_copies_only_hash_pinned_upstream_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source = self._extension(directory)
            built = build_interactive_report(root)
            reused = build_interactive_report(root)
            self.assertEqual(reused["source_snapshot_status"], "unchanged")
            source.write_text('{"changed":true}')
            self.assertEqual(build_interactive_report(root)["source_snapshot_status"], "changed")
            self.assertTrue(Path(built["output_directory"], "index.html").is_file())

    def test_extension_rejects_changed_or_unlisted_upstream_report(self):
        for alteration in ("changed", "unlisted", "wrong-target"):
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as directory:
                root, source = self._extension(directory)
                if alteration == "changed":
                    source.write_text('{"changed":true}')
                elif alteration == "unlisted":
                    (root / "experimental-after-main-contract.json").unlink()
                else:
                    original = next(root.glob("results/**/report.json"))
                    duplicate = source.parent / "different.json"
                    duplicate.write_bytes(source.read_bytes())
                    original.unlink()
                    original.symlink_to(duplicate)
                with self.assertRaises(InteractiveReportError):
                    build_interactive_report(root)

    def test_dependency_accepts_tested_stable_and_experimental_core(self):
        config = configparser.ConfigParser()
        config.read(Path(__file__).resolve().parents[1] / "setup.cfg")
        requirement = next(line.strip() for line in config["options"]["install_requires"].splitlines()
                           if line.strip().startswith("salsbury-md-analysis"))
        versions = SpecifierSet(requirement.removeprefix("salsbury-md-analysis"))
        for version in ("0.1.2", "0.2.0a2"):
            self.assertTrue(versions.contains(version, prereleases=True))
        self.assertFalse(versions.contains("0.3.0", prereleases=True))

    def test_embedded_json_cannot_close_script_case_insensitively(self):
        class Scripts(HTMLParser):
            tags = None
            def __init__(self):
                super().__init__()
                self.tags = []
            def handle_starttag(self, tag, attrs):
                if tag == "script":
                    self.tags.append(dict(attrs))
        for text in ("</ScRiPt><script id='sentinel'></script>", "<!--<SCRIPT> & >"):
            parser = Scripts()
            parser.feed(_render_html({"title": "Audit", "technical_status": "complete", "probe": text}))
            self.assertFalse(any(t.get("id") == "sentinel" for t in parser.tags))
            self.assertEqual(len(parser.tags), 3)

    def test_reuse_checks_packaged_evidence_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = test_report.InteractiveReportTests()._root(directory)
            built = build_interactive_report(root)
            target = Path(built["output_directory"])
            evidence = next((target / "evidence").rglob("*.json"))
            evidence.write_text('{"modified":true}')
            with self.assertRaises(InteractiveReportError):
                build_interactive_report(root)

    def test_reuse_checks_missing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = test_report.InteractiveReportTests()._root(directory)
            built = build_interactive_report(root)
            evidence = next((Path(built["output_directory"]) / "evidence").rglob("*.json"))
            evidence.unlink()
            with self.assertRaises(InteractiveReportError):
                build_interactive_report(root)
