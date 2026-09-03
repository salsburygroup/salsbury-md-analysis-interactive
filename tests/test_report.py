import hashlib
import json
import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from salsbury_md_analysis_interactive.report import (
    InteractiveReportError,
    build_interactive_report,
)


class InteractiveReportTests(unittest.TestCase):
    def _add_presentation_artifacts(self, root: Path) -> None:
        artifact_root = root / "presentation-artifacts"
        fes_path = artifact_root / "free-energy" / "primary-fes.svg"
        rg_path = artifact_root / "structural-dynamics" / "rg-histogram.svg"
        table_path = artifact_root / "free-energy" / "state-populations.csv"
        for path in (fes_path, rg_path, table_path):
            path.parent.mkdir(parents=True, exist_ok=True)
        fes_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><text x="5" y="15">'
            'PC 1 (A); PC 2 (A); free energy (kcal/mol)</text></svg>',
            encoding="utf-8",
        )
        rg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><text x="5" y="15">'
            'Radius of gyration (A); frame count; Scott bins</text></svg>',
            encoding="utf-8",
        )
        table_path.write_text(
            "system_id,state_id,frame_fraction\ncontrol,1,0.75\n",
            encoding="utf-8",
        )

        def record(
            artifact_id, artifact_type, module_id, analysis_class,
            purpose, title, path, context, media_type,
        ):
            return {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "module_id": module_id,
                "analysis_class": analysis_class,
                "purpose": purpose,
                "title": title,
                "relative_path": str(path.relative_to(artifact_root)),
                "media_type": media_type,
                "context": context,
                "primary_human_output": True,
                "source_report_paths": ["results/pca-fes-basins/report.json"],
                "source_report_sha256": ["0" * 64],
                "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "artifact_size_bytes": path.stat().st_size,
            }

        artifacts = [
            record(
                "figure-pca-primary", "figure", "pca_fes_basins",
                "free_energy_surfaces", "primary_fes", "Primary PCA-FES",
                fes_path, {"system_id": "control"}, "image/svg+xml",
            ),
            record(
                "table-pca-populations", "table", "pca_fes_basins",
                "free_energy_surfaces", "state_populations",
                "FES state populations", table_path,
                {"system_id": "control"}, "text/csv",
            ),
            record(
                "figure-rg-histogram", "figure", "replica_rmsd_rg",
                "structural_dynamics", "radius_of_gyration_histogram",
                "Radius of gyration Scott-rule histogram", rg_path,
                {"system_id": "control", "binning_rule": "Scott"},
                "image/svg+xml",
            ),
        ]
        (artifact_root / "presentation-manifest.json").write_text(
            json.dumps({
                "presentation_manifest_schema": "salsbury-presentation-artifacts-v1",
                "technical_status": "complete",
                "artifact_count": len(artifacts),
                "adapted_report_count": 3,
                "unadapted_report_count": 0,
                "artifacts": artifacts,
            }),
            encoding="utf-8",
        )
        findings_path = root / "prioritized_findings.json"
        findings = json.loads(findings_path.read_text(encoding="utf-8"))
        for key in ("findings", "headline_findings", "all_candidates"):
            for finding in findings[key]:
                if finding["finding_id"] == "finding-000001":
                    finding["presentation_artifacts"] = [
                        {"artifact_id": "figure-pca-primary"},
                        {"artifact_id": "table-pca-populations"},
                    ]
        findings_path.write_text(json.dumps(findings), encoding="utf-8")

    def _root(self, temporary: str) -> Path:
        root = Path(temporary)
        (root / "results" / "pca-fes-basins").mkdir(parents=True)
        (root / "results" / "cluster-kmeans").mkdir(parents=True)
        (root / "results" / "rmsf").mkdir(parents=True)
        structure_root = (
            root / "results" / "08_clustering" / "state_coordinate_exports"
            / "shared-fes-sigma1" / "state-0001" / "system-control"
        )
        structure_root.mkdir(parents=True)
        cluster_structure_root = (
            root / "results" / "08_clustering" / "state_coordinate_exports"
            / "shared-kmeans" / "state-0001" / "system-control"
        )
        cluster_structure_root.mkdir(parents=True)
        (root / "analysis-config.json").write_text(json.dumps({
            "config_schema": "salsbury-analysis-config-v1",
            "reporting": {
                "resource_table_enabled": True,
                "finding_picker_enabled": True,
                "interactive_report_enabled": True,
                "minimum_headline_findings": 10,
                "headline_findings": 12,
                "maximum_findings": 50,
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
            "presentation_contract": {
                "contract_id": "headline-secondary-50-v1",
                "headline_count_range": [10, 12],
                "highlighted_findings_total": 50,
                "secondary_count_range": [38, 40],
                "selected_headline_count": 1,
                "status": "candidate_limited",
                "candidate_limited": True,
                "headline_selection": "bh_significance_at_boundary",
            },
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
                "primary_smoothing_sigma_bins": 1.0,
                "smoothing_landscapes": [
                    {
                        "smoothing_sigma_bins": 0.0, "landscape": landscape,
                        "per_system_landscapes": [],
                    },
                    {
                        "smoothing_sigma_bins": 1.0, "landscape": landscape,
                        "per_system_landscapes": [],
                    },
                ],
                "landscape": landscape, "issues": [],
            }), encoding="utf-8"
        )
        (root / "results" / "cluster-kmeans" / "report.json").write_text(
            json.dumps({
                "module_id": "clustering_kmeans", "technical_status": "complete",
                "scientific_status": "not evaluated", "selected_model": {
                    "k": 2, "silhouette": 0.61, "cluster_sizes": [60, 40],
                }, "state_population_comparison": {"system_populations": [{
                    "system_id": "control", "state_populations": [
                        {"state_id": 1, "count": 60, "fraction_of_assigned": 0.6},
                        {"state_id": 2, "count": 40, "fraction_of_assigned": 0.4},
                    ],
                }]}, "issues": [{
                    "severity": "warning", "code": "CLUSTER_REVIEW_NOTE",
                    "message": "Review cluster separation in the clustering tab.",
                }],
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
        (root / "results" / "pca-fes-basins" / "surface.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">'
            '<circle cx="10" cy="10" r="8" fill="#1c7166"/></svg>',
            encoding="utf-8",
        )
        pdb = (
            "ATOM      1  CA  CYS A   1       0.000   0.000   0.000  1.00  1.20           C  \n"
            "HETATM    2 ZN   ZN  A 101       2.000   0.000   0.000  1.00  0.00          ZN  \n"
            "HETATM    3  O   HOH W 201       4.000   0.000   0.000  1.00  0.00           O  \n"
            "CONECT    1    2    3\n"
            "END\n"
        )
        (structure_root / "representative-1.pdb").write_text(
            pdb, encoding="utf-8"
        )
        (cluster_structure_root / "representative-1.pdb").write_text(
            pdb, encoding="utf-8"
        )
        return root

    def test_builds_offline_findings_figures_and_molecule_browser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            self._add_presentation_artifacts(root)
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
            self.assertEqual(manifest["generator_version"], "0.1.3")
            self.assertEqual(manifest["finding_count"], 1)
            self.assertEqual(manifest["headline_finding_count"], 1)
            self.assertEqual(manifest["secondary_finding_count"], 0)
            self.assertEqual(manifest["searchable_candidate_count"], 2)
            self.assertEqual(manifest["picker_accounted_module_count"], 1)
            self.assertEqual(manifest["picker_qc_record_count"], 1)
            self.assertEqual(manifest["picker_silent_omission_count"], 0)
            self.assertEqual(manifest["inline_structure_count"], 2)
            self.assertEqual(manifest["inline_figure_count"], 3)
            self.assertEqual(manifest["presentation_artifact_count"], 3)
            self.assertEqual(manifest["presentation_figure_count"], 2)
            self.assertEqual(manifest["presentation_table_count"], 1)
            self.assertEqual(manifest["network_dependency"], "none")
            self.assertEqual(
                manifest["index_sha256"], hashlib.sha256(index.read_bytes()).hexdigest()
            )
            for marker in (
                "Highest-priority findings", "Molecular states & figures",
                "All reports", "Resources, frames, and sampling",
                "representative-1", "Basin 1 contains",
                "Complete picker accounting", "ranked_candidates",
                "Additional QC records",
                "Additional candidates (",
                "An additional ranked candidate remains searchable.",
                "Review the structural fixture",
                '\"analysis_frame_stride\":4',
                "Radius of gyration Scott-rule histogram",
                "table-pca-populations",
            ):
                self.assertIn(marker, text)
            for removed in (
                "Interpretation boundary.", "Scientific status: not evaluated",
                "single or inferred system", ">raw evidence<",
            ):
                self.assertNotIn(removed, text)
            self.assertIn('"descriptive":"observational"', text)
            self.assertIn(
                "humanizeText(JSON.stringify(r.preview,null,2))", text
            )
            self.assertIn("$3Dmol.createViewer", text)
            self.assertIn("Free-energy surfaces", text)
            self.assertIn("Clustering, best silhouette first", text)
            self.assertIn("Population (%)", text)
            self.assertIn("View figure", text)
            self.assertIn("PC ${v.x_component||1} coordinate (Å)", text)
            self.assertTrue(
                (root / "interactive-report" / "evidence" / "results"
                 / "cluster-kmeans" / "report.json").is_file()
            )
            portable_pdb = (
                root / "interactive-report" / "evidence" / "results"
                / "08_clustering" / "state_coordinate_exports"
                / "shared-fes-sigma1"
                / "state-0001" / "system-control" / "representative-1.pdb"
            )
            self.assertTrue(portable_pdb.is_file())
            portable_pdb_text = portable_pdb.read_text(encoding="utf-8")
            self.assertNotIn("HOH", portable_pdb_text)
            self.assertIn("CONECT    1    2", portable_pdb_text)
            self.assertNotIn("    3", portable_pdb_text.split("CONECT", 1)[1])
            self.assertTrue(
                (root / "interactive-report" / "evidence" / "results"
                 / "pca-fes-basins" / "surface.svg").is_file()
            )
            self.assertTrue(
                (root / "interactive-report" / "evidence"
                 / "presentation-artifacts" / "structural-dynamics"
                 / "rg-histogram.svg").is_file()
            )
            self.assertTrue(
                (root / "interactive-report" / "evidence"
                 / "presentation-artifacts" / "free-energy"
                 / "state-populations.csv").is_file()
            )
            data_match = re.search(
                r'<script id="report-data" type="application/json">(.*?)</script>',
                text,
            )
            self.assertIsNotNone(data_match)
            embedded = json.loads(data_match.group(1))
            self.assertEqual(
                [
                    row["artifact_id"]
                    for row in embedded["headline_findings"][0][
                        "resolved_presentation_artifacts"
                    ]
                ],
                ["figure-pca-primary", "table-pca-populations"],
            )
            self.assertNotIn(
                "clustering_kmeans",
                {str(row.get("module_id")) for row in embedded["qc_issues"]},
            )
            cluster_visual = next(
                visual
                for report in embedded["reports"]
                if report["module_id"] == "clustering_kmeans"
                for visual in report["visuals"]
            )
            self.assertEqual(cluster_visual["method_name"], "K-means")
            self.assertEqual(
                cluster_visual["system_populations"][0]["system_id"], "control"
            )
            self.assertEqual(
                len(cluster_visual["representative_structures"]), 1
            )
            fes_visuals = [
                visual
                for report in embedded["reports"]
                if report["module_id"] == "pca_fes_basins"
                for visual in report["visuals"]
            ]
            self.assertEqual(
                [
                    len(visual["representative_structures"])
                    for visual in fes_visuals
                ],
                [1],
            )
            self.assertEqual(
                fes_visuals[0]["smoothing_sigma_bins"], 1.0
            )
            self.assertIn("artifactOrder", text)
            self.assertIn("connect-src 'none'", text)
            self.assertNotRegex(text, r'<script[^>]+src=["\']https?://')
            for official_wake_forest_color in (
                "--wake-black:#000", "--wake-gold:#9e7e38",
                "--web-gold:#8c6d2c", "--athletics-gold:#ceb888",
            ):
                self.assertIn(official_wake_forest_color, text)
            self.assertIn("--red:#9d2235", text)
            self.assertNotIn("--teal:#1c7166", text)
            reused = build_interactive_report(root)
            self.assertTrue(reused["reused"])

    def test_large_state_reports_stream_visual_fields(self):
        try:
            import ijson  # noqa: F401
        except ImportError:
            self.skipTest("ijson is not installed")
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            with patch(
                "salsbury_md_analysis_interactive.report._MAXIMUM_REPORT_PARSE_BYTES",
                1,
            ):
                result = build_interactive_report(root)
            html_text = Path(result["index_path"]).read_text(encoding="utf-8")
            embedded_json = html_text.split(
                '<script id="report-data" type="application/json">', 1
            )[1].split("</script>", 1)[0]
            embedded = json.loads(embedded_json)
            fes_report = next(
                row for row in embedded["reports"]
                if row["module_id"] == "pca_fes_basins"
            )
            clustering_report = next(
                row for row in embedded["reports"]
                if row["module_id"] == "clustering_kmeans"
            )
            self.assertEqual(fes_report["visuals"][0]["kind"], "fes")
            self.assertEqual(
                clustering_report["visuals"][0]["method_name"], "K-means"
            )
            self.assertEqual(
                clustering_report["visuals"][0]["silhouette"], 0.61
            )

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

    def test_fifty_highlights_and_all_additional_candidates_remain_indexed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            candidates = [
                {
                    "finding_id": f"finding-{index + 1:06d}",
                    "presentation_tier": (
                        "headline" if index < 11 else
                        "secondary" if index < 50 else
                        "additional_candidate"
                    ),
                    "category": "other_physical",
                    "module_id": "optional_observables",
                    "statement": f"Searchable candidate {index + 1}",
                    "evidence_level": "descriptive",
                    "system_ids": ["control"],
                    "effect_value": float(60 - index),
                    "statistically_significant": index < 11,
                    "report_path": "results/rmsf/report.json",
                }
                for index in range(60)
            ]
            findings_path = root / "prioritized_findings.json"
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            findings.update({
                "candidate_count": 60,
                "reported_count": 50,
                "headline_count": 11,
                "secondary_count": 39,
                "searchable_candidate_count": 60,
                "additional_candidate_count": 10,
                "findings": candidates[:50],
                "headline_findings": candidates[:11],
                "secondary_findings": candidates[11:50],
                "all_candidates": candidates,
                "presentation_contract": {
                    "contract_id": "headline-secondary-50-v1",
                    "headline_count_range": [10, 12],
                    "highlighted_findings_total": 50,
                    "secondary_count_range": [38, 40],
                    "selected_headline_count": 11,
                    "status": "satisfied",
                    "candidate_limited": False,
                    "headline_selection": "bh_significance_at_boundary",
                },
            })
            findings_path.write_text(json.dumps(findings), encoding="utf-8")

            result = build_interactive_report(root)
            manifest = json.loads(
                (root / "interactive-report" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            html_text = Path(result["index_path"]).read_text(encoding="utf-8")
            self.assertEqual(manifest["headline_finding_count"], 11)
            self.assertEqual(manifest["secondary_finding_count"], 39)
            self.assertEqual(manifest["finding_count"], 50)
            self.assertEqual(manifest["searchable_candidate_count"], 60)
            self.assertEqual(
                manifest["finding_presentation_contract"]["status"],
                "satisfied",
            )
            self.assertIn("Searchable candidate 60", html_text)
            self.assertIn("largest and most scientifically relevant", html_text)

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
            self.assertEqual(result["omitted_structure_count"], 2)

    def test_empty_directory_is_not_accepted_as_an_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(InteractiveReportError, "source reports"):
                build_interactive_report(Path(temporary))


if __name__ == "__main__":
    unittest.main()
