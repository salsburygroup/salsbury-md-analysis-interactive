// Execute the shipped handlers without a browser. CSS/layout needs separate QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8')),data=input.data,controls={};
const decode=s=>s.replace(/&(amp|lt|gt|quot|#39);/g,(_,k)=>({amp:'&',lt:'<',gt:'>',quot:'"','#39':"'"}[k]));
class Element {
  constructor(id){this.id=id;this.value='';this.rows=[];this.dataset={};}
  set innerHTML(text){this.html=text;if(this.id==='finding-tier')this.value='headline';
    if(this.id==='findings-list')this.rows=[...text.matchAll(/<div class="finding" ([^>]*)>/g)].map(m=>{
      const dataset={};for(const a of m[1].matchAll(/data-(\w+)="([^"]*)"/g))dataset[a[1]]=decode(a[2]);return {dataset,hidden:false};});}
  get innerHTML(){return this.html||'';}
  querySelectorAll(s){return s==='.finding'?this.rows:[];}
}
const document={getElementById:id=>id==='report-data'?{textContent:JSON.stringify(data)}:controls[id],
  querySelector:s=>controls[s.slice(1)]??=new Element(s.slice(1)),querySelectorAll:()=>[]};
const context=vm.createContext({document});
const boundary=input.js.lastIndexOf('\nrenderAnalysisTabs();');assert.ok(boundary>0);
vm.runInContext(input.js.slice(0,boundary),context);
const originalData=vm.runInContext('JSON.stringify(DATA)',context);
vm.runInContext('renderFindings()',context);
const states=[];
for(const selection of input.selections){
  for(const [id,value] of Object.entries(selection))controls['finding-'+id].value=value;
  controls['finding-search'].oninput();
  const expected=data.findings.map((f,i)=>({f,i})).filter(({f})=>{
    const c=id=>controls['finding-'+id].value;
    return (!c('search')||JSON.stringify(f).toLowerCase().includes(c('search').toLowerCase()))&&
      (!c('tier')||(f.presentation_tier||'headline')===c('tier'))&&
      (!c('category')||f.category.replace(/_+/g,' ')===c('category'))&&
      (!c('system')||(f.system_ids||[]).includes(c('system')));
  }).map(({i})=>i);
  const selected=controls['findings-list'].rows.flatMap((r,i)=>r.hidden?[]:[i]);
  assert.deepEqual(selected,expected);states.push({selection,count:selected.length});
}
assert.equal(controls['findings-list'].rows.length,data.findings.length);
context.calls=[];
vm.runInContext("go=(view)=>calls.push(['go',view]);loadStructure=(index)=>calls.push(['load',index]);",context);
document.body={dataset:{view:'analysis-free-energy'}};
context.location={hash:'#analysis-free-energy'};
vm.runInContext('routeHash()',context);
assert.equal(context.calls.length,0,'hashchange must not reset a same-view artifact jump');
context.location.hash='#findings';
vm.runInContext('routeHash()',context);
assert.equal(context.calls.at(-1)[1],'findings','back/forward navigation still changes view');
context.displayAtoms=[{resn:'GUA',serial:1,x:1,y:2,z:3},{resn:'EDU',serial:2},
  {resn:'ALA',serial:3},{resn:'K',serial:4,hetflag:true}];
vm.runInContext('prepareDisplayAtoms({selectedAtoms:()=>displayAtoms})',context);
assert.equal(context.displayAtoms[0].resn,'G');
assert.equal(context.displayAtoms[0].sourceResn,'GUA');
assert.equal(context.displayAtoms[0].x,1);
assert.equal(context.displayAtoms[1].resn,'EDU','do not invent a modified-residue alias');
vm.runInContext('prepareDisplayAtoms({selectedAtoms:()=>displayAtoms})',context);
assert.equal(context.displayAtoms[0].sourceResn,'GUA','display normalization is idempotent');
context.styleCalls=[];
vm.runInContext("molecular.model={selectedAtoms:()=>displayAtoms};molecular.viewer={setStyle:(selection,style)=>styleCalls.push({selection,style}),selectedAtoms:()=>displayAtoms,render:()=>{},zoomTo:()=>{}};$('#viewer-representation').value='overview';$('#viewer-color').value='chain';$('#viewer-search').value='';applyMolecularStyle();",context);
const fallback=context.styleCalls.find(c=>Array.isArray(c.selection.serial));
assert.deepEqual(Array.from(fallback.selection.serial),[2,4],'modified ATOM residues and hetero atoms get bonded fallback');
assert.ok(fallback.style.stick);
vm.runInContext('molecular.viewer=null;molecular.model=null',context);
const actions=[];
for(const artifact of data.presentation_artifacts.filter(a=>a.artifact_type==='structure')){
  context.artifact=artifact;
  const inline=data.structures.some(s=>s.structure_id===artifact.structure_id);
  const outputs=vm.runInContext('[structureAction(artifact),artifactCard(artifact),findingActions({resolved_presentation_artifacts:[artifact]}),representativeLinks({representative_structures:[artifact]})]',context);
  for(const html of outputs){if(inline)assert.ok(html.includes('data-structure-id='));else{assert.ok(html.includes('Open representative PDB (not embedded)'));assert.ok(!html.includes('data-structure-id='));assert.ok(!html.includes('<canvas'));}}
  vm.runInContext('openStructure(artifact.structure_id)',context);
  if(inline)assert.equal(context.calls.at(-1)[0],'load');else assert.ok(controls['structure-title'].innerHTML.includes('not embedded'));
  actions.push({id:artifact.structure_id,inline});
}
vm.runInContext("openStructure('unknown-structure')",context);
assert.equal(controls['structure-title'].innerHTML,'Representative structure file unavailable.');
assert.equal(vm.runInContext('JSON.stringify(DATA)',context),originalData);
console.log(JSON.stringify({states,actions,candidate_count:data.findings.length,data_unchanged:true}));
