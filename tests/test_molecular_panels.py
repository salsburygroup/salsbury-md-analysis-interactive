import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from salsbury_md_analysis_interactive.molecular_panels import load_spec, molecular_evidence_metadata


class MolecularPanelTests(unittest.TestCase):
    def test_binding_checks_saved_outputs_and_coordinate_ids(self):
        try:
            from salsbury_md_analysis.molecular_evidence import finding_signature
        except ImportError:
            self.skipTest('Requires the matching core molecular-evidence contract')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);spec=self.fixture(root)
            for name in ('figure.png','view.html'):
                (root/name).write_text(name)
            digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            record={'schema':'salsbury-molecular-render-v1','complete':True,'spec':spec,
                    'figure_sha256':digest(root/'figure.png'),'saved_view_sha256':digest(root/'view.html')}
            (root/'render.json').write_text(json.dumps(record))
            finding={'module_id':'pooled_rmsf','statement':'Measured fluctuation difference'}
            result=molecular_evidence_metadata(root,finding,['pdb'],'view')
            self.assertEqual(result['finding_signature_sha256'],finding_signature(finding))
            with self.assertRaises(ValueError):
                molecular_evidence_metadata(root,finding,[],'view')
            (root/'view.html').write_text('changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                molecular_evidence_metadata(root,finding,['pdb'],'view')

    def fixture(self, root):
        path = root / 'sample.pdb'
        path.write_text("ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00  0.00           C  \nEND\n")
        return {"schema": "salsbury-molecular-panel-v1", "title": "Control",
                "caption": "Observed structure", "alignment_description": "Single panel",
                "panels": [{"label": "Control", "pdb_path": path.name,
                    "pdb_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "selection_rule": "First retained frame", "source_identity": {
                        "system_id": "control", "replica_id": "rep1", "segment_id": "seg1", "source_frame_index": 0}}]}

    def test_valid_and_hash_bound_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); spec = self.fixture(root); path = root / "spec.json"
            path.write_text(json.dumps(spec))
            self.assertEqual(load_spec(path)["panels"][0]["pdb_path"], str((root / "sample.pdb").resolve()))
            (root / 'sample.pdb').write_text('END\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                load_spec(path)

    def test_rejects_unmatched_annotations_and_invalid_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); spec = self.fixture(root); path = root / "spec.json"
            changes = [{"highlights": [{"selection": {"resi": 2}, "label": "Missing"}]},
                       {"visible_ion_serials": [1]}, {"label": ""},
                       {"source_identity": {**spec['panels'][0]['source_identity'], 'source_frame_index': -1}},
                       {"atom_values": [{"serial": 9, "value": 1.0}]}]
            for change in changes:
                modified = copy.deepcopy(spec); modified['panels'][0].update(change)
                path.write_text(json.dumps(modified))
                with self.assertRaises(ValueError):
                    load_spec(path)
            spec['panels'][0]['atom_values'] = [{'serial': 1, 'value': 1.0}]
            spec['color_range'] = [1, 1]
            path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'increasing'):
                load_spec(path)
