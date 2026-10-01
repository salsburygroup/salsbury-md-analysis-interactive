"""Optional, offline molecular figure rendering from explicitly selected PDBs."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import shutil
from pathlib import Path


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_spec(path):
    path = Path(path).resolve()
    spec = json.loads(path.read_text())
    if spec.get("schema") != "salsbury-molecular-panel-v1":
        raise ValueError("Expected salsbury-molecular-panel-v1")
    if not isinstance(spec.get("panels"), list) or not 1 <= len(spec["panels"]) <= 4:
        raise ValueError("Supply one to four coordinate panels")
    for key in ("title", "caption", "alignment_description"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError(f"Missing {key}")
    if not isinstance(spec.get('zoom', 1), (int, float)) or not 0.25 <= spec.get('zoom', 1) <= 3:
        raise ValueError('Zoom must be between 0.25 and 3')
    if not isinstance(spec.get('panel_height', 380), int) or not 240 <= spec.get('panel_height', 380) <= 800:
        raise ValueError('Panel height must be 240–800 pixels')
    if not isinstance(spec.get('panel_width', 480), int) or not 320 <= spec.get('panel_width', 480) <= 800:
        raise ValueError('Panel width must be 320–800 pixels')
    for panel in spec["panels"]:
        if not isinstance(panel, dict) or not isinstance(panel.get("label"), str) or not panel["label"].strip():
            raise ValueError("Each panel needs a label")
        source = (path.parent / panel["pdb_path"]).resolve()
        if source.stat().st_size > 50_000_000:
            raise ValueError("PDB exceeds the 50-MB illustration limit")
        if _sha(source) != panel["pdb_sha256"]:
            raise ValueError("Coordinate hash mismatch")
        atoms = []
        for line in source.read_text().splitlines():
            if line.startswith(("ATOM  ", "HETATM")):
                xyz = [float(line[i:i+8]) for i in (30, 38, 46)]
                if not all(math.isfinite(x) for x in xyz):
                    raise ValueError("Non-finite coordinates")
                atoms.append({"serial": int(line[6:11]), "chain": line[21:22].strip(),
                              "resi": int(line[22:26]), "atom": line[12:16].strip(),
                              "element": line[76:78].strip().upper()})
        if not atoms or sum(line.startswith("MODEL ") for line in source.read_text().splitlines()) > 1:
            raise ValueError("Each panel needs one sampled coordinate model")
        if not panel.get("selection_rule") or not isinstance(panel.get("source_identity"), dict):
            raise ValueError("Record the selection rule and sampled source identity")
        for key in ("system_id", "replica_id", "segment_id", "source_frame_index"):
            if key not in panel["source_identity"]:
                raise ValueError(f"Missing source identity: {key}")
        frame = panel["source_identity"]["source_frame_index"]
        if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
            raise ValueError("Source frame index must be a nonnegative integer")
        for highlight in panel.get("highlights", []):
            selection = highlight["selection"]
            if not selection or set(selection) - {"serial", "chain", "resi", "atom"}:
                raise ValueError("Unsupported highlight selection")
            if not any(all(atom.get(k) == value for k, value in selection.items()) for atom in atoms):
                raise ValueError("Highlighted atom/residue is absent from the sampled structure")
        ion_serials = {a["serial"] for a in atoms if a["element"] in {"K","NA","MG","CA","CL","ZN","FE","MN","CU"}}
        if any(value not in ion_serials for value in panel.get("visible_ion_serials", [])):
            raise ValueError("Requested visible ion is absent or not an ion")
        if panel.get("atom_values"):
            if not spec.get("color_range") or len(spec["color_range"]) != 2:
                raise ValueError("Scalar-colored panels require a shared color range")
            if not all(math.isfinite(float(v)) for v in spec["color_range"]) or spec["color_range"][0] >= spec["color_range"][1]:
                raise ValueError("Shared color range must be finite and increasing")
            for row in panel["atom_values"]:
                if not math.isfinite(float(row["value"])) or row["serial"] not in {a["serial"] for a in atoms}:
                    raise ValueError("Invalid scalar value or unmatched atom")
        panel["pdb_path"] = str(source)
    return spec


SCRIPT = r"""
const viewers=[],counts=[];
const water=['HOH','WAT','TIP3','TIP3P','SOL'];
const ions=['K','NA','MG','CA','CL','ZN','FE','MN','CU'];
const aliases={GUA:'DG',ADE:'DA',CYT:'DC',THY:'DT',URA:'U'};
const protein=['ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE','LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL'];
SPEC.panels.forEach((panel,i)=>{
 const viewer=$3Dmol.createViewer(document.getElementById('mol-'+i),{backgroundColor:'#ffffff',antialias:true});
 const model=viewer.addModel(panel.pdb_text,'pdb',{keepH:true});
 const atoms=model.selectedAtoms({});
 // Display aliases enable nucleic-acid cartoons; source names and PDB bytes remain intact.
 atoms.forEach(a=>{if(aliases[a.resn])a.resn=aliases[a.resn]});
 viewer.setStyle({},{stick:{radius:.12,color:'#b7b5af'}});
 viewer.addStyle({resn:protein},{cartoon:{style:'rectangle',arrows:true,thickness:.4,color:'#CEB888'}});
 viewer.addStyle({resn:['DA','DG','DC','DT','A','G','C','U']},{cartoon:{color:'#CEB888',thickness:.3}});
 if(panel.atom_values){const colors=new Map(panel.atom_values.map(a=>[a.serial,a.value]));
  const lo=SPEC.color_range[0],hi=SPEC.color_range[1];
  panel.atom_values.forEach(v=>{const t=Math.min(1,Math.max(0,(v.value-lo)/(hi-lo)));
   const rgb=[206,184,136].map((x,j)=>Math.round(x+([156,47,47][j]-x)*t));
   const color='#'+rgb.map(x=>x.toString(16).padStart(2,'0')).join('');
   viewer.addStyle({serial:v.serial},{sphere:{radius:.65,color}});
  });
 }
 panel.highlights?.forEach(h=>{
  viewer.addStyle(h.selection,{stick:{radius:.24,color:h.color||'#9C2F2F'}});
  const selected=viewer.selectedAtoms(h.selection),a=selected.find(a=>a.atom==="C1'"||a.atom==='CA')||selected[0];
  viewer.addLabel(h.label,{position:{x:a.x+1.5,y:a.y+1.5,z:a.z},fontColor:h.color||'#9C2F2F',backgroundColor:'#ffffff',backgroundOpacity:.8,fontSize:14,inFront:true});
 });
 // Mobile ions are hidden unless an explicit state-specific list was supplied.
 ions.forEach(elem=>viewer.setStyle({elem},{}));
 (panel.visible_ion_serials||[]).forEach(serial=>viewer.setStyle({serial},{sphere:{scale:.65,color:'#53565A'}}));
 water.forEach(resn=>viewer.setStyle({resn},{}));viewer.setStyle({elem:'H'},{});
 viewers.push(viewer);counts.push(atoms.length);
});
// Use one camera fitted to the union of the already-aligned displayed structures.
const reference=viewers[0],temporary=[];
SPEC.panels.slice(1).forEach(p=>temporary.push(reference.addModel(p.pdb_text,'pdb',{keepH:true})));
temporary.forEach(m=>m.setStyle({},{}));
// Hidden mobile ions must not shrink the macromolecule to a dot in the view.
reference.zoomTo({and:[{not:{elem:ions}},{not:{resn:water}},{not:{elem:'H'}}]});
reference.rotate(25,'y');reference.rotate(-12,'x');
reference.zoom(SPEC.zoom||1);
const commonView=reference.getView();temporary.forEach(m=>reference.removeModel(m));
viewers.forEach(v=>{v.setView(commonView);v.render()});
window.PANEL_RENDER={atom_counts:counts,common_view:commonView,renderer:'3Dmol.js',complete:true};
"""


def render_panels(spec_path, output, *, browser_channel=None):
    """Render PNG + a reopenable offline view; never choose frames or fit states."""
    from playwright.sync_api import sync_playwright
    spec = load_spec(spec_path)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    spec_path = Path(spec_path).resolve()
    for i, panel in enumerate(spec["panels"]):
        destination = output / f"structure-{i+1}.pdb"
        shutil.copy2(panel["pdb_path"], destination)
        panel["pdb_path"] = destination.name
        panel["pdb_text"] = destination.read_text()
    vendor = Path(__file__).with_name("vendor") / "3Dmol-min.js"
    columns = min(2, len(spec["panels"]))
    panel_width = spec.get('panel_width', 480)
    content = ''.join(f'<section><h2>{html.escape(p["label"])}</h2><div class="mol" id="mol-{i}"></div>'
                      f'<p>{html.escape(p.get("display_note", ""))}</p></section>' for i,p in enumerate(spec["panels"]))
    legend = ''
    if spec.get("color_range"):
        legend = f'<p class="legend">{html.escape(spec.get("color_label", "Value"))}: '
        legend += f'{spec["color_range"][0]:g} <span></span> {spec["color_range"][1]:g}</p>'
    encoded = json.dumps(spec).replace('<', '\u003c')
    provenance = '<aside style="padding:20px;max-width:1000px"><p>'+html.escape(spec['caption'])+'</p><p>'+html.escape(spec['alignment_description'])+'</p>'
    for i,panel in enumerate(spec['panels']):
        identity = panel['source_identity']
        description = ' / '.join(str(identity[k]) for k in ('system_id','replica_id','segment_id')) + f" / frame {identity['source_frame_index']} (zero-based)"
        provenance += f'<p><a href="structure-{i+1}.pdb">{html.escape(panel["label"])}</a>: {html.escape(description)}. {html.escape(panel["selection_rule"])}</p>'
    provenance += '</aside>'
    text = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+html.escape(spec['title'])+'</title>'
            '<style>body{font:18px Arial;margin:0;color:#000;background:#fff}h1{font-size:25px;border-bottom:4px solid #9E7E38;padding:16px;margin:0}'
            f'.grid{{display:grid;grid-template-columns:repeat({columns},{panel_width}px)}}'
            'h2{font-size:20px;margin:12px 20px}section p{margin:8px 20px;font-size:16px}'
            f'.mol{{width:{panel_width}px;height:{spec.get("panel_height",380)}px;position:relative}}'
            '.legend{padding:0 20px}.legend span{display:inline-block;width:180px;height:15px;background:linear-gradient(to right,#CEB888,#9C2F2F)}</style>'
            '<div id="figure"><h1>'+html.escape(spec['title'])+'</h1><div class="grid">'+content+'</div>'+legend+'</div>'+provenance+
            '<script>'+vendor.read_text()+'</script><script>const SPEC='+encoded+';'+SCRIPT+'</script></html>')
    page_path = output / 'view.html'
    page_path.write_text(text)
    errors = []
    with sync_playwright() as playwright:
        kwargs = {'headless': True}
        if browser_channel:
            kwargs['channel'] = browser_channel
        browser = playwright.chromium.launch(**kwargs)
        try:
            page = browser.new_page(viewport={'width': columns*panel_width, 'height': 2200}, device_scale_factor=2)
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.route('http://**/*', lambda route: route.abort())
            page.route('https://**/*', lambda route: route.abort())
            page.goto(page_path.as_uri())
            page.wait_for_function('window.PANEL_RENDER && PANEL_RENDER.complete')
            evidence = page.evaluate('PANEL_RENDER')
            if errors:
                raise ValueError('; '.join(errors))
            page.locator('#figure').screenshot(path=str(output/'figure.png'))
        finally:
            browser.close()
    for panel in spec['panels']:
        panel.pop('pdb_text')
    evidence.update({'schema':'salsbury-molecular-render-v1', 'spec':spec,
                     'figure_sha256':_sha(output/'figure.png'), 'saved_view_sha256':_sha(page_path),
                     'vendor_sha256':_sha(vendor), 'network_requests_allowed':False,
                     'scientific_calculations_performed':False})
    (output/'render.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return evidence


def molecular_evidence_metadata(render_directory, finding, coordinate_ids, saved_view_id):
    """Build a core-manifest binding after checking every renderer output.

    The caller registers/copies the files in its reporting workspace; this
    helper never mutates an accepted campaign or selects a scientific frame.
    """
    from salsbury_md_analysis.molecular_evidence import finding_signature
    root = Path(render_directory)
    evidence = json.loads((root / 'render.json').read_text())
    if evidence.get('schema') != 'salsbury-molecular-render-v1' or not evidence.get('complete'):
        raise ValueError('Molecular render is incomplete')
    panels = evidence['spec']['panels']
    if len(coordinate_ids) != len(panels) or len(set(coordinate_ids)) != len(panels):
        raise ValueError('Supply one unique coordinate artifact ID per panel')
    for filename, expected in [('figure.png', evidence['figure_sha256']), ('view.html', evidence['saved_view_sha256'])]:
        if _sha(root / filename) != expected:
            raise ValueError('Rendered artifact hash mismatch')
    for panel in panels:
        path = (root / panel['pdb_path']).resolve()
        if not path.is_relative_to(root.resolve()) or _sha(path) != panel['pdb_sha256']:
            raise ValueError('Rendered coordinate hash mismatch')
    return {'finding_signature_sha256': finding_signature(finding),
            'coordinate_artifacts': [{'artifact_id': aid, 'sha256': panel['pdb_sha256']}
                                     for aid,panel in zip(coordinate_ids,panels)],
            'saved_view_artifact_id': saved_view_id,
            'saved_view_sha256': evidence['saved_view_sha256']}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Render saved, aligned PDBs as an offline molecular figure.')
    parser.add_argument('spec', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--browser-channel', help='Use an installed browser, e.g. chrome; default is Playwright Chromium')
    args = parser.parse_args(argv)
    try:
        result = render_panels(args.spec,args.output,browser_channel=args.browser_channel)
    except (OSError,ValueError,ImportError) as error:
        parser.exit(2,f'Molecular figure failed: {error}\n')
    print(json.dumps({k:v for k,v in result.items() if k!='spec'},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
