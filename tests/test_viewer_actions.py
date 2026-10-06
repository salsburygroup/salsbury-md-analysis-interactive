"""Finding visibility contract and offline structure fallback regressions."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from salsbury_md_analysis_interactive.report import _CSS, _JS


class ViewerActionTests(unittest.TestCase):
    def test_hidden_findings_override_grid_without_hiding_other_elements(self):
        rules = re.findall(r'([^{}]+)\{([^{}]*)\}', _CSS)
        scoped = [body for selector, body in rules if selector.strip() == '.finding[hidden]']
        self.assertEqual(scoped, ['display:none'])
        self.assertGreater(_CSS.index('.finding[hidden]'), _CSS.index('.finding{display:grid'))
        self.assertNotIn('[hidden]{display:none}', _CSS.replace('.finding[hidden]{display:none}', ''))

    def test_actual_javascript_filters_and_structure_actions(self):
        node = os.environ.get('SALSBURY_NODE_EXECUTABLE') or shutil.which('node')
        if not node:
            self.skipTest('Node required for non-browser JavaScript regression')
        rows = [dict(finding_id=f'finding-{i}', statement=statement, category=category,
                     system_ids=[system], presentation_tier=tier)
                for i, (statement, category, system, tier) in enumerate([
                    ('Dihedral difference', 'dihedral', 'A', 'headline'),
                    ('RMSF difference', 'rmsf', 'B', 'headline'),
                    ('Dihedral distribution', 'dihedral', 'B', 'secondary'),
                    ('RMSF profile', 'rmsf', 'A', 'additional_candidate')])]
        structures = [dict(structure_id='structure-00001',name='Inline',href='evidence/inline.pdb')]
        omitted = [dict(structure_id='structure-00125',name='Omitted',href='evidence/omitted.pdb')]
        data = dict(findings=rows,headline_findings=rows[:2],secondary_findings=rows[2:3],
                    highlighted_findings=rows[:3],reports=[],figures=[],structures=structures,
                    omitted_structures=omitted,presentation_artifacts=[
                        dict(s,artifact_type='structure') for s in structures+omitted])
        selections = [dict(search='',tier='headline',category='',system=''),
                      dict(search='dihedral'), dict(search='__absent__'), dict(search=''),
                      dict(tier='',system='A'),dict(category='rmsf'),dict(system='B'),
                      dict(tier='secondary'),dict(tier='',category='',system='')]
        result = subprocess.run([node, str(Path(__file__).with_name('viewer_actions.cjs'))],
            input=json.dumps(dict(data=data,js=_JS,selections=selections)), text=True,
            capture_output=True,check=True,timeout=30)
        result = json.loads(result.stdout)
        self.assertEqual([s['count'] for s in result['states']], [2,1,0,2,2,1,1,0,4])
        self.assertTrue(result['data_unchanged'])
