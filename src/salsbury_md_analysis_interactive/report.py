"""Offline-first interactive browser for completed analysis campaigns.

The generated report is one self-contained HTML document plus a small,
hash-bound manifest.  It does not require a Python server, a JavaScript package
manager, or an internet connection.  Raw analysis artifacts remain the source
of record and are linked rather than rewritten.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

class InteractiveReportError(ValueError):
    """Raised when an interactive result cannot preserve source evidence."""


_IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}
_MAXIMUM_REPORT_PARSE_BYTES = 128_000_000
_MAXIMUM_PORTABLE_REPORT_BYTES = 5_000_000
_MAXIMUM_PORTABLE_EVIDENCE_BYTES = 100_000_000
_MAXIMUM_STREAMED_VISUAL_ROWS = 500_000
_GENERATOR_PACKAGE = "salsbury-md-analysis-interactive"
_GENERATOR_VERSION = "0.1.2"
_THREEDMOL_PATH = Path(__file__).with_name("vendor") / "3Dmol-min.js"

_MODULE_LABELS = {
    "alternative_clustering": "Alternative clustering methods",
    "clustering_imwkmeans": "Minkowski-weighted K-means",
    "clustering_kmeans": "K-means",
    "clustering_hdbscan": "HDBSCAN",
    "common_pca": "Shared PCA",
    "convergence_uncertainty": "Convergence and uncertainty",
    "coordinate_cache": "Coordinate preparation",
    "dccm": "Dynamic cross-correlation",
    "dna_geometry": "DNA geometry",
    "dihedral_distributions": "Dihedral distributions",
    "ensemble_pocket_dynamics": "Pocket dynamics",
    "energetic_network_embeddings": "Energetic network embeddings",
    "generalized_correlation_and_information": "Nonlinear correlations",
    "hydrogen_bond_discovery": "Hydrogen-bond discovery",
    "hydrogen_bonds": "Hydrogen bonds",
    "hydrogen_bond_comparison": "Hydrogen-bond comparisons",
    "hydration_density_channels": "Hydration-density channels",
    "information_dynamics": "Information dynamics",
    "ion_atmosphere": "Ion atmosphere",
    "ion_coordination": "Ion coordination",
    "ion_geometry": "Ion geometry",
    "ion_coordination_geometry": "Ion coordination geometry",
    "integrated_comparison": "Integrated comparison",
    "interaction_fingerprints": "Interaction fingerprints",
    "interaction_persistence": "Interaction persistence",
    "markov_state_models": "Markov state models",
    "pca_fes_basins": "Free-energy surfaces and basins",
    "pald_community_analysis": "PaLD community analysis",
    "pooled_rmsf": "Root-mean-square fluctuations",
    "rmsd_radius_of_gyration": "RMSD and radius of gyration",
    "replica_rmsd_rg": "RMSD and radius of gyration",
    "radial_distribution_functions": "Radial distribution functions",
    "sasa": "Solvent-accessible surface area",
    "solvent_accessible_surface_area": "Solvent-accessible surface area",
    "scalar_feature_distributions": "Scalar-feature distributions",
    "secondary_structure": "Secondary structure",
    "state_coordinate_exports": "State coordinate exports",
    "representative_frames": "Representative frames",
    "structural_integrity_qc": "Structural-integrity QC",
    "time_lagged_independent_component_analysis": "Time-lagged independent component analysis",
    "water_mediated_hydrogen_bond_networks": "Water-mediated hydrogen-bond networks",
    "allosteric_pathways": "Allosteric pathways",
    "grouped_ml": "Grouped machine learning",
    "grouped_regularized_classification": "Grouped regularized classification",
    "helical_mechanics": "Helical mechanics",
    "multivalent_molecular_bridges": "Multivalent molecular bridges",
    "nucleic_acid_geometry": "Nucleic-acid geometry",
    "nucleic_acid_structure": "Nucleic-acid structure",
    "optional_observables": "Additional physical observables",
    "perturbation_response_dynamics": "Perturbation-response dynamics",
    "random_feature_koopman": "Random-feature Koopman analysis",
    "reactive_path_ensembles": "Reactive-path ensembles",
    "rmsf_visualization_export": "RMSF structure export",
    "spatial_interaction_ensembles": "Spatial interaction ensembles",
    "trajectory_reweighting": "Trajectory reweighting",
}

_ALGORITHM_LABELS = {
    "affinity_propagation": "Affinity propagation",
    "gaussian_mixture": "Gaussian mixture",
    "hdbscan": "HDBSCAN",
    "intelligent_minkowski_weighted_kmeans": "Minkowski-weighted K-means",
    "mean_shift": "Mean shift",
    "minkowski_weighted_partition_around_medoids": (
        "Minkowski-weighted partitioning around medoids"
    ),
    "partition_around_medoids": "Partitioning around medoids",
    "variational_gaussian_mixture": "Variational Gaussian mixture",
    "ward_agglomerative": "Ward agglomerative clustering",
}

_ANALYSIS_CLASSES = {
    "coordinate_cache": ("preparation", "Coordinate preparation"),
    "trajectory_features": ("preparation", "Coordinate preparation"),
    "pca_fes_basins": ("free-energy", "Free-energy surfaces"),
    "common_pca": ("free-energy", "Free-energy surfaces"),
    "individual_pca": ("free-energy", "Free-energy surfaces"),
    "clustering_kmeans": ("clustering", "Clustering"),
    "clustering_imwkmeans": ("clustering", "Clustering"),
    "clustering_hdbscan": ("clustering", "Clustering"),
    "alternative_clustering": ("clustering", "Clustering"),
    "pald_community_analysis": ("clustering", "Clustering"),
    "representative_frames": ("clustering", "Clustering"),
    "state_coordinate_exports": ("clustering", "Clustering"),
    "pooled_rmsf": ("rmsf", "RMSF"),
    "rmsf_visualization_export": ("rmsf", "RMSF"),
    "rmsd_radius_of_gyration": ("rmsd-rg", "RMSD and radius of gyration"),
    "replica_rmsd_rg": ("rmsd-rg", "RMSD and radius of gyration"),
    "sasa": ("sasa", "Solvent-accessible surface area"),
    "solvent_accessible_surface_area": ("sasa", "Solvent-accessible surface area"),
    "scalar_feature_distributions": ("distributions", "Distributions and observables"),
    "optional_observables": ("distributions", "Distributions and observables"),
    "radial_distribution_functions": ("distributions", "Distributions and observables"),
    "hydrogen_bonds": ("hydrogen-bonds", "Hydrogen bonds"),
    "hydrogen_bond_discovery": ("hydrogen-bonds", "Hydrogen bonds"),
    "hydrogen_bond_comparison": ("hydrogen-bonds", "Hydrogen bonds"),
    "water_mediated_hydrogen_bond_networks": ("hydration", "Hydration and water networks"),
    "hydration_density": ("hydration", "Hydration and water networks"),
    "hydration_density_channels": ("hydration", "Hydration and water networks"),
    "ion_atmosphere": ("ions", "Ions and coordination"),
    "ion_coordination": ("ions", "Ions and coordination"),
    "ion_geometry": ("ions", "Ions and coordination"),
    "ion_coordination_geometry": ("ions", "Ions and coordination"),
    "dna_geometry": ("dna", "DNA geometry"),
    "nucleic_acid_geometry": ("dna", "DNA geometry"),
    "nucleic_acid_structure": ("dna", "DNA geometry"),
    "secondary_structure": ("local-structure", "Secondary structure and dihedrals"),
    "dihedrals": ("local-structure", "Secondary structure and dihedrals"),
    "dihedral_distributions": ("local-structure", "Secondary structure and dihedrals"),
    "dccm": ("correlations", "Correlations and networks"),
    "generalized_correlation_and_information": ("correlations", "Correlations and networks"),
    "correlation_networks": ("correlations", "Correlations and networks"),
    "information_dynamics": ("correlations", "Correlations and networks"),
    "allosteric_pathways": ("correlations", "Correlations and networks"),
    "energetic_network_embeddings": ("correlations", "Correlations and networks"),
    "interaction_fingerprints": ("correlations", "Correlations and networks"),
    "interaction_persistence": ("correlations", "Correlations and networks"),
    "multivalent_molecular_bridges": ("correlations", "Correlations and networks"),
    "perturbation_response_dynamics": ("correlations", "Correlations and networks"),
    "spatial_interaction_ensembles": ("correlations", "Correlations and networks"),
    "time_lagged_independent_component_analysis": ("kinetics", "Kinetics and state models"),
    "markov_state_models": ("kinetics", "Kinetics and state models"),
    "scalar_threshold_states": ("kinetics", "Kinetics and state models"),
    "convergence_uncertainty": ("convergence", "Convergence and uncertainty"),
    "ensemble_pocket_dynamics": ("pockets", "Pocket dynamics"),
    "helical_mechanics": ("dna", "DNA geometry"),
    "grouped_ml": ("comparisons", "System comparisons"),
    "grouped_regularized_classification": ("comparisons", "System comparisons"),
    "integrated_comparison": ("comparisons", "System comparisons"),
    "trajectory_reweighting": ("comparisons", "System comparisons"),
    "random_feature_koopman": ("kinetics", "Kinetics and state models"),
    "reactive_path_ensembles": ("kinetics", "Kinetics and state models"),
    "structural_integrity_qc": ("qc", "Quality control"),
}

_QC_MODULES = {
    "preflight", "structural_integrity_qc", "structure_qc",
    "coordinate_continuity_qc", "topology_qc",
}

_SOLVENT_RESIDUES = {
    "HOH", "WAT", "TIP3", "TIP3P", "SOL", "H2O", "SPC", "SPCE",
}

_PATH_MODULE_ALIASES = {
    "alternative-clustering": "alternative_clustering",
    "cluster-hdbscan": "clustering_hdbscan",
    "cluster-imwkmeans": "clustering_imwkmeans",
    "cluster-kmeans": "clustering_kmeans",
    "common-pca": "common_pca",
    "convergence": "convergence_uncertainty",
    "dihedrals": "dihedral_distributions",
    "dna-geometry": "nucleic_acid_geometry",
    "hydrogen-bond-comparison": "hydrogen_bond_comparison",
    "information-correlation": "generalized_correlation_and_information",
    "ion-geometry": "ion_coordination_geometry",
    "markov-models": "markov_state_models",
    "pca-fes-basins": "pca_fes_basins",
    "rdf": "radial_distribution_functions",
    "rmsd-rg": "replica_rmsd_rg",
    "rmsf": "pooled_rmsf",
    "sasa": "solvent_accessible_surface_area",
    "scalar-distributions": "scalar_feature_distributions",
    "structural-qc": "structural_integrity_qc",
    "tica": "time_lagged_independent_component_analysis",
}


def _module_from_path(relative_path: str, default: str = "other") -> str:
    normalized = relative_path.lower().replace("_", "-")
    matches = [
        (len(token), module_id)
        for token, module_id in _PATH_MODULE_ALIASES.items()
        if token in normalized
    ]
    matches.extend(
        (len(module_id), module_id)
        for module_id in _ANALYSIS_CLASSES
        if module_id.replace("_", "-") in normalized
    )
    return max(matches, default=(0, default))[1]


def _module_label(module_id: object) -> str:
    key = str(module_id or "analysis")
    return _MODULE_LABELS.get(key, key.replace("_", " ").replace("-", " ").title())


def _algorithm_label(algorithm_id: object) -> str:
    key = str(algorithm_id or "clustering")
    if key in _MODULE_LABELS:
        return _MODULE_LABELS[key]
    return _ALGORITHM_LABELS.get(
        key, key.replace("_", " ").replace("-", " ").title()
    )


def _analysis_class(module_id: object) -> tuple[str, str]:
    return _ANALYSIS_CLASSES.get(
        str(module_id), ("other", "Other analyses")
    )


def _is_qc_module(module_id: object) -> bool:
    key = str(module_id or "").lower()
    return key in _QC_MODULES or key.endswith("_qc") or "quality_control" in key


def _display_context(relative_path: str) -> str:
    """Return useful system scope without exposing internal view identifiers."""

    parts = Path(relative_path).parts
    system = next(
        (part[7:] for part in parts if part.startswith("system-") or part.startswith("system_")),
        None,
    )
    if system:
        return system.replace("_", " ")
    if "conformational-views" in parts:
        return "Shared comparison"
    return "Campaign"


def _portable_href(relative_path: str) -> str:
    return "evidence/" + relative_path.replace(os.sep, "/")


def _load_json(path: Path) -> object:
    """Load one core analysis JSON artifact without importing core internals."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(root))
    except ValueError as exc:
        raise InteractiveReportError(
            f"interactive-report asset escapes the analysis root: {path}"
        ) from exc


def _raw_link(relative_path: str) -> str:
    """Return a link inside the portable interactive-report directory."""

    return _portable_href(relative_path)


def _optional_json(path: Path) -> object | None:
    if not path.is_file():
        return None
    try:
        return _load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise InteractiveReportError(f"cannot read JSON evidence {path}: {exc}") from exc


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _json_safe(value: object) -> object:
    """Return strict JSON data, replacing non-finite scientific sentinels.

    Python otherwise emits ``NaN`` and ``Infinity`` tokens. Browsers reject
    those tokens in ``JSON.parse``. Raw reports remain linked and hash-bound;
    the interactive preview represents an undefined numeric value as ``null``.
    """

    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _preview(value: object, *, depth: int = 0, maximum_items: int = 80) -> object:
    """Return a deterministic bounded preview while leaving raw JSON linked."""

    if depth >= 6:
        if isinstance(value, (dict, list)):
            return {"preview_truncated": True, "value_type": type(value).__name__}
        return value
    if isinstance(value, dict):
        result: Dict[str, object] = {}
        for index, key in enumerate(sorted(value, key=str)):
            if str(key) in {"scientific_status", "evidence_level"}:
                continue
            if index >= maximum_items:
                result["preview_truncated_keys"] = len(value) - maximum_items
                break
            result[str(key)] = _preview(
                value[key], depth=depth + 1, maximum_items=maximum_items
            )
        return result
    if isinstance(value, list):
        if len(value) <= maximum_items:
            return [
                _preview(row, depth=depth + 1, maximum_items=maximum_items)
                for row in value
            ]
        step = max(1, math.ceil(len(value) / maximum_items))
        sampled = value[::step][:maximum_items]
        return {
            "preview_truncated": True,
            "source_item_count": len(value),
            "deterministic_preview_stride": step,
            "items": [
                _preview(row, depth=depth + 1, maximum_items=maximum_items)
                for row in sampled
            ],
        }
    return value


def _key_metrics(report: Mapping[str, object]) -> List[Dict[str, object]]:
    preferred = re.compile(
        r"(count|fraction|occupancy|silhouette|score|rms[fd]|sasa|memory|cpu|"
        r"wall|frame|observation|cluster|basin|state|ion|coordination)",
        flags=re.IGNORECASE,
    )
    metrics: List[Dict[str, object]] = []

    def visit(value: object, path: Sequence[str], depth: int) -> None:
        if len(metrics) >= 24 or depth > 3:
            return
        if _finite_number(value) and path and preferred.search(path[-1]):
            metrics.append({"label": ".".join(path), "value": value})
            return
        if isinstance(value, dict):
            for key in sorted(value, key=str):
                if str(key) in {
                    "assignments", "frame_assignments", "grid", "matrix",
                    "projections", "coordinates", "atom_statistics",
                }:
                    continue
                visit(value[key], [*path, str(key)], depth + 1)

    visit(report, [], 0)
    return metrics


def _fes_visuals(report: Mapping[str, object]) -> List[Dict[str, object]]:
    rows = report.get("smoothing_landscapes")
    visuals: List[Dict[str, object]] = []
    basis = report.get("pca_basis")
    x_component = basis.get("x_component", 1) if isinstance(basis, dict) else 1
    y_component = basis.get("y_component", 2) if isinstance(basis, dict) else 2
    if not isinstance(rows, list):
        landscape = report.get("landscape")
        if isinstance(landscape, dict):
            rows = [{
                "smoothing_sigma_bins": report.get("primary_smoothing_sigma_bins"),
                "landscape": landscape,
                "per_system_landscapes": report.get("per_system_landscapes", []),
            }]
        else:
            return visuals
    for smoothing in rows:
        if not isinstance(smoothing, dict):
            continue
        sigma = smoothing.get("smoothing_sigma_bins")
        pooled = smoothing.get("landscape")
        if isinstance(pooled, dict) and isinstance(pooled.get("grid"), list):
            visuals.append({
                "kind": "fes",
                "title": f"Pooled FES / occupancy surface; smoothing sigma {sigma} bins",
                "system_id": "pooled",
                "smoothing_sigma_bins": sigma,
                "landscape": pooled,
                "x_component": x_component,
                "y_component": y_component,
            })
        systems = smoothing.get("per_system_landscapes")
        complete_systems = [
            system for system in systems
            if (
                isinstance(system, dict)
                and system.get("technical_status") == "complete"
                and isinstance(system.get("landscape"), dict)
            )
        ] if isinstance(systems, list) else []
        # For one system, the pooled and per-system surfaces are the same
        # observation set. Keep the pooled view only; comparisons retain every
        # system-specific surface alongside the common pooled surface.
        if len(complete_systems) > 1:
            for system in complete_systems:
                if (
                    isinstance(system, dict)
                    and isinstance(system.get("landscape"), dict)
                ):
                    visuals.append({
                        "kind": "fes",
                        "title": (
                            f"{system.get('system_id')} FES / occupancy surface; "
                            f"smoothing sigma {sigma} bins"
                        ),
                        "system_id": str(system.get("system_id")),
                        "smoothing_sigma_bins": sigma,
                        "landscape": system["landscape"],
                        "x_component": x_component,
                        "y_component": y_component,
                    })
    return visuals


def _cluster_visual(
    *,
    method_id: str,
    model: Mapping[str, object],
    population_comparison: object,
) -> Dict[str, object] | None:
    sizes = model.get(
        "full_cluster_sizes",
        model.get("cluster_sizes", model.get("selected_cluster_sizes")),
    )
    if not isinstance(sizes, list) or not all(_finite_number(value) for value in sizes):
        return None
    silhouette = model.get("silhouette")
    if silhouette is None and isinstance(model.get("silhouette_evaluation"), dict):
        silhouette = model["silhouette_evaluation"].get("score")
    system_populations = []
    if isinstance(population_comparison, dict):
        rows = population_comparison.get("system_populations")
        if isinstance(rows, list):
            system_populations = [row for row in rows if isinstance(row, dict)]
    return {
        "kind": "cluster_populations",
        "title": _algorithm_label(method_id),
        "method_id": method_id,
        "method_name": _algorithm_label(method_id),
        "cluster_sizes": sizes,
        "silhouette": silhouette,
        "system_populations": system_populations,
        "model": {
            key: model.get(key)
            for key in (
                "k", "seed", "iteration_count", "inertia", "silhouette",
                "mean_adjusted_rand_to_best", "assigned_observation_count",
                "noise_observation_count",
            )
            if key in model
        },
    }


def _clustering_visuals(
    module_id: str, report: Mapping[str, object]
) -> List[Dict[str, object]]:
    if module_id == "alternative_clustering":
        visuals = []
        rows = report.get("algorithm_results")
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            method_id = str(
                row.get("algorithm_id", row.get("algorithm", row.get("method", "clustering")))
            )
            visual = _cluster_visual(
                method_id=method_id,
                model=row,
                population_comparison=row.get("state_population_comparison"),
            )
            if visual is not None:
                visuals.append(visual)
        return visuals
    model = report.get("selected_model")
    if not isinstance(model, dict):
        return []
    visual = _cluster_visual(
        method_id=module_id,
        model=model,
        population_comparison=report.get("state_population_comparison"),
    )
    return [visual] if visual is not None else []


def _rmsf_visuals(report: Mapping[str, object]) -> List[Dict[str, object]]:
    systems = report.get("systems")
    if not isinstance(systems, list):
        return []
    visuals = []
    for system in systems:
        if not isinstance(system, dict) or not isinstance(system.get("atom_statistics"), list):
            continue
        residues: Dict[tuple[str, int, str, str], List[float]] = {}
        for atom in system["atom_statistics"]:
            if not isinstance(atom, dict):
                continue
            value = atom.get("frame_pooled_rmsf_angstrom", atom.get("rmsf_angstrom"))
            number = atom.get("residue_number")
            if not _finite_number(value) or isinstance(number, bool) or not isinstance(number, int):
                continue
            key = (
                str(atom.get("chain_id", "")), number,
                str(atom.get("insertion_code", "")),
                str(atom.get("residue_name", "UNK")),
            )
            residues.setdefault(key, []).append(float(value))
        rows = [
            {
                "chain_id": key[0], "residue_number": key[1],
                "insertion_code": key[2], "residue_name": key[3],
                "mean_rmsf_angstrom": sum(values) / len(values),
            }
            for key, values in sorted(residues.items())
        ]
        if rows:
            visuals.append({
                "kind": "rmsf",
                "title": f"Residue-mean RMSF: {system.get('system_id')}",
                "system_id": str(system.get("system_id")),
                "residues": rows,
            })
    return visuals


def _dccm_visuals(report: Mapping[str, object], maximum_atoms: int = 180) -> List[Dict[str, object]]:
    atoms = report.get("analysis_atoms")
    systems = report.get("systems")
    if not isinstance(atoms, list) or not isinstance(systems, list) or not atoms:
        return []
    stride = max(1, math.ceil(len(atoms) / maximum_atoms))
    indices = list(range(0, len(atoms), stride))[:maximum_atoms]
    labels = []
    for index in indices:
        atom = atoms[index]
        if isinstance(atom, dict):
            labels.append(
                f"{atom.get('chain_id', '_')}:{atom.get('residue_name', 'UNK')}"
                f"{atom.get('residue_number', '?')}:{atom.get('atom_name', '?')}"
            )
        else:
            labels.append(str(index))
    visuals = []
    for system in systems:
        if not isinstance(system, dict):
            continue
        payload = system.get("frame_pooled_dccm")
        matrix = payload.get("matrix") if isinstance(payload, dict) else None
        if not isinstance(matrix, list) or len(matrix) < len(atoms):
            continue
        reduced = []
        valid = True
        for left in indices:
            row = matrix[left]
            if not isinstance(row, list) or len(row) < len(atoms):
                valid = False
                break
            reduced.append([
                float(row[right]) if _finite_number(row[right]) else None
                for right in indices
            ])
        if valid:
            visuals.append({
                "kind": "dccm",
                "title": f"DCCM: {system.get('system_id')}",
                "system_id": str(system.get("system_id")),
                "matrix": reduced,
                "labels": labels,
                "source_atom_count": len(atoms),
                "display_stride": stride,
            })
    return visuals


def _module_visuals(module_id: str, report: Mapping[str, object]) -> List[Dict[str, object]]:
    if module_id == "pca_fes_basins":
        return _fes_visuals(report)
    if module_id in {
        "clustering_kmeans", "clustering_imwkmeans", "clustering_hdbscan",
        "alternative_clustering",
    }:
        return _clustering_visuals(module_id, report)
    if module_id == "pooled_rmsf":
        return _rmsf_visuals(report)
    if module_id == "dccm":
        return _dccm_visuals(report)
    return []


def _stream_scalar(value: object) -> object:
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    try:
        return float(value)  # ijson may return Decimal with some backends.
    except (TypeError, ValueError):
        return str(value)


def _stream_large_fes_visuals(path: Path) -> tuple[List[Dict[str, object]], bool]:
    """Read FES display fields without materializing assignments from a huge report."""

    try:
        import ijson  # type: ignore[import-not-found]
    except ImportError:
        return [], False

    compact: Dict[str, object] = {"module_id": "pca_fes_basins", "pca_basis": {}}
    smoothing_rows: List[Dict[str, object]] = []
    current_smoothing: Dict[str, object] | None = None
    current_system: Dict[str, object] | None = None
    current_grid: Dict[str, object] | None = None
    current_basin: Dict[str, object] | None = None
    current_target: Dict[str, object] | None = None
    streamed_rows = 0
    truncated = False
    smoothing_prefix = "smoothing_landscapes.item"
    system_prefix = smoothing_prefix + ".per_system_landscapes.item"
    pooled_landscape_prefix = smoothing_prefix + ".landscape"
    system_landscape_prefix = system_prefix + ".landscape"

    with path.open("rb") as handle:
        for prefix, event, value in ijson.parse(handle, use_float=True):
            scalar = event in {"string", "number", "boolean", "null"}
            if scalar and prefix in {"pca_basis.x_component", "pca_basis.y_component"}:
                compact["pca_basis"][prefix.rsplit(".", 1)[1]] = _stream_scalar(value)
            elif event == "start_map" and prefix == smoothing_prefix:
                current_smoothing = {
                    "landscape": {"bounds": {}, "grid": [], "basins": []},
                    "per_system_landscapes": [],
                }
            elif scalar and current_smoothing is not None and prefix == (
                smoothing_prefix + ".smoothing_sigma_bins"
            ):
                current_smoothing["smoothing_sigma_bins"] = _stream_scalar(value)
            elif event == "start_map" and prefix == system_prefix:
                current_system = {
                    "landscape": {"bounds": {}, "grid": [], "basins": []},
                }
            elif scalar and current_system is not None and prefix in {
                system_prefix + ".system_id", system_prefix + ".technical_status",
            }:
                current_system[prefix.rsplit(".", 1)[1]] = _stream_scalar(value)
            elif event == "end_map" and prefix == system_prefix:
                if current_smoothing is not None and current_system is not None:
                    current_system.setdefault("technical_status", "complete")
                    current_smoothing["per_system_landscapes"].append(current_system)
                current_system = None
            elif event == "end_map" and prefix == smoothing_prefix:
                if current_smoothing is not None:
                    smoothing_rows.append(current_smoothing)
                current_smoothing = None
            elif current_smoothing is not None:
                if prefix.startswith(system_landscape_prefix) and current_system is not None:
                    current_target = current_system["landscape"]
                    landscape_prefix = system_landscape_prefix
                elif prefix.startswith(pooled_landscape_prefix):
                    current_target = current_smoothing["landscape"]
                    landscape_prefix = pooled_landscape_prefix
                else:
                    continue
                bounds_prefix = landscape_prefix + ".bounds."
                grid_prefix = landscape_prefix + ".grid.item"
                basin_prefix = landscape_prefix + ".basins.item"
                if scalar and prefix.startswith(bounds_prefix) and "." not in prefix[len(bounds_prefix):]:
                    current_target["bounds"][prefix[len(bounds_prefix):]] = _stream_scalar(value)
                elif event == "start_map" and prefix == grid_prefix:
                    current_grid = {}
                elif scalar and current_grid is not None and prefix.startswith(grid_prefix + ".") and "." not in prefix[len(grid_prefix) + 1:]:
                    current_grid[prefix.rsplit(".", 1)[1]] = _stream_scalar(value)
                elif event == "end_map" and prefix == grid_prefix:
                    if streamed_rows < _MAXIMUM_STREAMED_VISUAL_ROWS:
                        current_target["grid"].append(current_grid or {})
                        streamed_rows += 1
                    else:
                        truncated = True
                    current_grid = None
                elif event == "start_map" and prefix == basin_prefix:
                    current_basin = {}
                elif scalar and current_basin is not None and prefix.startswith(basin_prefix + ".") and "." not in prefix[len(basin_prefix) + 1:]:
                    current_basin[prefix.rsplit(".", 1)[1]] = _stream_scalar(value)
                elif event == "end_map" and prefix == basin_prefix:
                    current_target["basins"].append(current_basin or {})
                    current_basin = None
    compact["smoothing_landscapes"] = smoothing_rows
    return _fes_visuals(compact), truncated


def _stream_large_clustering_visuals(
    path: Path, module_id: str
) -> tuple[List[Dict[str, object]], bool]:
    """Read clustering scores and populations while skipping centers and assignments."""

    try:
        import ijson  # type: ignore[import-not-found]
    except ImportError:
        return [], False

    compact: Dict[str, object] = {"module_id": module_id}
    selected: Dict[str, object] = {}
    selected_populations: List[Dict[str, object]] = []
    algorithms: List[Dict[str, object]] = []
    current_algorithm: Dict[str, object] | None = None
    current_system: Dict[str, object] | None = None
    current_state: Dict[str, object] | None = None
    current_population_owner: Dict[str, object] | None = None
    current_sizes: List[object] | None = None
    current_sizes_key: str | None = None

    selected_prefix = "selected_model"
    algorithm_prefix = "algorithm_results.item"
    selected_system_prefix = "state_population_comparison.system_populations.item"
    algorithm_system_prefix = algorithm_prefix + ".state_population_comparison.system_populations.item"
    direct_fields = {
        "algorithm", "requested_algorithm", "k", "seed", "iteration_count",
        "inertia", "silhouette", "mean_adjusted_rand_to_best",
        "assigned_observation_count", "noise_observation_count",
    }

    with path.open("rb") as handle:
        for prefix, event, value in ijson.parse(handle, use_float=True):
            scalar = event in {"string", "number", "boolean", "null"}
            if event == "start_map" and prefix == algorithm_prefix:
                current_algorithm = {}
            elif event == "end_map" and prefix == algorithm_prefix:
                if current_algorithm is not None:
                    algorithms.append(current_algorithm)
                current_algorithm = None
            elif scalar and prefix.startswith(selected_prefix + "."):
                field = prefix[len(selected_prefix) + 1:]
                if "." not in field and field in direct_fields:
                    selected[field] = _stream_scalar(value)
                elif field == "silhouette_evaluation.score" and "silhouette" not in selected:
                    selected["silhouette"] = _stream_scalar(value)
            elif scalar and current_algorithm is not None and prefix.startswith(algorithm_prefix + "."):
                field = prefix[len(algorithm_prefix) + 1:]
                if "." not in field and field in direct_fields:
                    current_algorithm[field] = _stream_scalar(value)
                elif field == "silhouette_evaluation.score" and "silhouette" not in current_algorithm:
                    current_algorithm["silhouette"] = _stream_scalar(value)

            if event == "start_array" and prefix in {
                selected_prefix + ".cluster_sizes", selected_prefix + ".full_cluster_sizes",
                algorithm_prefix + ".cluster_sizes", algorithm_prefix + ".full_cluster_sizes",
            }:
                current_sizes = []
                current_sizes_key = prefix.rsplit(".", 1)[1]
            elif scalar and current_sizes is not None and prefix.endswith(".item"):
                current_sizes.append(_stream_scalar(value))
            elif event == "end_array" and current_sizes is not None and current_sizes_key is not None:
                if prefix in {
                    selected_prefix + ".cluster_sizes", selected_prefix + ".full_cluster_sizes",
                }:
                    selected[current_sizes_key] = current_sizes
                    current_sizes = None
                    current_sizes_key = None
                elif prefix in {
                    algorithm_prefix + ".cluster_sizes", algorithm_prefix + ".full_cluster_sizes",
                }:
                    if current_algorithm is not None:
                        current_algorithm[current_sizes_key] = current_sizes
                    current_sizes = None
                    current_sizes_key = None

            if event == "start_map" and prefix in {selected_system_prefix, algorithm_system_prefix}:
                current_system = {"state_populations": []}
                current_population_owner = (
                    selected if prefix == selected_system_prefix else current_algorithm
                )
            elif scalar and current_system is not None and prefix.rsplit(".", 1)[0] in {
                selected_system_prefix, algorithm_system_prefix,
            }:
                current_system[prefix.rsplit(".", 1)[1]] = _stream_scalar(value)
            elif event == "start_map" and prefix in {
                selected_system_prefix + ".state_populations.item",
                algorithm_system_prefix + ".state_populations.item",
            }:
                current_state = {}
            elif scalar and current_state is not None and prefix.rsplit(".", 1)[0] in {
                selected_system_prefix + ".state_populations.item",
                algorithm_system_prefix + ".state_populations.item",
            }:
                current_state[prefix.rsplit(".", 1)[1]] = _stream_scalar(value)
            elif event == "end_map" and current_state is not None and prefix in {
                selected_system_prefix + ".state_populations.item",
                algorithm_system_prefix + ".state_populations.item",
            }:
                if current_system is not None:
                    current_system["state_populations"].append(current_state)
                current_state = None
            elif event == "end_map" and current_system is not None and prefix in {
                selected_system_prefix, algorithm_system_prefix,
            }:
                if current_population_owner is selected:
                    selected_populations.append(current_system)
                elif current_population_owner is not None:
                    comparison = current_population_owner.setdefault(
                        "state_population_comparison", {"system_populations": []}
                    )
                    comparison["system_populations"].append(current_system)
                current_system = None
                current_population_owner = None

    if module_id == "alternative_clustering":
        compact["algorithm_results"] = algorithms
    else:
        compact["selected_model"] = selected
        compact["state_population_comparison"] = {
            "system_populations": selected_populations,
        }
    return _clustering_visuals(module_id, compact), False


def _stream_large_report_visuals(
    path: Path, module_id: str
) -> tuple[List[Dict[str, object]], bool]:
    if module_id == "pca_fes_basins":
        return _stream_large_fes_visuals(path)
    if module_id in {
        "alternative_clustering", "clustering_hdbscan", "clustering_imwkmeans",
        "clustering_kmeans",
    }:
        return _stream_large_clustering_visuals(path, module_id)
    return [], False


def _report_record(path: Path, root: Path) -> Dict[str, object]:
    size_bytes = path.stat().st_size
    relative = _relative(path, root)
    context = _display_context(relative)
    portable_full_report = size_bytes <= _MAXIMUM_PORTABLE_REPORT_BYTES
    evidence_relative = (
        relative if portable_full_report else relative + ".interactive-summary.json"
    )
    if size_bytes > _MAXIMUM_REPORT_PARSE_BYTES:
        sidecar_path = Path(str(path) + ".summary.json")
        sidecar = _optional_json(sidecar_path)
        if not isinstance(sidecar, dict):
            sidecar = {}
        module_id = str(
            sidecar.get("module_id", _module_from_path(relative, path.parent.name))
        )
        module_id = _module_from_path(relative, module_id)
        visuals, visual_rows_truncated = _stream_large_report_visuals(path, module_id)
        preview_issue = {
            "severity": "info",
            "code": "INTERACTIVE_REPORT_PREVIEW_OMITTED",
            "message": (
                "The source report exceeds the bounded full-report parser. "
                "The browser keeps its hash and a compact evidence index."
            ),
        }
        issues = [preview_issue]
        if not visuals and module_id in {
            "pca_fes_basins", "alternative_clustering", "clustering_hdbscan",
            "clustering_imwkmeans", "clustering_kmeans",
        }:
            issues.append({
                "severity": "warning",
                "code": "INTERACTIVE_STREAMING_READER_UNAVAILABLE",
                "message": (
                    "This large state report needs the ijson dependency for bounded "
                    "FES or clustering visualization. Its compact index remains available."
                ),
            })
        if visual_rows_truncated:
            issues.append({
                "severity": "warning",
                "code": "INTERACTIVE_VISUAL_ROW_LIMIT",
                "message": (
                    "The bounded streaming reader reached its visualization-row limit."
                ),
            })
        class_id, class_title = _analysis_class(module_id)
        return {
            "module_id": module_id,
            "title": _module_label(module_id),
            "context": context,
            "analysis_class_id": class_id,
            "analysis_class_title": class_title,
            "technical_status": str(sidecar.get("technical_status", "unknown")),
            "path": relative,
            "href": _portable_href(evidence_relative),
            "evidence_kind": "compact_index",
            "size_bytes": size_bytes,
            "sha256": _sha256_file(path),
            "issues": issues,
            "limitations": [],
            "key_metrics": _key_metrics(sidecar),
            "visuals": visuals,
            "preview": _preview(sidecar),
        }
    report = _load_json(path)
    if not isinstance(report, dict):
        raise InteractiveReportError(f"module report is not a JSON object: {path}")
    module_id = str(report.get("module_id", path.parent.name))
    class_id, class_title = _analysis_class(module_id)
    issues = [row for row in report.get("issues", []) if isinstance(row, dict)]
    limitations = [
        str(row) for row in report.get("limitations", []) if isinstance(row, str)
    ]
    return {
        "module_id": module_id,
        "title": _module_label(module_id),
        "context": context,
        "analysis_class_id": class_id,
        "analysis_class_title": class_title,
        "technical_status": str(report.get("technical_status", "unknown")),
        "path": relative,
        "href": _portable_href(evidence_relative),
        "evidence_kind": "complete_json" if portable_full_report else "compact_index",
        "size_bytes": size_bytes,
        "sha256": _sha256_file(path),
        "issues": issues,
        "limitations": limitations,
        "key_metrics": _key_metrics(report),
        "visuals": _module_visuals(module_id, report),
        "preview": _preview(report),
    }


def _structure_records(
    root: Path,
    *,
    maximum_structures: int,
    maximum_total_bytes: int,
) -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    candidates = sorted({
        *root.glob("results/**/*.pdb"),
        *root.glob("results/**/*.ent"),
        *root.glob("*.rmsf_bfactor.pdb"),
    })
    included: List[Dict[str, object]] = []
    omitted: List[Dict[str, object]] = []
    total_bytes = 0
    for path in candidates:
        relative = _relative(path, root)
        source_text = path.read_text(encoding="utf-8", errors="replace")
        source_lines = source_text.splitlines(keepends=True)
        kept_atom_serials = set()
        removed_atom_serials = set()
        removed_solvent_atoms = 0
        atom_count = 0
        for line in source_lines:
            record_name = line[:6].strip()
            if record_name in {"ATOM", "HETATM"}:
                residue_name = line[17:20].strip().upper()
                serial_text = line[6:11].strip()
                serial = int(serial_text) if serial_text.isdigit() else None
                if residue_name in _SOLVENT_RESIDUES:
                    removed_solvent_atoms += 1
                    if serial is not None:
                        removed_atom_serials.add(serial)
                    continue
                atom_count += 1
                if serial is not None:
                    kept_atom_serials.add(serial)
        kept_lines = []
        for line in source_lines:
            record_name = line[:6].strip()
            if record_name in {"ATOM", "HETATM"}:
                residue_name = line[17:20].strip().upper()
                if residue_name in _SOLVENT_RESIDUES:
                    continue
            elif record_name == "CONECT":
                serials = [
                    int(value) for value in line[6:].split() if value.isdigit()
                ]
                if not serials or serials[0] not in kept_atom_serials:
                    continue
                retained_neighbors = [
                    value for value in serials[1:]
                    if value in kept_atom_serials and value not in removed_atom_serials
                ]
                if not retained_neighbors:
                    continue
                newline = "\n" if line.endswith("\n") else ""
                line = "CONECT" + "".join(
                    f"{value:5d}" for value in [serials[0], *retained_neighbors]
                ) + newline
            kept_lines.append(line)
        pdb_text = "".join(kept_lines)
        size = len(pdb_text.encode("utf-8"))
        relative_parts = Path(relative).parts
        state_part = next(
            (part for part in relative_parts if re.fullmatch(r"state-\d+", part)),
            None,
        )
        state_index = relative_parts.index(state_part) if state_part else -1
        method_part = relative_parts[state_index - 1] if state_index > 0 else None
        method_token = str(method_part or "").lower().replace("_", "-")
        sigma_match = re.search(r"(?:^|-)sigma([0-9]+(?:[p.]?[0-9]+)?)", method_token)
        export_sigma = None
        if sigma_match:
            try:
                export_sigma = float(sigma_match.group(1).replace("p", "."))
            except ValueError:
                export_sigma = None
        if "fes" in method_token or "basin" in method_token:
            method_id = "pca_fes_basins"
        elif "imwkmeans" in method_token or "minkowski" in method_token:
            method_id = "clustering_imwkmeans"
        elif "kmeans" in method_token or "cluster" in method_token:
            method_id = "clustering_kmeans"
        else:
            method_id = _module_from_path(relative, str(method_part or "other"))
        system_part = next(
            (part[7:] for part in relative_parts if part.startswith("system-")),
            None,
        )
        display_name = path.stem
        if state_part:
            state_label = state_part.replace("-", " ").title()
            method_label = (
                _module_label(method_id) if method_id else "State"
            )
            display_name = f"{method_label} · {state_label}"
        record = {
            "structure_id": f"structure-{len(included) + len(omitted) + 1:05d}",
            "name": display_name,
            "path": relative,
            "href": _portable_href(relative),
            "size_bytes": size,
            "source_sha256": _sha256_file(path),
            "sha256": hashlib.sha256(pdb_text.encode("utf-8")).hexdigest(),
            "atom_count": atom_count,
            "removed_solvent_atom_count": removed_solvent_atoms,
            "state_id": state_part,
            "system_id": system_part,
            "method_id": method_id,
            "module_id": method_id,
            "export_id": method_part,
            "fes_smoothing_sigma_bins": export_sigma,
        }
        if len(included) >= maximum_structures or total_bytes + size > maximum_total_bytes:
            omitted.append({**record, "reason": "interactive inline-asset limit"})
            continue
        record["pdb_text"] = pdb_text
        included.append(record)
        total_bytes += size
    return included, omitted


def _figure_records(
    root: Path, *, maximum_total_bytes: int
) -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    candidates = sorted({
        path
        for extension in _IMAGE_MEDIA_TYPES
        for path in root.glob(f"results/**/*{extension}")
    })
    included: List[Dict[str, object]] = []
    omitted: List[Dict[str, object]] = []
    total_bytes = 0
    for path in candidates:
        relative = _relative(path, root)
        size = path.stat().st_size
        module_id = _module_from_path(relative)
        class_id, class_title = _analysis_class(module_id)
        record = {
            "name": path.stem,
            "path": relative,
            "href": _portable_href(relative),
            "size_bytes": size,
            "sha256": _sha256_file(path),
            "media_type": _IMAGE_MEDIA_TYPES[path.suffix.lower()],
            "module_id": module_id,
            "analysis_class_id": class_id,
            "analysis_class_title": class_title,
        }
        if total_bytes + size > maximum_total_bytes:
            omitted.append({**record, "reason": "interactive inline-asset limit"})
            continue
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        record["data_uri"] = f"{record['media_type']};base64,{payload}"
        included.append(record)
        total_bytes += size
    return included, omitted


def _attach_visual_assets(
    reports: Sequence[Mapping[str, object]],
    structures: Sequence[Mapping[str, object]],
) -> None:
    """Attach portable representative structures to FES and clustering panels."""

    for report in reports:
        report_context = str(report.get("context", "Campaign"))
        visuals = report.get("visuals")
        if not isinstance(visuals, list):
            continue
        for visual in visuals:
            if not isinstance(visual, dict):
                continue
            visual["context"] = report_context
            method_id = str(visual.get("method_id", report.get("module_id", "")))
            target_system = str(visual.get("system_id", ""))
            visual_sigma = visual.get("smoothing_sigma_bins")
            related = []
            for structure in structures:
                if str(structure.get("method_id", "")) != method_id:
                    continue
                structure_sigma = structure.get("fes_smoothing_sigma_bins")
                if (
                    method_id == "pca_fes_basins"
                    and visual_sigma is not None
                    and structure_sigma is not None
                    and not math.isclose(
                        float(visual_sigma), float(structure_sigma), abs_tol=1e-9
                    )
                ):
                    continue
                structure_system = str(structure.get("system_id", ""))
                if target_system not in {"", "pooled"} and structure_system not in {
                    "", target_system,
                }:
                    continue
                related.append({
                    key: structure.get(key)
                    for key in (
                        "structure_id", "name", "href", "state_id", "system_id",
                        "method_id", "atom_count", "export_id",
                        "fes_smoothing_sigma_bins",
                    )
                })
            visual["representative_structures"] = related


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _portable_report_summary(report: Mapping[str, object]) -> Dict[str, object]:
    return {
        "interactive_evidence_schema": "salsbury-interactive-compact-evidence-v1",
        "module_id": report.get("module_id"),
        "module_name": report.get("title"),
        "context": report.get("context"),
        "technical_status": report.get("technical_status"),
        "source_report_path": report.get("path"),
        "source_report_sha256": report.get("sha256"),
        "source_report_size_bytes": report.get("size_bytes"),
        "issues": report.get("issues", []),
        "limitations": report.get("limitations", []),
        "key_metrics": report.get("key_metrics", []),
        "bounded_preview": report.get("preview"),
    }


def _write_portable_evidence(
    root: Path,
    target: Path,
    data: Mapping[str, object],
) -> List[Dict[str, object]]:
    """Package working JSON, PDB, and figure links beside the offline HTML."""

    records: List[Dict[str, object]] = []
    copied_report_bytes = 0
    reports = data.get("reports", [])
    for report in reports if isinstance(reports, list) else []:
        if not isinstance(report, dict):
            continue
        relative = str(report["path"])
        source = root / relative
        copy_complete = (
            source.stat().st_size <= _MAXIMUM_PORTABLE_REPORT_BYTES
            and copied_report_bytes + source.stat().st_size
            <= _MAXIMUM_PORTABLE_EVIDENCE_BYTES
        )
        if copy_complete:
            destination_relative = relative
            destination = target / _portable_href(destination_relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied_report_bytes += source.stat().st_size
            report["evidence_kind"] = "complete_json"
        else:
            destination_relative = relative + ".interactive-summary.json"
            destination = target / _portable_href(destination_relative)
            _write_json(destination, _portable_report_summary(report))
            report["evidence_kind"] = "compact_index"
        report["href"] = _portable_href(destination_relative)
        records.append({
            "path": _portable_href(destination_relative),
            "sha256": _sha256_file(destination),
            "size_bytes": destination.stat().st_size,
            "evidence_kind": report["evidence_kind"],
            "source_path": relative,
            "source_sha256": report.get("sha256"),
        })

    structures = data.get("structures", [])
    for structure in structures if isinstance(structures, list) else []:
        if not isinstance(structure, dict):
            continue
        destination = target / str(structure["href"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(str(structure["pdb_text"]), encoding="utf-8")
        records.append({
            "path": structure["href"],
            "sha256": _sha256_file(destination),
            "size_bytes": destination.stat().st_size,
            "evidence_kind": "all_atom_non_solvent_pdb",
            "source_path": structure["path"],
            "source_sha256": structure.get("source_sha256"),
        })

    figures = data.get("figures", [])
    for figure in figures if isinstance(figures, list) else []:
        if not isinstance(figure, dict):
            continue
        destination = target / str(figure["href"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / str(figure["path"]), destination)
        records.append({
            "path": figure["href"],
            "sha256": _sha256_file(destination),
            "size_bytes": destination.stat().st_size,
            "evidence_kind": "figure",
            "source_path": figure["path"],
            "source_sha256": figure.get("sha256"),
        })

    for relative in (
        "prioritized_findings.json", "analysis_resource_and_frame_table.json",
        "module-coverage.json", "analysis-config.json", "preflight.report.json",
        "sampling-plan.json", "automatic-chemical-context.json",
        "conformational-views.json", "project.json", "system.json",
    ):
        source = root / relative
        if not source.is_file():
            continue
        destination = target / _portable_href(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        records.append({
            "path": _portable_href(relative),
            "sha256": _sha256_file(destination),
            "size_bytes": destination.stat().st_size,
            "evidence_kind": "campaign_metadata",
            "source_path": relative,
            "source_sha256": _sha256_file(source),
        })
    return records


def _project_title(root: Path, project: object, system: object) -> str:
    for payload in (project, system):
        if isinstance(payload, dict):
            for key in ("project_id", "campaign_id", "system_id", "title"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return root.name


def _system_ids(system: object, project: object) -> List[str]:
    values = []
    for payload in (system, project):
        if not isinstance(payload, dict):
            continue
        systems = payload.get("systems")
        if isinstance(systems, list):
            for row in systems:
                if isinstance(row, dict) and isinstance(row.get("system_id"), str):
                    values.append(str(row["system_id"]))
        if isinstance(payload.get("system_id"), str):
            values.append(str(payload["system_id"]))
    return sorted(set(values))


def _resource_rows_with_sampling(
    rows: Sequence[Mapping[str, object]],
    sampling: object,
    views: object,
) -> List[Dict[str, object]]:
    """Attach explicit integer-stride context to measured resource rows."""

    direct_strides: Dict[str, int] = {}
    if isinstance(sampling, dict) and isinstance(sampling.get("method_plans"), list):
        for plan in sampling["method_plans"]:
            if not isinstance(plan, dict):
                continue
            module_id = plan.get("module_id")
            stride = plan.get("frame_stride")
            if isinstance(module_id, str) and isinstance(stride, int) and stride > 0:
                direct_strides[module_id] = stride

    view_strides: Dict[str, int] = {}
    if isinstance(views, dict) and isinstance(views.get("views"), list):
        for view in views["views"]:
            if not isinstance(view, dict):
                continue
            output_root = view.get("analysis_output_root")
            plan = view.get("resource_plan")
            selection = plan.get("basis_frame_selection") if isinstance(plan, dict) else None
            stride = selection.get("stride") if isinstance(selection, dict) else None
            if isinstance(output_root, str) and isinstance(stride, int) and stride > 0:
                view_strides[output_root.rstrip("/") + "/"] = stride

    annotated: List[Dict[str, object]] = []
    for source in rows:
        row = dict(source)
        module_id = str(row.get("module_id", ""))
        report_path = str(row.get("report_path", "")).replace(os.sep, "/")
        basis_stride = next(
            (
                stride for prefix, stride in view_strides.items()
                if report_path.startswith(prefix) or f"/{prefix}" in report_path
            ),
            None,
        )
        source_frames = row.get("source_physical_frames_available")
        selected_frames = row.get("selected_source_physical_frames")
        analysis_stride = direct_strides.get(module_id)
        if basis_stride is not None:
            row["basis_frame_stride"] = basis_stride
            if module_id == "common_pca":
                analysis_stride = basis_stride
        if analysis_stride is None and (
            isinstance(source_frames, int)
            and isinstance(selected_frames, int)
            and source_frames == selected_frames
        ):
            analysis_stride = 1
        if analysis_stride is not None:
            row["analysis_frame_stride"] = analysis_stride
        annotated.append(row)
    return annotated


def _collect_data(
    root: Path,
    *,
    title: str | None,
    maximum_inline_structures: int,
    maximum_inline_structure_bytes: int,
    maximum_inline_figure_bytes: int,
) -> tuple[Dict[str, object], List[Dict[str, object]]]:
    project = _optional_json(root / "project.json")
    system = _optional_json(root / "system.json")
    config = _optional_json(root / "analysis-config.json")
    preflight = _optional_json(root / "preflight.report.json")
    findings = _optional_json(root / "prioritized_findings.json")
    resources = _optional_json(root / "analysis_resource_and_frame_table.json")
    coverage = _optional_json(root / "module-coverage.json")
    chemistry = _optional_json(root / "automatic-chemical-context.json")
    views = _optional_json(root / "conformational-views.json")
    sampling = _optional_json(root / "sampling-plan.json")

    reports = [
        _report_record(path, root)
        for path in sorted((root / "results").glob("**/report.json"))
    ] if (root / "results").is_dir() else []
    structures, omitted_structures = _structure_records(
        root,
        maximum_structures=maximum_inline_structures,
        maximum_total_bytes=maximum_inline_structure_bytes,
    )
    figures, omitted_figures = _figure_records(
        root, maximum_total_bytes=maximum_inline_figure_bytes
    )
    _attach_visual_assets(reports, structures)
    qc_issues: List[Dict[str, object]] = []
    if isinstance(preflight, dict):
        qc_issues.extend(
            {**row, "source": "preflight.report.json"}
            for row in preflight.get("issues", []) if isinstance(row, dict)
        )
    for report in reports:
        if _is_qc_module(report["module_id"]):
            qc_issues.extend(
                {**row, "source": report["path"], "module_id": report["module_id"]}
                for row in report["issues"] if isinstance(row, dict)
            )
    severity_order = {"error": 0, "warning": 1, "info": 2}
    qc_issues.sort(key=lambda row: (
        severity_order.get(str(row.get("severity", "info")), 9),
        str(row.get("module_id", "")), str(row.get("code", "")),
    ))
    hidden_finding_fields = {"scientific_status", "evidence_level"}
    highlighted_finding_rows = (
        [
            {key: value for key, value in row.items() if key not in hidden_finding_fields}
            for row in findings.get("findings", []) if isinstance(row, dict)
        ]
        if isinstance(findings, dict) else []
    )
    finding_rows = (
        [
            {key: value for key, value in row.items() if key not in hidden_finding_fields}
            for row in findings.get("all_candidates", []) if isinstance(row, dict)
        ]
        if isinstance(findings, dict) else []
    ) or highlighted_finding_rows
    headline_rows = (
        [
            {key: value for key, value in row.items() if key not in hidden_finding_fields}
            for row in findings.get("headline_findings", []) if isinstance(row, dict)
        ]
        if isinstance(findings, dict) else []
    )
    secondary_rows = (
        [
            {key: value for key, value in row.items() if key not in hidden_finding_fields}
            for row in findings.get("secondary_findings", []) if isinstance(row, dict)
        ]
        if isinstance(findings, dict) else []
    )
    presentation_contract = (
        findings.get("presentation_contract", {})
        if isinstance(findings, dict) else {}
    )
    if not isinstance(presentation_contract, dict):
        presentation_contract = {}
    if not headline_rows:
        headline_count = min(
            int(findings.get("headline_count", min(12, len(highlighted_finding_rows))))
            if isinstance(findings, dict) else 0,
            len(highlighted_finding_rows),
        )
        headline_rows = highlighted_finding_rows[:headline_count]
        secondary_rows = highlighted_finding_rows[headline_count:]
    for index, row in enumerate(finding_rows):
        if row.get("presentation_tier"):
            continue
        row["presentation_tier"] = (
            "headline" if index < len(headline_rows) else
            "secondary" if index < len(highlighted_finding_rows) else
            "additional_candidate"
        )
    module_accounting = (
        [row for row in findings.get("module_accounting", []) if isinstance(row, dict)]
        if isinstance(findings, dict) else []
    )
    all_picker_qc_records = (
        [row for row in findings.get("quality_control_records", []) if isinstance(row, dict)]
        if isinstance(findings, dict) else []
    )
    picker_qc_records = [
        row for row in all_picker_qc_records if _is_qc_module(row.get("module_id"))
    ]
    analysis_review_records = [
        row for row in all_picker_qc_records if not _is_qc_module(row.get("module_id"))
    ]
    for report in reports:
        report["review_notes"] = [
            row for row in analysis_review_records
            if str(row.get("module_id", "")) == str(report.get("module_id", ""))
        ]
    raw_resource_rows = (
        [row for row in resources.get("rows", []) if isinstance(row, dict)]
        if isinstance(resources, dict) else []
    )
    resource_rows = _resource_rows_with_sampling(raw_resource_rows, sampling, views)
    status_counts: Dict[str, int] = {}
    for report in reports:
        key = str(report["technical_status"])
        status_counts[key] = status_counts.get(key, 0) + 1

    source_records = [
        {
            "path": report["path"],
            "size_bytes": report["size_bytes"],
            "sha256": report["sha256"],
        }
        for report in reports
    ]
    analysis_classes_by_id: Dict[str, str] = {}
    for report in reports:
        class_id = str(report.get("analysis_class_id", "other"))
        if class_id == "qc":
            continue
        analysis_classes_by_id[class_id] = str(
            report.get("analysis_class_title", "Other analyses")
        )
    preferred_class_order = [
        "free-energy", "clustering", "rmsd-rg", "rmsf", "sasa",
        "distributions", "hydrogen-bonds", "hydration", "ions", "dna",
        "local-structure", "correlations", "pockets", "kinetics",
        "convergence", "comparisons", "preparation", "other",
    ]
    analysis_classes = [
        {"class_id": class_id, "title": analysis_classes_by_id[class_id]}
        for class_id in preferred_class_order if class_id in analysis_classes_by_id
    ]
    data = {
        "interactive_report_schema": "salsbury-interactive-results-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "title": title or _project_title(root, project, system),
        "technical_status": (
            "attention_required" if status_counts.get("failed", 0) else "complete"
        ),
        "scientific_boundary": (
            "Technical completion and automated ranking do not establish convergence, "
            "mechanism, causality, biological importance, or scientific validity."
        ),
        "system_ids": _system_ids(system, project),
        "status_counts": status_counts,
        "findings": finding_rows,
        "highlighted_findings": highlighted_finding_rows,
        "headline_findings": headline_rows,
        "secondary_findings": secondary_rows,
        "presentation_contract": presentation_contract,
        "finding_metadata": {
            key: findings.get(key)
            for key in (
                "candidate_count", "reported_count", "headline_count",
                "secondary_count", "searchable_candidate_count",
                "additional_candidate_count", "silent_omission_count",
            )
            if isinstance(findings, dict) and key in findings
        },
        "module_accounting": module_accounting,
        "picker_qc_records": picker_qc_records,
        "analysis_review_records": analysis_review_records,
        "analysis_classes": analysis_classes,
        "display_terms": {
            **_MODULE_LABELS,
            **_ALGORITHM_LABELS,
            "global_common_heavy": "Whole complex",
            "macromolecular_trace": "Polymer backbone",
            "protein_dna_interface": "Protein–DNA interface",
            "oligomer_member_pooled": "Pooled oligomer members",
            "member_pooled": "Pooled oligomer members",
            "protein_only_heavy": "Protein",
            "dna_only_heavy": "DNA",
            "interface_heavy": "Molecular interface",
            "frame_pooled_dccm": "frame-pooled correlation network",
            "difference_from_reference_dccm": "difference-from-reference correlation network",
            "descriptive": "observational",
        },
        "reports": reports,
        "resources": resource_rows,
        "resource_metadata": _preview(resources) if isinstance(resources, dict) else None,
        "qc_issues": qc_issues,
        "structures": structures,
        "omitted_structures": omitted_structures,
        "figures": figures,
        "omitted_figures": omitted_figures,
        "module_coverage": _preview(coverage),
        "chemical_context": _preview(chemistry),
        "conformational_views": _preview(views),
        "sampling_plan": _preview(sampling),
        "configuration": _preview(config),
        "project_manifest": _preview(project),
        "system_manifest": _preview(system),
        "preflight": _preview(preflight),
        "raw_links": {
            label: _portable_href(relative)
            for label, relative in {
                "Prioritized findings": "prioritized_findings.json",
                "Resource and frame table": "analysis_resource_and_frame_table.json",
                "Module coverage": "module-coverage.json",
                "Resolved configuration": "analysis-config.json",
                "Preflight report": "preflight.report.json",
                "Sampling plan": "sampling-plan.json",
            }.items()
            if (root / relative).is_file()
        },
    }
    return data, source_records


_CSS = r"""
:root{--ink:#18211d;--muted:#617069;--paper:#f7f5ef;--card:#fff;--line:#d9ddd7;--forest:#173f35;--teal:#1c7166;--gold:#d69b35;--red:#a43d32;--blue:#3767a6;--shadow:0 10px 35px rgba(25,44,36,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select{font:inherit}a{color:var(--teal)}
.shell{display:grid;grid-template-columns:270px minmax(0,1fr);min-height:100vh}.sidebar{background:var(--forest);color:#eef5f1;padding:25px 18px;position:sticky;top:0;height:100vh;overflow:auto}.brand{font:700 22px/1.1 ui-serif,Georgia,serif;margin:0 8px 8px}.subtitle{color:#b9cbc4;font-size:12px;margin:0 8px 25px}.nav button{display:block;width:100%;border:0;background:transparent;color:#dceae4;text-align:left;padding:9px 12px;border-radius:10px;margin:2px 0;cursor:pointer}.nav button.active,.nav button:hover{background:#285b4e;color:#fff}.nav-heading{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:#91ada2;margin:18px 12px 6px}
.main{padding:32px clamp(20px,4vw,64px);max-width:1600px}.topline{display:flex;gap:15px;align-items:flex-start;justify-content:space-between;margin-bottom:22px}.topline h1{font:700 clamp(28px,4vw,46px)/1.05 ui-serif,Georgia,serif;margin:0}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:var(--teal);font-size:12px;font-weight:800}.status{border-radius:999px;padding:7px 12px;background:#e4efe9;color:var(--forest);font-weight:700;white-space:nowrap}.status.failed,.severity-error{background:#fae5e2;color:var(--red)}.status.warning,.severity-warning{background:#fff1d7;color:#875c0b}
.view{display:none}.view.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0 24px}.stat,.card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow)}.stat{padding:16px}.stat strong{font-size:26px;display:block}.stat span{font-size:12px;color:var(--muted)}.card{padding:20px;margin-bottom:18px}.card h2,.card h3{font-family:ui-serif,Georgia,serif;margin-top:0}.card h2{font-size:25px}.card h3{font-size:19px}.muted{color:var(--muted)}.boundary-banner{border-left:5px solid var(--gold);background:#fff8e9;padding:14px 18px;border-radius:10px;margin:18px 0}
.finding{display:grid;grid-template-columns:42px minmax(0,1fr);gap:12px;padding:15px 0;border-bottom:1px solid var(--line)}.finding:last-child{border:0}.rank{width:36px;height:36px;border-radius:50%;background:#e6f0ec;color:var(--forest);display:grid;place-items:center;font-weight:800}.badges{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.badge{font-size:11px;border-radius:999px;padding:3px 8px;background:#edf0ee;color:#46534d}.badge.sig{background:#dcebd8;color:#2f642a}.finding-footer,.structure-links{display:flex;align-items:center;gap:9px;flex-wrap:wrap;color:var(--muted);font-size:11px;margin-top:8px}.inline-link{border:1px solid #adc6bc;background:#f3f8f6;color:var(--teal);border-radius:7px;padding:4px 8px;cursor:pointer}.inline-link:hover{background:#e4f0eb}.filters{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 20px}.filters input,.filters select{border:1px solid var(--line);background:#fff;border-radius:9px;padding:9px 11px;min-width:180px}
.issue{padding:12px 14px;border-left:4px solid var(--line);background:#fafafa;margin:9px 0;border-radius:7px}.issue.error{border-color:var(--red)}.issue.warning{border-color:var(--gold)}.issue code{font-size:11px}.module-row{border-bottom:1px solid var(--line);padding:12px 0}.module-row summary{cursor:pointer;font-weight:700;display:flex;justify-content:space-between;gap:12px}.metric-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:7px;margin:12px 0}.metric{background:#f4f6f3;padding:8px 10px;border-radius:7px;font-size:12px}.json{background:#17231e;color:#dce9e2;padding:14px;border-radius:9px;overflow:auto;max-height:460px;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
.chart{width:100%;min-height:300px;border:1px solid var(--line);border-radius:12px;background:#fff}.chart svg,.chart canvas{display:block;width:100%;height:auto}.chart-note{font-size:12px;color:var(--muted);margin-top:8px}.visual-controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}.visual-controls select{padding:7px;border:1px solid var(--line);border-radius:8px;background:white}
.representative-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,220px));gap:10px;width:100%}.representative-card{padding:0;border:1px solid var(--line);background:#fff;border-radius:10px;overflow:hidden;text-align:left;color:var(--ink);cursor:pointer}.representative-card:hover{border-color:var(--teal);box-shadow:0 4px 14px rgba(25,44,36,.12)}.representative-card canvas{display:block;width:100%;height:auto}.representative-card span{display:block;padding:7px 9px;font-size:11px}
.molecule-layout{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(250px,.7fr);gap:16px}.viewer{background:#0e1714;border-radius:15px;overflow:hidden;position:relative;min-height:520px}.molecule-viewer{width:100%;height:520px;position:relative}.molecule-viewer canvas{cursor:grab}.molecule-viewer canvas:active{cursor:grabbing}.viewer-tools{display:flex;gap:7px;flex-wrap:wrap;padding:10px;background:#17231e}.viewer-tools select,.viewer-tools input,.viewer-tools button{background:#f5f8f6;border:0;border-radius:7px;padding:7px}.viewer-info{position:absolute;left:12px;bottom:12px;background:rgba(0,0,0,.68);color:#fff;padding:8px 10px;border-radius:7px;font-size:12px;max-width:85%;z-index:5;pointer-events:none}.structure-list{max-height:585px;overflow:auto}.structure-item{padding:9px;border-bottom:1px solid var(--line);cursor:pointer}.structure-item.active{background:#e7f1ed}.structure-item small{display:block;color:var(--muted)}
.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}th{position:sticky;top:0;background:#f0f3ef}.figure img{max-width:100%;height:auto;border-radius:10px}.empty{padding:30px;text-align:center;border:1px dashed #b8c0ba;border-radius:12px;color:var(--muted)}
@media(max-width:850px){.shell{display:block}.sidebar{position:static;height:auto}.nav{display:flex;overflow:auto}.nav button{width:auto;white-space:nowrap}.sidebar .boundary{display:none}.main{padding:22px 15px}.molecule-layout{grid-template-columns:1fr}.topline{display:block}.status{display:inline-block;margin-top:12px}}
@media print{.sidebar,.filters,.viewer-tools{display:none!important}.shell{display:block}.main{padding:0}.view{display:block!important;break-before:page}.card{box-shadow:none;break-inside:avoid}}
"""


_JS = r"""
const DATA=JSON.parse(document.getElementById('report-data').textContent);
const $=(s,e=document)=>e.querySelector(s);const $$=(s,e=document)=>[...e.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>typeof v==='number'?(Math.abs(v)>=1000?v.toLocaleString():Number(v.toPrecision(5)).toString()):String(v??'—');
const DISPLAY_TERMS=DATA.display_terms||{};
const humanizeText=v=>{let text=String(v??'');Object.entries(DISPLAY_TERMS).sort((a,b)=>b[0].length-a[0].length).forEach(([raw,label])=>{const token=raw.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');text=text.replace(new RegExp(token,'gi'),label)});return text};
const cleanLabel=v=>humanizeText(v).replace(/_+/g,' ').replace(/\s+/g,' ').trim();
const moduleName=id=>DATA.reports.find(r=>r.module_id===id)?.title||cleanLabel(id);
function go(name){$$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));$$('.nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));location.hash=name;window.scrollTo(0,0);if(name==='molecules'&&molecular.viewer)requestAnimationFrame(()=>{molecular.viewer.resize();molecular.viewer.render()})}
$$('.nav button').forEach(b=>b.onclick=()=>go(b.dataset.view));
function badge(text,cls=''){return `<span class="badge ${cls}">${esc(text)}</span>`}
function reportForFinding(f){const p=String(f.report_path||'').replace(/^.*?results\//,'results/');return DATA.reports.find(r=>r.path===p)||DATA.reports.find(r=>r.module_id===f.module_id)}
function structureForModule(moduleId){return DATA.structures.find(s=>s.method_id===moduleId||s.module_id===moduleId)||null}
function figuresForModule(moduleId){const report=DATA.reports.find(r=>r.module_id===moduleId),classId=report?.analysis_class_id;return DATA.figures.filter(f=>f.module_id===moduleId||(classId&&f.analysis_class_id===classId)).slice(0,3)}
function findingActions(f){const r=reportForFinding(f),parts=[];if(r){const target=['pca_fes_basins','clustering_kmeans','clustering_imwkmeans','alternative_clustering','representative_frames','state_coordinate_exports'].includes(r.module_id)?'states':`analysis-${r.analysis_class_id}`;parts.push(`<button class="inline-link" data-report-view="${esc(target)}">View ${esc(target==='states'?'molecular states':r.analysis_class_title||'analysis')}</button>`)}const s=structureForModule(f.module_id);if(s)parts.push(`<button class="inline-link" data-structure-id="${esc(s.structure_id)}">Representative structure</button>`);figuresForModule(f.module_id).forEach((figure,index)=>parts.push(`<a class="inline-link" href="${esc(figure.href)}" target="_blank">${index?'Another figure':'View figure'}</a>`));return parts.join('')}
function wireActions(host){$$('[data-report-view]',host).forEach(b=>b.onclick=()=>go(b.dataset.reportView));$$('[data-structure-id]',host).forEach(b=>b.onclick=()=>openStructure(b.dataset.structureId))}
function findingHTML(f,i){const tier=f.presentation_tier||'headline',sig=f.statistically_significant===true?badge('statistically significant after correction','sig'):'';return `<div class="finding" data-category="${esc(f.category)}" data-systems="${esc((f.system_ids||[]).join(' '))}" data-tier="${esc(tier)}" data-search="${esc(JSON.stringify(f).toLowerCase())}"><div class="rank">${esc(String(f.finding_id||i+1).replace('finding-','').replace(/^0+/,''))}</div><div><div>${esc(humanizeText(f.statement))}</div><div class="badges">${badge(tier.replaceAll('_',' '))}${badge(cleanLabel(f.category))}${badge(moduleName(f.module_id))}${sig}${(f.system_ids||[]).map(s=>badge(cleanLabel(s))).join('')}</div><div class="finding-footer"><span>Effect: ${fmt(f.effect_value)}</span>${findingActions(f)}</div></div></div>`}
function renderFindings(){const host=$('#findings-list');host.innerHTML=DATA.findings.length?DATA.findings.map(findingHTML).join(''):'<div class="empty">No ranked findings were generated.</div>';wireActions(host);const cats=[...new Set(DATA.findings.map(f=>f.category))].sort();const systems=[...new Set(DATA.findings.flatMap(f=>f.system_ids||[]))].sort();$('#finding-category').innerHTML='<option value="">All categories</option>'+cats.map(v=>`<option>${esc(cleanLabel(v))}</option>`).join('');$('#finding-system').innerHTML='<option value="">All systems</option>'+systems.map(v=>`<option>${esc(v)}</option>`).join('');const tier=$('#finding-tier');tier.innerHTML=`<option value="headline">Headline (${DATA.headline_findings.length})</option><option value="secondary">Secondary (${DATA.secondary_findings.length})</option><option value="additional_candidate">Additional candidates (${Math.max(0,DATA.findings.length-DATA.highlighted_findings.length)})</option><option value="">All candidates (${DATA.findings.length})</option>`;const filter=()=>{const q=$('#finding-search').value.toLowerCase(),c=$('#finding-category').value,s=$('#finding-system').value,t=tier.value;let shown=0;$$('.finding',host).forEach(row=>{row.hidden=!!((q&&!row.dataset.search.includes(q))||(c&&cleanLabel(row.dataset.category)!==c)||(s&&!row.dataset.systems.split(' ').includes(s))||(t&&row.dataset.tier!==t));if(!row.hidden)shown+=1});$('#finding-summary').textContent=`Showing ${shown} of ${DATA.findings.length} ranked candidates.`};['finding-search','finding-category','finding-system','finding-tier'].forEach(id=>$(`#${id}`).oninput=filter);filter()}
function issueHTML(i){const sev=String(i.severity||'info').toLowerCase(),source=String(i.source||'').includes('results/')?'Analysis report':cleanLabel(i.source||'');return `<div class="issue ${esc(sev)}"><strong>${esc(sev.toUpperCase())}</strong> ${i.code?`<code>${esc(i.code)}</code>`:''}<div>${esc(humanizeText(i.message||i.reason||JSON.stringify(i)))}</div><small class="muted">${esc(moduleName(i.module_id)||'')} ${esc(source)} ${esc(cleanLabel(i.location||''))}</small></div>`}
function renderOverview(){const meta=DATA.finding_metadata||{};$('#stats').innerHTML=[['Module reports',DATA.reports.length],['Analysis classes',DATA.analysis_classes.length],['Picker-accounted modules',DATA.module_accounting.length],['Silent omissions',meta.silent_omission_count??'—'],['Headline findings',DATA.headline_findings.length],['Secondary findings',DATA.secondary_findings.length],['All candidates',DATA.findings.length]].map(([a,b])=>`<div class="stat"><strong>${fmt(b)}</strong><span>${esc(a)}</span></div>`).join('');$('#overview-finding-note').textContent=`The opening page shows the ${DATA.headline_findings.length} largest and most scientifically relevant observed differences selected by the picker. ${DATA.secondary_findings.length} additional highlights follow, and all ${DATA.findings.length} candidates remain searchable.`;const host=$('#overview-findings');host.innerHTML=DATA.headline_findings.map(findingHTML).join('')||'<div class="empty">No findings available.</div>';wireActions(host)}
function moduleHTML(r){const metrics=(r.key_metrics||[]).map(m=>`<div class="metric"><strong>${esc(cleanLabel(m.label))}</strong><br>${esc(fmt(m.value))}</div>`).join(''),a=DATA.module_accounting.find(x=>x.module_id===r.module_id),evidenceLabel=r.evidence_kind==='complete_json'?'Open results JSON':'Open compact results JSON',notes=(r.review_notes||[]).map(n=>issueHTML({severity:n.severity,code:n.status,message:n.statement,module_id:n.module_id})).join('');return `<details class="module-row" data-class="${esc(r.analysis_class_id)}" data-search="${esc((r.title+' '+r.context+' '+JSON.stringify(r.issues)+' '+JSON.stringify(a||{})).toLowerCase())}"><summary><span>${esc(r.title)} <small class="muted">${esc(r.context)}</small></span><span>${a?badge(cleanLabel(a.disposition)):''}${badge(r.technical_status,r.technical_status==='failed'?'severity-error':'')}</span></summary><p class="muted">${(r.size_bytes/1024).toFixed(1)} KiB · <a href="${esc(r.href)}" target="_blank">${evidenceLabel}</a></p>${a?`<p><strong>Picker accounting:</strong> ${esc(humanizeText(a.reason))} Candidates: ${fmt(a.candidate_count)}; highlighted: ${fmt(a.reported_finding_count)}.</p>`:''}<div class="metric-list">${metrics||'<span class="muted">No compact numeric metrics indexed.</span>'}</div>${(r.issues||[]).map(issueHTML).join('')}${notes}<details><summary>Indexed JSON preview</summary><pre class="json">${esc(humanizeText(JSON.stringify(r.preview,null,2)))}</pre></details>${(r.limitations||[]).length?`<details><summary>Scientific limitations</summary><ul>${r.limitations.map(x=>`<li>${esc(humanizeText(x))}</li>`).join('')}</ul></details>`:''}</details>`}
function renderModules(){const host=$('#module-list');host.innerHTML=DATA.reports.map(moduleHTML).join('')||'<div class="empty">No module reports found.</div>';$('#module-search').oninput=()=>{const q=$('#module-search').value.toLowerCase();$$('.module-row',host).forEach(r=>r.hidden=q&&!r.dataset.search.includes(q))}}
function renderAccounting(){const rows=DATA.module_accounting||[],host=$('#accounting-table');if(!rows.length){host.innerHTML='<div class="empty">No picker-accounting records were found.</div>';return}const cols=['module_id','review_role','report_count','candidate_count','reported_finding_count','disposition'];host.innerHTML=`<table><thead><tr>${cols.map(c=>`<th>${esc(cleanLabel(c))}</th>`).join('')}<th>Reason</th></tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(c==='module_id'?moduleName(r[c]):cleanLabel(fmt(r[c])))}</td>`).join('')}<td style="white-space:normal">${esc(humanizeText(r.reason))}</td></tr>`).join('')}</tbody></table>`}
function colorScale(t){t=Math.max(0,Math.min(1,t));const stops=[[42,30,73],[40,98,130],[35,151,138],[132,196,103],[244,222,55]];const p=t*(stops.length-1),i=Math.min(stops.length-2,Math.floor(p)),f=p-i;return `rgb(${stops[i].map((v,j)=>Math.round(v+(stops[i+1][j]-v)*f)).join(',')})`}
function representativeLinks(v){const rows=v.representative_structures||[];if(!rows.length)return '<span class="muted">No representative structure was exported for this state definition.</span>';return `<div class="representative-grid">${rows.map(s=>`<button class="representative-card" data-structure-id="${esc(s.structure_id)}"><canvas width="220" height="150" data-structure-preview="${esc(s.structure_id)}"></canvas><span>${esc(cleanLabel(s.name))}${s.system_id?` · ${esc(s.system_id)}`:''}</span></button>`).join('')}</div>`}
function drawStructurePreviews(host){$$('[data-structure-preview]',host).forEach(c=>{const s=DATA.structures.find(row=>row.structure_id===c.dataset.structurePreview);if(!s)return;const parsed=parsePDB(s.pdb_text),atoms=parsed.atoms.filter(a=>!waterResidues.has(a.res)),pts=atoms.map(a=>({a,x:.82*a.x+.38*a.z,y:.18*a.x+.86*a.y-.24*a.z}));if(!pts.length)return;const extent=Math.max(1,...pts.flatMap(p=>[Math.abs(p.x),Math.abs(p.y)])),scale=.42*Math.min(c.width,c.height)/extent,x=c.getContext('2d'),byIndex=new Map();x.fillStyle='#0e1714';x.fillRect(0,0,c.width,c.height);pts.forEach(p=>byIndex.set(p.a.i,{...p,sx:c.width/2+p.x*scale,sy:c.height/2-p.y*scale}));const traces={};[...byIndex.values()].filter(p=>['CA','P'].includes(p.a.name)).forEach(p=>(traces[p.a.chain]??=[]).push(p));x.lineCap='round';x.lineJoin='round';Object.values(traces).forEach(t=>{let previous=null;t.forEach(p=>{if(!previous||Math.hypot(p.a.x-previous.a.x,p.a.y-previous.a.y,p.a.z-previous.a.z)>8){previous=p;return}x.beginPath();x.moveTo(previous.sx,previous.sy);x.lineTo(p.sx,p.sy);x.strokeStyle='#5aa18d';x.lineWidth=6;x.stroke();previous=p})});parsed.bonds.forEach(([i,j])=>{const a=byIndex.get(i),b=byIndex.get(j);if(!a||!b||!isHetero(a.a)||!isHetero(b.a))return;x.beginPath();x.moveTo(a.sx,a.sy);x.lineTo(b.sx,b.sy);x.strokeStyle='#c8d1cd';x.lineWidth=2;x.stroke()});[...byIndex.values()].filter(p=>isHetero(p.a)).forEach(p=>{x.beginPath();x.arc(p.sx,p.sy,isIon(p.a)?7:2.8,0,Math.PI*2);x.fillStyle=elemColors[p.a.el]||'#d0a8c9';x.fill()})})}
function renderFES(v,host){
  const land=v.landscape||{},grid=land.grid||[];
  if(!grid.length){host.innerHTML='<div class="empty">No FES grid.</div>';return}
  const nx=1+Math.max(...grid.map(r=>r.x_bin)),ny=1+Math.max(...grid.map(r=>r.y_bin));
  const field=grid.some(r=>typeof r.relative_free_energy_kcal_per_mol==='number')?'relative_free_energy_kcal_per_mol':'relative_occupancy_score';
  const vals=grid.map(r=>r[field]).filter(Number.isFinite),max=Math.max(...vals,1e-9),bounds=land.bounds||{};
  const xmin=bounds.x_min_angstrom??bounds.x_min??0,xmax=bounds.x_max_angstrom??bounds.x_max??nx;
  const ymin=bounds.y_min_angstrom??bounds.y_min??0,ymax=bounds.y_max_angstrom??bounds.y_max??ny;
  const c=document.createElement('canvas');c.width=Math.max(620,nx*12);c.height=Math.max(500,ny*12);c.className='chart';
  const x=c.getContext('2d'),left=72,right=28,top=25,bottom=66,w=c.width-left-right,h=c.height-top-bottom;
  x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);
  grid.forEach(r=>{const val=r[field];x.fillStyle=Number.isFinite(val)?colorScale(1-val/max):'#eceeea';const cw=w/nx,ch=h/ny;x.fillRect(left+r.x_bin*cw,top+(ny-1-r.y_bin)*ch,cw+.4,ch+.4)});
  x.strokeStyle='#26362f';x.strokeRect(left,top,w,h);x.fillStyle='#18211d';x.font='13px sans-serif';x.textAlign='center';
  x.fillText(`PC ${v.x_component||1} coordinate (Å)`,left+w/2,c.height-14);
  x.fillText(fmt(xmin),left,c.height-bottom+22);x.fillText(fmt(xmax),left+w,c.height-bottom+22);
  x.save();x.translate(18,top+h/2);x.rotate(-Math.PI/2);x.fillText(`PC ${v.y_component||2} coordinate (Å)`,0,0);x.restore();
  x.textAlign='right';x.fillText(fmt(ymin),left-8,top+h+4);x.fillText(fmt(ymax),left-8,top+4);
  (land.basins||[]).forEach(b=>{const cw=w/nx,ch=h/ny,px=left+(b.root_x_bin+.5)*cw,py=top+(ny-1-b.root_y_bin+.5)*ch;x.beginPath();x.arc(px,py,8,0,Math.PI*2);x.fillStyle='rgba(255,255,255,.9)';x.fill();x.strokeStyle='#111';x.stroke();x.fillStyle='#111';x.font='bold 10px sans-serif';x.textAlign='center';x.fillText(String(b.basin_id),px,py+3)});
  c.title=field.replaceAll('_',' ');host.appendChild(c);
  host.insertAdjacentHTML('beforeend',`<div class="chart-note">${esc(v.context||'')} ${esc(v.title)}. Color shows ${esc(field.replaceAll('_',' '))}; numbered circles mark basin roots.</div><div class="structure-links">${representativeLinks(v)}</div>`);
  wireActions(host);drawStructurePreviews(host);
}
function renderClusters(v,host){
  const sizes=v.cluster_sizes||[],total=sizes.reduce((a,b)=>a+b,0)||1,w=760,h=400,left=68,right=24,top=28,bottom=62,plotW=w-left-right,plotH=h-top-bottom;
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(v.method_name)} cluster populations">`;
  [0,25,50,75,100].forEach(t=>{const y=top+plotH*(1-t/100);svg+=`<line x1="${left}" y1="${y}" x2="${w-right}" y2="${y}" stroke="#d9ddd7"/><text x="${left-8}" y="${y+4}" text-anchor="end" font-size="11">${t}</text>`});
  const bw=plotW/Math.max(1,sizes.length);
  sizes.forEach((n,i)=>{const pct=100*n/total,bh=plotH*pct/100,x=left+i*bw+5,y=top+plotH-bh;svg+=`<rect x="${x}" y="${y}" width="${Math.max(4,bw-10)}" height="${bh}" fill="#1c7166"><title>Cluster ${i+1}: ${n} frames (${pct.toFixed(1)}%)</title></rect><text x="${x+(bw-10)/2}" y="${top+plotH+18}" text-anchor="middle" font-size="11">${i+1}</text>`});
  svg+=`<text x="${left+plotW/2}" y="${h-10}" text-anchor="middle" font-size="12">Cluster</text><text x="18" y="${top+plotH/2}" transform="rotate(-90 18 ${top+plotH/2})" text-anchor="middle" font-size="12">Population (%)</text></svg>`;
  const systems=v.system_populations||[],states=sizes.map((_,i)=>i+1);
  const table=systems.length?`<div class="table-wrap"><table><thead><tr><th>System</th>${states.map(s=>`<th>Cluster ${s}</th>`).join('')}</tr></thead><tbody>${systems.map(row=>{const byState=Object.fromEntries((row.state_populations||[]).map(p=>[p.state_id,p.fraction_of_assigned??p.fraction_of_all_evaluated]));return `<tr><td>${esc(cleanLabel(row.system_id))}</td>${states.map(s=>`<td>${Number.isFinite(byState[s])?(100*byState[s]).toFixed(1)+'%':'—'}</td>`).join('')}</tr>`}).join('')}</tbody></table></div>`:'';
  host.innerHTML=svg+`<div class="chart-note"><strong>${esc(v.method_name)}</strong> · silhouette ${fmt(v.silhouette)} · ${sizes.length} clusters · ${total.toLocaleString()} assigned observations.</div>${table}<div class="structure-links">${representativeLinks(v)}</div>`;
  wireActions(host);drawStructurePreviews(host);
}
function renderRMSF(v,host){const rows=v.residues||[],w=900,h=360,p=50;if(!rows.length){host.innerHTML='<div class="empty">No RMSF rows.</div>';return}const max=Math.max(...rows.map(r=>r.mean_rmsf_angstrom),1e-9),step=Math.max(1,Math.ceil(rows.length/1000)),shown=rows.filter((_,i)=>i%step===0);const pts=shown.map((r,i)=>`${p+i*(w-2*p)/Math.max(1,shown.length-1)},${h-p-r.mean_rmsf_angstrom*(h-2*p)/max}`).join(' ');host.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Residue RMSF"><line x1="${p}" y1="${p}" x2="${p}" y2="${h-p}" stroke="#777"/><line x1="${p}" y1="${h-p}" x2="${w-p}" y2="${h-p}" stroke="#777"/><polyline points="${pts}" fill="none" stroke="#3767a6" stroke-width="2"/><text x="15" y="${h/2}" transform="rotate(-90 15 ${h/2})" font-size="12">RMSF (Å)</text><text x="${w/2}" y="${h-10}" text-anchor="middle" font-size="12">Residue order</text></svg><div class="chart-note">${esc(v.title)}; residue values are means over mapped atom RMSFs. Display stride ${step}.</div>`}
function renderDCCM(v,host){const m=v.matrix||[],n=m.length;if(!n){host.innerHTML='<div class="empty">No DCCM matrix.</div>';return}const c=document.createElement('canvas');c.width=Math.max(540,n*3+70);c.height=c.width;const x=c.getContext('2d'),pad=52,side=c.width-pad-18,cell=side/n;x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);m.forEach((row,i)=>row.forEach((z,j)=>{const q=Number.isFinite(z)?z:0;x.fillStyle=q<0?`rgb(${Math.round(255*(1+q))},${Math.round(255*(1+q))},255)`:`rgb(255,${Math.round(255*(1-q))},${Math.round(255*(1-q))})`;x.fillRect(pad+i*cell,pad+(n-1-j)*cell,cell+.5,cell+.5)}));x.strokeStyle='#26362f';x.strokeRect(pad,pad,side,side);x.fillStyle='#18211d';x.font='12px sans-serif';x.textAlign='center';x.fillText('Atom/residue index',pad+side/2,c.height-8);x.save();x.translate(14,pad+side/2);x.rotate(-Math.PI/2);x.fillText('Atom/residue index',0,0);x.restore();c.className='chart';host.appendChild(c);host.insertAdjacentHTML('beforeend',`<div class="chart-note">${esc(v.title)}; blue is anticorrelation and red is positive correlation. ${v.source_atom_count} source atoms; display stride ${v.display_stride}.</div>`)}
function allVisuals(){return DATA.reports.flatMap(r=>(r.visuals||[]).map(v=>({...v,module_id:r.module_id,analysis_class_id:r.analysis_class_id,context:v.context||r.context})))}
function drawVisualCard(v,host,rank=null){const card=document.createElement('section');card.className='card';const heading=rank?`${rank}. ${v.method_name||v.title}`:v.title;card.innerHTML=`<h3>${esc(cleanLabel(heading))}</h3><div class="chart"></div>`;host.appendChild(card);const target=$('.chart',card);target.className='';if(v.kind==='fes')renderFES(v,target);else if(v.kind==='cluster_populations')renderClusters(v,target);else if(v.kind==='rmsf')renderRMSF(v,target);else if(v.kind==='dccm')renderDCCM(v,target)}
function renderVisuals(){const visuals=allVisuals().filter(v=>['fes','cluster_populations'].includes(v.kind));const select=$('#visual-kind');select.innerHTML='<option value="">FES followed by clustering</option><option value="fes">Free-energy surfaces</option><option value="cluster_populations">Clustering, best silhouette first</option>';function draw(){const host=$('#visual-list'),kind=select.value;host.innerHTML='';const selected=visuals.filter(v=>!kind||v.kind===kind).sort((a,b)=>{if(a.kind!==b.kind)return a.kind==='fes'?-1:1;if(a.kind==='cluster_populations')return (Number.isFinite(b.silhouette)?b.silhouette:-Infinity)-(Number.isFinite(a.silhouette)?a.silhouette:-Infinity);return String(a.title).localeCompare(String(b.title))});let clusterRank=0;selected.forEach(v=>drawVisualCard(v,host,v.kind==='cluster_populations'?++clusterRank:null));if(!host.children.length)host.innerHTML='<div class="empty">No molecular-state visualization is available for this filter.</div>'}select.oninput=draw;draw()}
function renderAnalysisTabs(){const nav=$('#analysis-nav'),views=$('#analysis-views');nav.innerHTML='';views.innerHTML='';(DATA.analysis_classes||[]).forEach(group=>{const name=`analysis-${group.class_id}`,button=document.createElement('button');button.dataset.view=name;button.textContent=group.title;button.onclick=()=>go(name);nav.appendChild(button);const section=document.createElement('section');section.id=`view-${name}`;section.className='view';const reports=DATA.reports.filter(r=>r.analysis_class_id===group.class_id),figures=DATA.figures.filter(f=>f.analysis_class_id===group.class_id),visuals=allVisuals().filter(v=>v.analysis_class_id===group.class_id);section.innerHTML=`<section class="card"><h2>${esc(group.title)}</h2><div class="analysis-visuals"></div></section>${figures.length?`<section class="card"><h3>Figures</h3><div class="grid analysis-figures">${figures.map(f=>`<section class="figure"><h4>${esc(cleanLabel(f.name))}</h4><img src="data:${f.data_uri}" alt="${esc(cleanLabel(f.name))}"><p><a href="${esc(f.href)}" target="_blank">Open figure file</a></p></section>`).join('')}</div></section>`:''}<section class="card"><h3>Reports</h3>${reports.map(moduleHTML).join('')}</section>`;views.appendChild(section);const visualHost=$('.analysis-visuals',section);const ordered=visuals.sort((a,b)=>a.kind==='cluster_populations'&&b.kind==='cluster_populations'?((b.silhouette??-Infinity)-(a.silhouette??-Infinity)):String(a.title).localeCompare(String(b.title)));ordered.forEach((v,i)=>drawVisualCard(v,visualHost,v.kind==='cluster_populations'?i+1:null));if(!ordered.length)visualHost.innerHTML='<p class="muted">The report details and packaged evidence files are available below.</p>'})}
function renderFigures(){const host=$('#figure-list');host.innerHTML=DATA.figures.map(f=>`<section class="card figure"><h3>${esc(cleanLabel(f.name))}</h3><img src="data:${f.data_uri}" alt="${esc(cleanLabel(f.name))}"><p><a href="${esc(f.href)}" target="_blank">Open figure file</a></p></section>`).join('')||'<div class="empty">No pre-rendered image files were found.</div>'}
function renderResources(){const rows=DATA.resources||[],host=$('#resource-table');if(!rows.length){host.innerHTML='<div class="empty">No consolidated resource/frame table was found.</div>';return}const wanted=['module_id','technical_status','total_cpu_seconds','wall_seconds','maximum_resident_memory_mib','selected_source_physical_frames','analysis_frame_stride','basis_frame_stride','symmetry_expanded_observations','model_fit_observations','full_assignment_observations'];const cols=wanted.filter(k=>rows.some(r=>k in r));host.innerHTML=`<table><thead><tr>${cols.map(c=>`<th>${esc(cleanLabel(c))}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(c==='module_id'?moduleName(r[c]):fmt(r[c]))}</td>`).join('')}</tr>`).join('')}</tbody></table>`}
function renderQC(){const host=$('#qc-list');host.innerHTML=DATA.qc_issues.map(issueHTML).join('')||'<div class="empty">No QC issues were indexed.</div>';const picker=$('#picker-qc-list');picker.innerHTML=DATA.picker_qc_records.map(r=>issueHTML({severity:r.severity,code:r.status,message:r.statement,module_id:r.module_id,source:r.report_path})).join('')||'<div class="empty">No additional QC records were reported.</div>';$('#provenance-links').innerHTML=Object.entries(DATA.raw_links||{}).map(([label,href])=>`<a href="${esc(href)}" target="_blank">${esc(label)}</a>`).join(' · ');$('#provenance-json').textContent=humanizeText(JSON.stringify({module_coverage:DATA.module_coverage,chemical_context:DATA.chemical_context,conformational_views:DATA.conformational_views,sampling_plan:DATA.sampling_plan,configuration:DATA.configuration,project_manifest:DATA.project_manifest,system_manifest:DATA.system_manifest,preflight:DATA.preflight,omitted_structures:DATA.omitted_structures,omitted_figures:DATA.omitted_figures},null,2))}
const molecular={viewer:null,model:null,index:-1};
const elemColors={H:'#e7ecea',C:'#a9b3ae',N:'#4b77d1',O:'#d94a45',S:'#e3b63b',P:'#e27731',ZN:'#8b6ab8',MG:'#44b78b',K:'#b55ec5',NA:'#6c77d8',CA:'#3ba86a',CL:'#4db04f',FE:'#c66a35',MN:'#9c7bb8',CU:'#c77b3a',CO:'#cf718a',NI:'#70a57e'};
const polymerResidues=new Set('ALA ARG ASN ASP CYS GLN GLU GLY HIS HSD HSE HSP ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL ACE NME A C G U T DA DC DG DT DU ADE CYT GUA THY URA RA RC RG RU'.split(' '));
const waterResidues=new Set('HOH WAT TIP3 TIP3P SOL H2O'.split(' '));
const ionElements=new Set(['LI','NA','K','RB','CS','MG','CA','SR','BA','MN','FE','CO','NI','CU','ZN','CD','HG','CL']);
const ionResidues=new Set(['LI','LIT','NA','SOD','K','POT','RB','CS','MG','CAL','CA','SR','BA','MN','FE','FE2','FE3','CO','NI','CU','CU1','CU2','ZN','CD','HG','CL','CLA']);
const covalentRadius={H:.31,C:.76,N:.71,O:.66,F:.57,P:1.07,S:1.05,CL:1.02,ZN:1.22,MG:1.41,FE:1.24,CA:1.76,NA:1.66,K:2.03};
function parsePDB(text){const atoms=[],connect=[],serialToIndex=new Map();text.split(/\r?\n/).forEach((line,i)=>{const rec=line.slice(0,6).trim();if(rec==='CONECT'){const ids=line.slice(6).trim().split(/\s+/).map(Number).filter(Number.isFinite);if(ids.length>1)ids.slice(1).forEach(b=>connect.push([ids[0],b]));return}if(!['ATOM','HETATM'].includes(rec))return;const x=+line.slice(30,38),y=+line.slice(38,46),z=+line.slice(46,54);if(![x,y,z].every(Number.isFinite))return;let el=line.slice(76,78).trim().toUpperCase()||line.slice(12,16).trim().replace(/[0-9]/g,'').slice(0,2).toUpperCase();if(el.length>1&&!ionElements.has(el))el=el[0];const atom={i:atoms.length,serial:+line.slice(6,11),rec,name:line.slice(12,16).trim(),res:line.slice(17,20).trim().toUpperCase(),chain:line.slice(21,22).trim()||'_',resid:+line.slice(22,26),x,y,z,b:+line.slice(60,66)||0,el};serialToIndex.set(atom.serial,atom.i);atoms.push(atom)});if(!atoms.length)return{atoms,bonds:[]};const cx=atoms.reduce((s,a)=>s+a.x,0)/atoms.length,cy=atoms.reduce((s,a)=>s+a.y,0)/atoms.length,cz=atoms.reduce((s,a)=>s+a.z,0)/atoms.length;atoms.forEach(a=>{a.x-=cx;a.y-=cy;a.z-=cz});const bondSet=new Set(),bonds=[];const addBond=(i,j)=>{if(i===undefined||j===undefined||i===j)return;const key=i<j?`${i}:${j}`:`${j}:${i}`;if(!bondSet.has(key)){bondSet.add(key);bonds.push([i,j])}};connect.forEach(([a,b])=>addBond(serialToIndex.get(a),serialToIndex.get(b)));const ligand=atoms.filter(a=>isHetero(a)&&!isIon(a));if(ligand.length<=600)for(let i=0;i<ligand.length;i++)for(let j=i+1;j<ligand.length;j++){const a=ligand[i],b=ligand[j];if(a.chain!==b.chain||a.resid!==b.resid||a.res!==b.res)continue;const d2=(a.x-b.x)**2+(a.y-b.y)**2+(a.z-b.z)**2,cut=(covalentRadius[a.el]||.8)+(covalentRadius[b.el]||.8)+.45;if(d2>.16&&d2<cut*cut)addBond(a.i,b.i)}return{atoms,bonds}}
function isIon(a){return a.rec==='HETATM'&&ionElements.has(a.el)&&(ionResidues.has(a.res)||a.res===a.el)}
function isHetero(a){return !waterResidues.has(a.res)&&(a.rec==='HETATM'||isIon(a)||!polymerResidues.has(a.res))}
function colorScheme(){const mode=$('#viewer-color').value;if(mode==='chain')return'chain';if(mode==='bfactor'){const atoms=molecular.viewer.selectedAtoms({});const range=$3Dmol.getPropertyRange(atoms,'b');return{prop:'b',gradient:new $3Dmol.Gradient.RWB(range)}}return'Jmol'}
function searchSelection(){const q=$('#viewer-search').value.trim();if(!q)return null;const parts=q.split(':');if(parts.length>=3){const chain=parts[0],match=parts[1].match(/^([A-Za-z0-9]+?)(-?\d+)$/),atom=parts.slice(2).join(':');if(match)return{chain,resn:match[1],resi:+match[2],atom}}if(/^\d+$/.test(q))return{resi:+q};return{resn:q.toUpperCase()}}
function applyMolecularStyle(){if(!molecular.viewer||!molecular.model)return;const rep=$('#viewer-representation').value,scheme=colorScheme(),showH=$('#viewer-h').checked,ions=[...ionElements];molecular.viewer.setStyle({},{});if(rep==='all')molecular.viewer.setStyle({},{stick:{radius:.18,colorscheme:scheme}});if(rep==='overview'||rep==='backbone')molecular.viewer.setStyle({hetflag:false},{cartoon:{style:'rectangle',arrows:true,tubes:false,thickness:.4,colorscheme:scheme}});if(rep==='overview'||rep==='hetero')molecular.viewer.setStyle({hetflag:true},{stick:{radius:.24,colorscheme:scheme}});ions.forEach(elem=>molecular.viewer.setStyle({elem},{sphere:{scale:.55,colorscheme:'Jmol'}}));if(!showH)molecular.viewer.setStyle({elem:'H'},{});const selection=searchSelection();if(selection){molecular.viewer.addStyle(selection,{stick:{radius:.36,color:'#ffd54f'},sphere:{scale:.35,color:'#ffd54f'}});molecular.viewer.zoomTo(selection)}molecular.viewer.render();const count=molecular.viewer.selectedAtoms({}).filter(a=>showH||String(a.elem).toUpperCase()!=='H').length;$('#viewer-info').textContent=`${count.toLocaleString()} non-solvent atoms · true molecular cartoon · bonded ligands/cofactors · space-filling ions · drag to rotate, scroll to zoom`}
function loadStructure(index){const s=DATA.structures[index];if(!s||!molecular.viewer)return;molecular.index=index;molecular.viewer.removeAllModels();molecular.model=molecular.viewer.addModel(s.pdb_text,'pdb',{keepH:true});molecular.viewer.setClickable({},true,(atom)=>{$('#viewer-info').textContent=`${atom.chain||'_'}:${atom.resn}${atom.resi}:${atom.atom} · ${atom.elem} · B ${Number(atom.b||0).toFixed(2)}`});$('#structure-title').textContent=cleanLabel(s.name);$$('.structure-item').forEach((e,i)=>e.classList.toggle('active',i===index));applyMolecularStyle();molecular.viewer.zoomTo();molecular.viewer.render()}
function openStructure(structureId){const index=DATA.structures.findIndex(s=>s.structure_id===structureId);if(index<0)return;go('molecules');loadStructure(index)}
function renderMolecules(){const list=$('#structure-list');list.innerHTML=DATA.structures.map((s,i)=>`<div class="structure-item" data-index="${i}"><strong>${esc(cleanLabel(s.name))}</strong><small>${esc(s.system_id||moduleName(s.module_id)||'Representative structure')} · ${fmt(s.atom_count)} atoms · <a href="${esc(s.href)}" target="_blank">Open PDB</a></small></div>`).join('')||'<div class="empty">No PDB representative structures were found.</div>';$$('.structure-item',list).forEach(e=>e.addEventListener('click',ev=>{if(ev.target.tagName!=='A')loadStructure(+e.dataset.index)}));if(typeof $3Dmol==='undefined'){$('#viewer-info').textContent='The embedded molecular renderer could not be loaded.';return}molecular.viewer=$3Dmol.createViewer($('#molecule-viewer'),{backgroundColor:'#0e1714',antialias:true});['viewer-representation','viewer-color','viewer-h'].forEach(id=>{const control=$(`#${id}`);control.addEventListener('change',applyMolecularStyle)});$('#viewer-search').addEventListener('change',applyMolecularStyle);$('#viewer-reset').addEventListener('click',()=>loadStructure(molecular.index));if(DATA.structures.length)loadStructure(0);if('ResizeObserver' in window)new ResizeObserver(()=>{molecular.viewer.resize();molecular.viewer.render()}).observe($('#molecule-viewer'))}
renderAnalysisTabs();renderOverview();renderFindings();renderModules();renderAccounting();renderVisuals();renderFigures();renderResources();renderQC();renderMolecules();go((location.hash||'#overview').slice(1));
"""


def _render_html(data: Mapping[str, object]) -> str:
    try:
        threedmol_javascript = _THREEDMOL_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise InteractiveReportError(
            f"bundled 3Dmol.js renderer is unavailable: {_THREEDMOL_PATH}"
        ) from exc
    threedmol_javascript = threedmol_javascript.replace("</script", "<\\/script")
    encoded = json.dumps(
        _json_safe(data),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    encoded = encoded.replace("</script", "<\\/script").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    title = html.escape(str(data["title"]))
    systems = ", ".join(data.get("system_ids", []))
    system_line = f'<div class="muted">{html.escape(systems)}</div>' if systems else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; frame-src 'none'; connect-src 'none'; media-src 'self'">
<title>{title} — interactive molecular analysis</title><style>{_CSS}</style></head>
<body><div class="shell"><aside class="sidebar"><div class="brand">Salsbury MD Analysis</div><div class="subtitle">Interactive results · v0.1.2</div><nav class="nav">
<button data-view="overview">Overview</button><button data-view="findings">Key findings</button><button data-view="states">Molecular states & figures</button><button data-view="molecules">Molecular structures</button><div class="nav-heading">Analysis results</div><div id="analysis-nav"></div><button data-view="analyses">All reports</button><button data-view="resources">Resources & sampling</button><button data-view="qc">QC & provenance</button></nav></aside>
<main class="main"><div class="topline"><div><div class="eyebrow">Analysis campaign</div><h1>{title}</h1>{system_line}</div><span class="status">{html.escape(str(data['technical_status']))}</span></div>
<section id="view-overview" class="view"><div id="stats" class="stats"></div><section class="card"><h2>Highest-priority findings</h2><p id="overview-finding-note" class="muted"></p><div id="overview-findings"></div><p><button onclick="go('findings')">Review all ranked findings</button></p></section></section>
<section id="view-findings" class="view"><section class="card"><h2>Ranked findings</h2><p class="muted">The opening page contains the largest and most scientifically relevant observed differences selected by the picker. Additional highlights and every other candidate remain searchable here.</p><div class="filters"><input id="finding-search" placeholder="Search findings"><select id="finding-tier"></select><select id="finding-category"></select><select id="finding-system"></select></div><p id="finding-summary" class="muted"></p><div id="findings-list"></div></section><section class="card"><h2>Complete picker accounting</h2><p class="muted">Every completed module is listed, including QC, context, technical support, and reports that produced no automatic highlight.</p><div id="accounting-table" class="table-wrap"></div></section></section>
<section id="view-states" class="view"><section class="card"><h2>Molecular states & generated figures</h2><p class="muted">Free-energy surfaces appear first. Clustering methods follow in descending silhouette-score order, with per-system populations and available representative structures.</p><div class="visual-controls"><select id="visual-kind"></select></div></section><div id="visual-list"></div><h2>Pre-rendered figures</h2><div id="figure-list" class="grid"></div></section>
<section id="view-molecules" class="view"><section class="card"><h2>Representative molecular structures</h2><p class="muted">Each packaged PDB retains all non-solvent atoms. The default view uses a VMD-style polymer cartoon, bonded ligands and cofactors, and space-filling ions.</p><div class="molecule-layout"><div class="viewer"><div class="viewer-tools"><select id="viewer-representation"><option value="overview">Cartoon + ligands/cofactors + ions</option><option value="all">All non-solvent atoms</option><option value="backbone">Polymer cartoon</option><option value="hetero">Ligands, cofactors and ions</option></select><select id="viewer-color"><option value="chain">Color by chain</option><option value="element">Color by element</option><option value="bfactor">Color by B factor</option></select><label style="color:white"><input id="viewer-h" type="checkbox"> H</label><input id="viewer-search" placeholder="A:CYS54:SG"><button id="viewer-reset">Reset</button></div><div id="molecule-viewer" class="molecule-viewer"></div><div id="viewer-info" class="viewer-info"></div></div><div><h3 id="structure-title">Structures</h3><div id="structure-list" class="structure-list"></div></div></div></section></section>
<div id="analysis-views"></div>
<section id="view-analyses" class="view"><section class="card"><h2>All reports</h2><p class="muted">Every indexed module is listed whether or not it produced a ranked finding.</p><div class="filters"><input id="module-search" placeholder="Search reports and issues"></div><div id="module-list"></div></section></section>
<section id="view-resources" class="view"><section class="card"><h2>Resources, frames, and sampling</h2><div id="resource-table" class="table-wrap"></div></section></section>
<section id="view-qc" class="view"><section class="card"><h2>QC requiring attention</h2><div id="qc-list"></div></section><section class="card"><h2>Additional QC records</h2><p class="muted">These records stay under QC and are not mixed into scientific-result tabs.</p><div id="picker-qc-list"></div></section><section class="card"><h2>Configuration and provenance</h2><p id="provenance-links"></p><pre id="provenance-json" class="json"></pre></section></section>
</main></div><script id="report-data" type="application/json">{encoded}</script><script>{threedmol_javascript}</script><script>{_JS}</script></body></html>"""


def _validate_existing(target: Path) -> Dict[str, object]:
    manifest_path = target / "manifest.json"
    index_path = target / "index.html"
    if not manifest_path.is_file() or not index_path.is_file():
        raise InteractiveReportError(
            f"interactive-report directory exists without complete evidence: {target}"
        )
    manifest = _load_json(manifest_path)
    if (
        not isinstance(manifest, dict)
        or manifest.get("technical_status") != "complete"
        or manifest.get("index_sha256") != _sha256_file(index_path)
    ):
        raise InteractiveReportError(
            f"existing interactive report is incomplete or hash-mismatched: {target}"
        )
    return {**manifest, "reused": True}


def build_interactive_report(
    root: Path,
    *,
    output_name: str = "interactive-report",
    title: str | None = None,
    maximum_inline_structures: int = 100,
    maximum_inline_structure_bytes: int = 50_000_000,
    maximum_inline_figure_bytes: int = 25_000_000,
) -> Dict[str, object]:
    """Build an immutable, offline interactive result under an analysis root."""

    analysis_root = Path(root).expanduser().resolve(strict=True)
    source_reports = sorted((analysis_root / "results").glob("**/report.json"))
    if not source_reports:
        raise InteractiveReportError(
            "analysis root has no results/**/report.json source reports"
        )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", output_name):
        raise InteractiveReportError("output_name must be one safe path component")
    for label, value in (
        ("maximum_inline_structures", maximum_inline_structures),
        ("maximum_inline_structure_bytes", maximum_inline_structure_bytes),
        ("maximum_inline_figure_bytes", maximum_inline_figure_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise InteractiveReportError(f"{label} must be a nonnegative integer")
    target = analysis_root / output_name
    if target.exists():
        return _validate_existing(target)
    temporary = analysis_root / f".{output_name}.tmp-{os.getpid()}"
    if temporary.exists():
        raise InteractiveReportError(f"temporary interactive-report path exists: {temporary}")
    temporary.mkdir()
    try:
        data, source_records = _collect_data(
            analysis_root,
            title=title,
            maximum_inline_structures=maximum_inline_structures,
            maximum_inline_structure_bytes=maximum_inline_structure_bytes,
            maximum_inline_figure_bytes=maximum_inline_figure_bytes,
        )
        portable_evidence_records = _write_portable_evidence(
            analysis_root, temporary, data
        )
        html_text = _render_html(data)
        index_path = temporary / "index.html"
        index_path.write_text(html_text, encoding="utf-8")
        manifest = {
            "interactive_report_manifest_schema": "salsbury-interactive-results-manifest-v1",
            "generator_package": _GENERATOR_PACKAGE,
            "generator_version": _GENERATOR_VERSION,
            "technical_status": "complete",
            "scientific_status": "not evaluated",
            "generated_at_utc": data["generated_at_utc"],
            "index_path": f"{output_name}/index.html",
            "index_sha256": _sha256_file(index_path),
            "index_size_bytes": index_path.stat().st_size,
            "module_report_count": len(data["reports"]),
            "finding_count": len(data["highlighted_findings"]),
            "headline_finding_count": len(data["headline_findings"]),
            "secondary_finding_count": len(data["secondary_findings"]),
            "searchable_candidate_count": len(data["findings"]),
            "finding_presentation_contract": data["presentation_contract"],
            "picker_accounted_module_count": len(data["module_accounting"]),
            "picker_qc_record_count": len(data["picker_qc_records"]),
            "picker_silent_omission_count": (
                data.get("finding_metadata", {}).get("silent_omission_count")
                if isinstance(data.get("finding_metadata"), dict) else None
            ),
            "inline_structure_count": len(data["structures"]),
            "omitted_structure_count": len(data["omitted_structures"]),
            "inline_figure_count": len(data["figures"]),
            "omitted_figure_count": len(data["omitted_figures"]),
            "source_report_records": source_records,
            "portable_evidence_records": portable_evidence_records,
            "portable_evidence_count": len(portable_evidence_records),
            "network_dependency": "none",
            "interpretation": data["scientific_boundary"],
        }
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, target)
        return {
            **manifest,
            "output_directory": str(target),
            "index_path": str(target / "index.html"),
            "manifest_path": str(target / "manifest.json"),
            "reused": False,
        }
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
