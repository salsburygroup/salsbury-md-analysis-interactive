import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from salsbury_md_analysis_interactive.report import (
    InteractiveReportError,
    build_interactive_report,
)


class InteractiveReportTests(unittest.TestCase):
    def _root(self, temporary: str) -> Path:
        root = Path(temporary)
        (root / "results" / "pca-fes-basins").mkdir(parents=True)
        (root / "results" / "cluster-kmeans").mkdir(parents=True)
        (root / "results" / "rmsf").mkdir(parents=True)
        (root / "results" / "states").mkdir(parents=True)
        (root / "analysis-config.json").write_text(json.dumps({
            "config_schema": "salsbury-analysis-config-v1",
            "reporting": {
                "resource_table_enabled": True,
                "finding_picker_enabled": True,
                "interactive_report_enabled": True,
                "headline_findings": 1,
                "maximum_findings": 20,
            },
        }), encoding="utf-8")
        (root / "system.json").write_text(json.dumps({
            "project_id": "interactive-fixture",
            "systems": [{"system_id": "control"}],
        }), encoding="utf-8")
        (root / "preflight.report.json").write_text(json.dumps({
            "technical_status": "complete",
            "scientific_status": "not evaluated",
            "issues": [{
                "severity": "warning", "code": "FIXTURE_WARNING",
                "message": "Review this synthetic fixture.",
            }],
        }), encoding="utf-8")
        (root / "prioritized_findings.json").write_text(json.dumps({
            "technical_status": "complete",
            "scientific_status": "not evaluated",
            "candidate_count": 1,
            "reported_count": 1,
            "headline_count": 1,
            "secondary_count": 0,
            "searchable_candidate_count": 2,
            "silent_omission_count": 0,
            "findings": [{
                "finding_id": "finding-000001",
                "presentation_tier": "headline",
                "category": "free_energy_surface",
                "module_id": "pca_fes_basins",
                "statement": "Basin 1 contains the largest observed frame fraction.",
                "evidence_level": "descriptive",
                "system_ids": ["control"],
                "effect_value": 0.75,
                "statistically_significant": None,
                "report_path": "results/pca-fes-basins/report.json",
            }],
            "headline_findings": [{
                "finding_id": "finding-000001",
                "presentation_tier": "headline",
                "category": "free_energy_surface",
                "module_id": "pca_fes_basins",
                "statement": "Basin 1 contains the largest observed frame fraction.",
                "evidence_level": "descriptive",
                "system_ids": ["control"],
                "effect_value": 0.75,
                "statistically_significant": None,
                "report_path": "results/pca-fes-basins/report.json",
            }],
            "secondary_findings": [],
            "all_candidates": [{
                "finding_id": "finding-000001",
                "presentation_tier": "headline",
                "category": "free_energy_surface",
                "module_id": "pca_fes_basins",
                "statement": "Basin 1 contains the largest observed frame fraction.",
                "evidence_level": "descriptive",
                "system_ids": ["control"],
                "effect_value": 0.75,
                "statistically_significant": None,
                "report_path": "results/pca-fes-basins/report.json",
            }, {
                "finding_id": "finding-000002",
                "presentation_tier": "additional_candidate",
                "category": "structural_dynamics",
                "module_id": "pooled_rmsf",
                "statement": "An additional ranked candidate remains searchable.",
                "evidence_level": "descriptive",
                "system_ids": ["control"],
                "effect_value": 1.2,
                "statistically_significant": None,
                "report_path": "results/rmsf/report.json",
            }],
            "module_accounting": [{
                "module_id": "pca_fes_basins",
                "review_role": "scientific_result",
                "report_count": 1,
                "candidate_count": 1,
                "reported_finding_count": 1,
                "disposition": "ranked_candidates",
                "reason": "The module produced automated candidates.",
            }],
            "quality_control_records": [{
                "module_id": "structural_integrity_qc",
                "severity": "warning",
                "status": "review_required",
                "statement": "Review the structural fixture.",
                "report_path": "results/structural-qc/report.json",
            }],
        }), encoding="utf-8")
        (root / "analysis_resource_and_frame_table.json").write_text(json.dumps({
            "technical_status": "complete", "scientific_status": "not evaluated",
            "rows": [{
                "module_id": "pca_fes_basins", "technical_status": "complete",
                "total_cpu_seconds": 2.0, "wall_seconds": 3.0,
                "maximum_resident_memory_mib": 40.0,
                "selected_source_physical_frames": 100,
                "source_physical_frames_available": 400,
            }],
        }), encoding="utf-8")
        (root / "sampling-plan.json").write_text(json.dumps({
            "technical_status": "complete",
            "scientific_status": "not evaluated",
            "method_plans": [{
                "module_id": "pca_fes_basins", "frame_stride": 4,
            }],
        }), encoding="utf-8")
        landscape = {
            "bounds": {
                "x_min_angstrom": -1.0, "x_max_angstrom": 1.0,
                "y_min_angstrom": -1.0, "y_max_angstrom": 1.0,
            },
            "grid": [
                {
                    "x_bin": x, "y_bin": y, "count": 25,
                    "relative_free_energy_kcal_per_mol": float(x + y),
                    "basin_id": 1,
                }
                for x in range(2) for y in range(2)
            ],
            "basins": [{
                "basin_id": 1, "root_x_bin": 0, "root_y_bin": 0,
                "assigned_count": 100, "assigned_fraction": 1.0,
            }],
        }
        (root / "results" / "pca-fes-basins" / "report.json").write_text(
            json.dumps({
                "module_id": "pca_fes_basins", "technical_status": "complete",
                "scientific_status": "not evaluated", "pca_basis": {
                    "x_component": 1, "y_component": 2,
                },
                "primary_smoothing_sigma_bins": 0.0,
                "smoothing_landscapes": [{
                    "smoothing_sigma_bins": 0.0, "landscape": landscape,
                    "per_system_landscapes": [],
                }],
                "landscape": landscape, "issues": [],
            }), encoding="utf-8"
        )
        (root / "results" / "cluster-kmeans" / "report.json").write_text(
            json.dumps({
                "module_id": "clustering_kmeans", "technical_status": "complete",
                "scientific_status": "not evaluated", "selected_model": {
                    "k": 2, "silhouette": 0.61, "cluster_sizes": [60, 40],
                }, "issues": [],
            }), encoding="utf-8"
        )
        (root / "results" / "rmsf" / "report.json").write_text(
            json.dumps({
                "module_id": "pooled_rmsf", "technical_status": "complete",
                "scientific_status": "not evaluated", "systems": [{
                    "system_id": "control", "atom_statistics": [{
                        "chain_id": "A", "residue_name": "CYS",
                        "residue_number": 1, "insertion_code": "",
                        "atom_name": "CA", "frame_pooled_rmsf_angstrom": 1.2,
                    }],
                }], "issues": [],
            }), encoding="utf-8"
        )
        pdb = (
            "ATOM      1  CA  CYS A   1       0.000   0.000   0.000  1.00  1.20           C  \n"
            "HETATM    2 ZN   ZN  A 101       2.000   0.000   0.000  1.00  0.00          ZN  \n"
            "END\n"
        )
        (root / "results" / "states" / "representative-1.pdb").write_text(
            pdb, encoding="utf-8"
        )
        return root

    def test_builds_offline_findings_figures_and_molecule_browser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            result = build_interactive_report(root)
            self.assertEqual(result["technical_status"], "complete")
            self.assertEqual(result["scientific_status"], "not evaluated")
            index = root / "interactive-report" / "index.html"
            manifest = json.loads(
                (root / "interactive-report" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            text = index.read_text(encoding="utf-8")
            self.assertEqual(manifest["module_report_count"], 3)
            self.assertEqual(
                manifest["generator_package"], "salsbury-md-analysis-interactive"
            )
            self.assertEqual(manifest["generator_version"], "0.1.1")
            self.assertEqual(manifest["finding_count"], 1)
            self.assertEqual(manifest["headline_finding_count"], 1)
            self.assertEqual(manifest["secondary_finding_count"], 0)
            self.assertEqual(manifest["searchable_candidate_count"], 2)
            self.assertEqual(manifest["picker_accounted_module_count"], 1)
            self.assertEqual(manifest["picker_qc_record_count"], 1)
            self.assertEqual(manifest["picker_silent_omission_count"], 0)
            self.assertEqual(manifest["inline_structure_count"], 1)
            self.assertEqual(manifest["network_dependency"], "none")
            self.assertEqual(
                manifest["index_sha256"], hashlib.sha256(index.read_bytes()).hexdigest()
            )
            for marker in (
                "Highest-priority findings", "Molecular states & figures",
                "All analyses", "Resources, frames, and sampling",
                "representative-1", "Basin 1 contains",
                "Complete picker accounting", "ranked_candidates",
                "Picker QC and interpretation records",
                "Additional candidates (",
                "An additional ranked candidate remains searchable.",
                "Review the structural fixture",
                '\"analysis_frame_stride\":4',
            ):
                self.assertIn(marker, text)
            self.assertNotIn("https://", text)
            reused = build_interactive_report(root)
            self.assertTrue(reused["reused"])

    def test_existing_report_hash_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            build_interactive_report(root)
            with (root / "interactive-report" / "index.html").open(
                "a", encoding="utf-8"
            ) as handle:
                handle.write("tamper")
            with self.assertRaises(InteractiveReportError):
                build_interactive_report(root)

    def test_nonfinite_scientific_values_become_strict_json_nulls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            report_path = root / "results" / "pca-fes-basins" / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["undefined_score"] = -math.inf
            report_path.write_text(
                json.dumps(report, allow_nan=True), encoding="utf-8"
            )

            result = build_interactive_report(root)
            html_text = Path(result["index_path"]).read_text(encoding="utf-8")
            embedded_json = html_text.split(
                '<script id="report-data" type="application/json">', 1
            )[1].split("</script>", 1)[0]
            self.assertNotIn("-Infinity", embedded_json)
            self.assertNotIn("NaN", embedded_json)
            self.assertIn('\"undefined_score\":null', embedded_json)

    def test_inline_structure_limits_are_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            result = build_interactive_report(
                root, maximum_inline_structures=0,
            )
            self.assertEqual(result["inline_structure_count"], 0)
            self.assertEqual(result["omitted_structure_count"], 1)

    def test_empty_directory_is_not_accepted_as_an_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(InteractiveReportError, "source reports"):
                build_interactive_report(Path(temporary))


if __name__ == "__main__":
    unittest.main()
