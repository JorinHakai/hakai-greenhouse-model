"""Wrap the built GLB into a single self-contained viewer HTML.

The geometry is embedded as base64, so the output works from disk, from
email, or hosted, with no side-car files.  three.js comes from a CDN.

Because the viewer is generated from the same GLB the build produces, it can
never drift out of step with the model -- there is no second copy of the
geometry to keep in sync.

    python gh_build.py --noholes && python gh_viewer.py
    ->  greenhouse_viewer.html   (also copied to index.html)

The template below uses __TOKEN__ placeholders rather than an f-string, so
none of the CSS or JavaScript braces need escaping.
"""
import base64, json, os, shutil, sys

GLB = sys.argv[1] if len(sys.argv) > 1 else (
    "greenhouse_web.glb" if os.path.exists("greenhouse_web.glb") else "greenhouse.glb")
OUT = "greenhouse_viewer.html"

def raw_extents(path):
    """Bounding extents straight from the GLB POSITION accessors, in mm.

    This is vertex space, before any node transform, where the model is
    x = width, y = height, z = length by construction.  The viewer compares
    the extents it measures *after* applying node transforms against these,
    so a stray root rotation (cadquery has shipped one) is caught instead of
    silently standing the building on its end.
    """
    raw = open(path, "rb").read()
    jlen = int.from_bytes(raw[12:16], "little")
    gj = json.loads(raw[20:20+jlen])
    mn = [1e18]*3; mx = [-1e18]*3
    for a in gj["accessors"]:
        if a.get("type") == "VEC3" and len(a.get("min", [])) == 3:
            for k in range(3):
                mn[k] = min(mn[k], a["min"][k]); mx[k] = max(mx[k], a["max"][k])
    return [round(mx[k]-mn[k], 3) for k in range(3)]


blob = base64.b64encode(open(GLB, "rb").read()).decode("ascii")
EXP = raw_extents(GLB)
man = json.load(open("manifest.json")) if os.path.exists("manifest.json") else {}
try:
    rep = json.load(open("verification_report.json"))
    npass = sum(1 for r in rep["dimensional"] if r["pass"])
    ntot = len(rep["dimensional"])
    nfail = rep.get("failures", 0)
    checks = f"{npass}/{ntot} dimensional checks pass &middot; {nfail} failures"
except Exception:
    checks = "see verification_report.json"

nsolids = sum(man.values()) if man else 0
rows = "".join(f"<tr><td>{v}</td><td>{k}</td></tr>"
               for k, v in sorted(man.items(), key=lambda kv: (-kv[1], kv[0])))

TEMPLATE = r"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Greenhouse digital twin</title>
<style>
  :root[data-theme="light"]{
    --bg:#eef1f4; --panel:rgba(255,255,255,.86); --line:#c9d2db;
    --ink:#1b2733; --dim:#5d6b7a; --accent:#0b6fa4; --ok:#0e7a52;
    --btn:#ffffff; --btnh:#e8eef4; --shadow:0 2px 14px rgba(22,38,54,.13);
  }
  :root[data-theme="dark"]{
    --bg:#11151a; --panel:rgba(18,23,29,.90); --line:#2b3540;
    --ink:#e7edf3; --dim:#8fa3b6; --accent:#6fc4f2; --ok:#7fd6a2;
    --btn:#1d2530; --btnh:#26313e; --shadow:0 2px 14px rgba(0,0,0,.45);
  }
  html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);
    font:13px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    overflow:hidden;transition:background .25s,color .25s}
  #cv{position:fixed;inset:0;display:block}
  .panel{position:fixed;background:var(--panel);backdrop-filter:blur(9px);
    border:1px solid var(--line);border-radius:11px;padding:12px 14px;
    box-shadow:var(--shadow)}
  #hud{top:12px;left:12px;max-width:292px}
  #hud h1{font-size:15px;margin:0 0 5px}
  #hud dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:9px 0 0}
  #hud dt{color:var(--dim)} #hud dd{margin:0;font-variant-numeric:tabular-nums}
  #ctl{top:12px;right:12px;display:flex;flex-direction:column;gap:6px;
    width:186px;max-height:calc(100vh - 24px);overflow:auto}
  #ctl label{display:flex;gap:8px;align-items:center;cursor:pointer;
    white-space:nowrap}
  #ctl .sec{color:var(--dim);text-transform:uppercase;letter-spacing:.07em;
    font-size:10.5px;margin-top:6px;border-top:1px solid var(--line);
    padding-top:6px}
  #ctl .sec:first-child{border-top:0;margin-top:0}
  button{background:var(--btn);color:var(--ink);border:1px solid var(--line);
    border-radius:7px;padding:5px 9px;cursor:pointer;font:inherit;font-size:12px}
  button:hover{background:var(--btnh)}
  button.on{border-color:var(--accent);color:var(--accent)}
  .row{display:flex;gap:6px}
  .row button{flex:1}
  input[type=range]{width:100%;accent-color:var(--accent)}
  select{width:100%;background:var(--btn);color:var(--ink);font:inherit;
    font-size:12px;border:1px solid var(--line);border-radius:7px;padding:4px}
  #man{bottom:12px;left:12px;max-height:40vh;overflow:auto;display:none}
  #man table{border-collapse:collapse;font-size:11.5px}
  #man td{padding:1px 8px 1px 0;vertical-align:top}
  #man td:first-child{text-align:right;color:var(--accent);
    font-variant-numeric:tabular-nums}
  #tip{bottom:12px;right:12px;color:var(--dim);font-size:11.5px;
    max-width:330px;text-align:right}
  #load{position:fixed;inset:0;display:grid;place-items:center;
    background:var(--bg);z-index:9;font-size:14px;color:var(--dim)}
  kbd{font:11px ui-monospace,monospace;border:1px solid var(--line);
    border-bottom-width:2px;border-radius:4px;padding:0 4px;color:var(--ink)}
</style>
</head>
<body>
<canvas id="cv"></canvas>
<div id="load">loading geometry&hellip;</div>

<div class="panel" id="hud">
  <h1>Greenhouse digital twin</h1>
  <div style="color:var(--dim)">Curved-eave gable greenhouse.<br>
  Dimension-accurate starting point for interior fit-out.</div>
  <dl>
    <dt>Width</dt><dd>20&#8242;-6&#188;&#8243;</dd>
    <dt>Length</dt><dd>51&#8242;-3&#188;&#8243;</dd>
    <dt>Ridge</dt><dd>10&#8242;-2&#8542;&#8243;</dd>
    <dt>Pitch</dt><dd>23.1&deg;</dd>
    <dt>Trusses</dt><dd>4</dd>
    <dt>Solids</dt><dd>__NSOLIDS__</dd>
    <dt>Heading</dt><dd><span id="az">--</span>&deg;</dd>
  </dl>
  <div style="margin-top:8px;color:var(--ok)">__CHECKS__</div>
</div>

<div class="panel" id="ctl">
  <div class="sec">Theme</div>
  <div class="row">
    <button id="tLight" class="on">Light</button>
    <button id="tDark">Dark</button>
  </div>

  <div class="sec">Spin</div>
  <div class="row">
    <button id="spinL" title="Rotate 30&deg; left (Left arrow)">&#9664;</button>
    <button id="spinR" title="Rotate 30&deg; right (Right arrow)">&#9654;</button>
  </div>
  <label><input type="checkbox" id="cSpin"> Auto-rotate <kbd>space</kbd></label>
  <select id="spinAxis" title="Which axis auto-rotate turns about">
    <option value="v">about vertical (walk around)</option>
    <option value="z">about long axis (roll)</option>
  </select>
  <input type="range" id="spinSpeed" min="1" max="30" value="8"
         title="Spin speed">

  <div class="sec">View</div>
  <div class="row"><button id="vIso">Iso</button><button id="vEnd">End</button></div>
  <div class="row"><button id="vSide">Side</button><button id="vTop">Plan</button></div>
  <button id="vInside">Interior</button>
  <button id="vTruss">Truss bay</button>
  <button id="vReset">Reset <kbd>r</kbd></button>

  <div class="sec">Show</div>
  <label><input type="checkbox" id="cFrame" checked> Frame</label>
  <label><input type="checkbox" id="cGlass" checked> Glazing</label>
  <label><input type="checkbox" id="cEdge"> Edges</label>
  <label><input type="checkbox" id="cGrid" checked> Ground grid</label>
  <button id="bMan">Member list</button>
</div>

<div class="panel" id="man"><table>__ROWS__</table></div>
<div class="panel" id="tip">
  drag orbit &middot; scroll zoom &middot; right-drag pan &middot;
  <kbd>&larr;</kbd><kbd>&rarr;</kbd> spin &middot; <kbd>&uarr;</kbd><kbd>&darr;</kbd> tilt
</div>

<script type="importmap">
{"imports":{
  "three":"https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"
}}
</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const B64="__BLOB__";
const bin=Uint8Array.from(atob(B64),c=>c.charCodeAt(0)).buffer;

/* ---------------------------------------------------------------- themes */
const THEMES={
  light:{bg:0xeef1f4, fogNear:22, fogFar:80,
         frame:0x98a3ae, frameMetal:.80, frameRough:.33, frameEnv:1.05,
         glass:0x9ec6e4, glassOp:.16,
         grid1:0xbcc6d1, grid2:0xd6dee6,
         hemiSky:0xffffff, hemiGnd:0xc4ccd4, hemiI:.55,
         sunI:2.0, fillI:.55, envI:1.1, edge:0x64707c, toneExp:1.05},
  dark: {bg:0x11151a, fogNear:24, fogFar:88,
         frame:0xd7dee6, frameMetal:.75, frameRough:.34, frameEnv:.85,
         glass:0xbcd9ee, glassOp:.19,
         grid1:0x2c3742, grid2:0x1b2229,
         hemiSky:0xdfefff, hemiGnd:0x2a2f36, hemiI:.9,
         sunI:1.6, fillI:.5, envI:.55, edge:0x35424f, toneExp:1.0}
};
let theme='light';

/* ---------------------------------------------------------------- scene */
const cv=document.getElementById('cv');
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;

const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(45,1,0.02,600);

const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;
controls.dampingFactor=0.085;
controls.rotateSpeed=0.85;
controls.zoomSpeed=0.9;
controls.panSpeed=0.75;
controls.minDistance=0.8;
controls.maxDistance=85;
// Never let the camera reach either pole: at the pole the azimuth is
// degenerate and horizontal dragging stops doing anything predictable,
// which is what made spinning feel stuck.
controls.minPolarAngle=0.09;
controls.maxPolarAngle=Math.PI*0.62;

const hemi=new THREE.HemisphereLight(0xffffff,0x888888,1);
scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffffff,1.8);
sun.position.set(9,16,7); scene.add(sun);
const fill=new THREE.DirectionalLight(0xffffff,.5);
fill.position.set(-10,6,-12); scene.add(fill);

const pmrem=new THREE.PMREMGenerator(renderer);
const envTex=pmrem.fromScene(new RoomEnvironment(),0.04).texture;
scene.environment=envTex;

const grid=new THREE.GridHelper(34,34);
scene.add(grid);

// pivot carries the model so "roll about the long axis" can rotate the
// building without dragging the ground grid round with it
const pivot=new THREE.Group(); scene.add(pivot);
const frameGrp=new THREE.Group(), glassGrp=new THREE.Group();
pivot.add(frameGrp,glassGrp);
let edges=null;

const matFrame=new THREE.MeshStandardMaterial({});
const matGlass=new THREE.MeshPhysicalMaterial({
  transparent:true, transmission:.72, roughness:.14, metalness:0,
  side:THREE.DoubleSide, depthWrite:false});

function applyTheme(){
  const t=THEMES[theme];
  document.documentElement.setAttribute('data-theme',theme);
  scene.background=new THREE.Color(t.bg);
  scene.fog=new THREE.Fog(t.bg,t.fogNear,t.fogFar);
  matFrame.color.setHex(t.frame);
  matFrame.metalness=t.frameMetal;
  matFrame.roughness=t.frameRough;
  matFrame.envMapIntensity=t.frameEnv;
  matFrame.needsUpdate=true;
  matGlass.color.setHex(t.glass);
  matGlass.opacity=t.glassOp;
  matGlass.envMapIntensity=t.frameEnv;
  matGlass.needsUpdate=true;
  hemi.color.setHex(t.hemiSky); hemi.groundColor.setHex(t.hemiGnd);
  hemi.intensity=t.hemiI; sun.intensity=t.sunI; fill.intensity=t.fillI;
  renderer.toneMappingExposure=t.toneExp;
  grid.material.color.setHex(t.grid1);
  grid.material.opacity=theme==='light'?.38:.8;
  grid.material.transparent=true;
  if(edges) edges.traverse(o=>{if(o.material)o.material.color.setHex(t.edge);});
  document.getElementById('tLight').classList.toggle('on',theme==='light');
  document.getElementById('tDark').classList.toggle('on',theme==='dark');
  try{localStorage.setItem('ghTheme',theme);}catch(e){}
}
try{const s=localStorage.getItem('ghTheme'); if(s)theme=s;}catch(e){}

/* ---------------------------------------------------------------- load */
let SZ=new THREE.Vector3(6.26,3.12,15.63);   // metres, from the GLB bounds

// Extents in the GLB's own vertex space, mm: width, height, length.
const EXPECT=[__EXPW__,__EXPH__,__EXPL__];

function reorient(geoms){
  /* Guard against a node transform having permuted the axes.  cadquery
     writes a Z-up -> Y-up root rotation, which is wrong for a model that
     is authored Y-up and stands the 615" length vertically.  gh_build.py
     strips that rotation, but this check means a future exporter change
     cannot silently break the viewer again.  The three extents are all
     distinct, so matching measured to expected is unambiguous. */
  const box=new THREE.Box3().makeEmpty();
  geoms.forEach(g=>{g.computeBoundingBox();box.union(g.boundingBox);});
  const s=box.getSize(new THREE.Vector3()).toArray();
  const used=[false,false,false];
  const pick=e=>{let bi=-1,bd=Infinity;
    for(let i=0;i<3;i++){if(used[i])continue;
      const d=Math.abs(s[i]-e); if(d<bd){bd=d;bi=i;}}
    used[bi]=true; return bi;};
  const idx=[pick(EXPECT[0]),pick(EXPECT[1]),pick(EXPECT[2])];
  if(idx[0]===0&&idx[1]===1&&idx[2]===2) return 'identity';
  const e=[new THREE.Vector3(1,0,0),new THREE.Vector3(0,1,0),
           new THREE.Vector3(0,0,1)];
  let r0=e[idx[0]].clone(), r1=e[idx[1]].clone(), r2=e[idx[2]].clone();
  const m=new THREE.Matrix4().set(r0.x,r0.y,r0.z,0,
                                  r1.x,r1.y,r1.z,0,
                                  r2.x,r2.y,r2.z,0, 0,0,0,1);
  if(m.determinant()<0){                 // keep it a rotation, not a mirror
    r0.negate();
    m.set(r0.x,r0.y,r0.z,0, r1.x,r1.y,r1.z,0, r2.x,r2.y,r2.z,0, 0,0,0,1);
  }
  geoms.forEach(g=>g.applyMatrix4(m));
  return 'corrected axes ['+idx.join(',')+']';
}

new GLTFLoader().parse(bin,'',gltf=>{
  const root=gltf.scene; root.updateMatrixWorld(true);
  const geoms=[], flags=[];
  root.traverse(o=>{
    if(!o.isMesh) return;
    const g=o.geometry.clone(); g.applyMatrix4(o.matrixWorld);
    // cadquery exports the glazing shell with baseColorFactor alpha < 1
    const a=(o.material&&o.material.opacity!==undefined)?o.material.opacity:1;
    geoms.push(g); flags.push(a<0.9);
  });
  window.__orient=reorient(geoms);
  geoms.forEach((g,i)=>{
    ((flags[i])?glassGrp:frameGrp).add(
      new THREE.Mesh(g,flags[i]?matGlass:matFrame));
  });

  const box=new THREE.Box3().makeEmpty();
  [frameGrp,glassGrp].forEach(g=>box.expandByObject(g));
  const c=box.getCenter(new THREE.Vector3());
  const s=1/1000;                                  // mm -> m
  [frameGrp,glassGrp].forEach(g=>{
    g.position.set(-c.x*s,-box.min.y*s,-c.z*s);
    g.scale.setScalar(s);
  });
  SZ=box.getSize(new THREE.Vector3()).multiplyScalar(s);
  grid.position.y=0;
  applyTheme();
  document.getElementById('load').style.display='none';
  setView('iso');
},err=>{
  document.getElementById('load').textContent='could not load geometry: '+err;
});

/* ------------------------------------------------------- view presets */
// azimuth 0 looks down +Z (the long axis); 90deg looks down +X (broadside)
const VIEWS={
  iso:   {az:38,  pol:66, d:1.08, ty:.42},
  end:   {az:5,   pol:80, d:0.88, ty:.42},
  side:  {az:90,  pol:78, d:0.80, ty:.45},
  top:   {az:90,  pol:12, d:1.00, ty:.35},   // 12deg off the pole, not 0
  inside:{az:6,   pol:88, d:0.20, ty:.55},
  truss: {az:62,  pol:74, d:0.26, ty:.72}
};
function setView(k,animate){
  const v=VIEWS[k]; if(!v) return;
  const reach=Math.max(SZ.x,SZ.z);
  const tgt=new THREE.Vector3(0,SZ.y*v.ty,0);
  const r=reach*v.d;
  const sph=new THREE.Spherical(r,
    THREE.MathUtils.degToRad(v.pol), THREE.MathUtils.degToRad(v.az));
  sph.makeSafe();
  const pos=new THREE.Vector3().setFromSpherical(sph).add(tgt);
  controls.target.copy(tgt);
  camera.position.copy(pos);
  controls.update();
}
for(const [id,k] of [['vIso','iso'],['vEnd','end'],['vSide','side'],
                     ['vTop','top'],['vInside','inside'],['vTruss','truss']])
  document.getElementById(id).onclick=()=>setView(k);
document.getElementById('vReset').onclick=()=>{
  pivot.rotation.z=0; grid.visible=document.getElementById('cGrid').checked;
  setView('iso');
};

/* ---------------------------------------------------------------- spin */
// Step the azimuth with a short tween so the direction of travel is obvious.
let tween=null;
function nudge(deg){
  const from=controls.getAzimuthalAngle();
  const to=from+THREE.MathUtils.degToRad(deg);
  tween={from,to,t0:performance.now(),ms:420};
}
document.getElementById('spinL').onclick=()=>nudge(-30);
document.getElementById('spinR').onclick=()=>nudge(30);

const cSpin=document.getElementById('cSpin');
const spinAxis=document.getElementById('spinAxis');
const spinSpeed=document.getElementById('spinSpeed');
function spinState(){
  const on=cSpin.checked, axis=spinAxis.value;
  controls.autoRotate = on && axis==='v';
  controls.autoRotateSpeed = spinSpeed.value/5;
  // rolling the building through the ground plane looks wrong, so the grid
  // steps aside while a long-axis roll is running
  grid.visible=document.getElementById('cGrid').checked &&
               !(on && axis==='z');
  if(!(on&&axis==='z')) { /* leave any existing roll in place */ }
}
cSpin.onchange=spinState; spinAxis.onchange=spinState;
spinSpeed.oninput=spinState;

/* -------------------------------------------------------------- toggles */
document.getElementById('cFrame').onchange=e=>frameGrp.visible=e.target.checked;
document.getElementById('cGlass').onchange=e=>glassGrp.visible=e.target.checked;
document.getElementById('cGrid').onchange=()=>spinState();
document.getElementById('cEdge').onchange=e=>{
  if(e.target.checked){
    edges=new THREE.Group();
    const m=new THREE.LineBasicMaterial({color:THEMES[theme].edge});
    frameGrp.children.forEach(o=>{
      edges.add(new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry,26),m));
    });
    edges.position.copy(frameGrp.position);
    edges.scale.copy(frameGrp.scale);
    pivot.add(edges);
  } else if(edges){ pivot.remove(edges); edges=null; }
};
const manEl=document.getElementById('man');
document.getElementById('bMan').onclick=()=>{
  manEl.style.display=manEl.style.display==='block'?'none':'block';};
document.getElementById('tLight').onclick=()=>{theme='light';applyTheme();};
document.getElementById('tDark').onclick=()=>{theme='dark';applyTheme();};

/* ------------------------------------------------------------ keyboard */
addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT') return;
  const k=e.key;
  if(k==='ArrowLeft'){nudge(-30);e.preventDefault();}
  else if(k==='ArrowRight'){nudge(30);e.preventDefault();}
  else if(k==='ArrowUp'||k==='ArrowDown'){
    const d=(k==='ArrowUp'?-1:1)*THREE.MathUtils.degToRad(8);
    const p=THREE.MathUtils.clamp(controls.getPolarAngle()+d,
      controls.minPolarAngle+1e-3, controls.maxPolarAngle-1e-3);
    controls.setPolarAngle(p); e.preventDefault();
  }
  else if(k===' '){cSpin.checked=!cSpin.checked;spinState();e.preventDefault();}
  else if(k==='r'||k==='R'){document.getElementById('vReset').click();}
  else if(k==='l'||k==='L'){theme=theme==='light'?'dark':'light';applyTheme();}
  else if(k==='['){pivot.rotation.z-=THREE.MathUtils.degToRad(10);}
  else if(k===']'){pivot.rotation.z+=THREE.MathUtils.degToRad(10);}
  else if('123456'.includes(k)){
    setView(['iso','end','side','top','inside','truss'][+k-1]);
  }
});

/* ------------------------------------------------------------- render */
const azEl=document.getElementById('az');
function resize(){
  const w=innerWidth,h=innerHeight;
  renderer.setSize(w,h,false);
  camera.aspect=w/h; camera.updateProjectionMatrix();
}
addEventListener('resize',resize); resize();
applyTheme();

let last=performance.now();
(function loop(now){
  requestAnimationFrame(loop);
  now=now||performance.now();
  const dt=Math.min((now-last)/1000,.05); last=now;
  if(tween){
    const u=Math.min((now-tween.t0)/tween.ms,1);
    const e=u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2;      // ease in/out
    controls.setAzimuthalAngle(tween.from+(tween.to-tween.from)*e);
    if(u>=1) tween=null;
  }
  if(cSpin.checked && spinAxis.value==='z')
    pivot.rotation.z += dt*(spinSpeed.value/5)*0.35;
  controls.update();
  azEl.textContent=(((THREE.MathUtils.radToDeg(controls.getAzimuthalAngle())%360)+360)%360).toFixed(0);
  renderer.render(scene,camera);
})();
</script>
</body>
</html>
"""

HTML = (TEMPLATE
        .replace("__NSOLIDS__", str(nsolids))
        .replace("__CHECKS__", checks)
        .replace("__ROWS__", rows)
        .replace("__EXPW__", repr(EXP[0]))
        .replace("__EXPH__", repr(EXP[1]))
        .replace("__EXPL__", repr(EXP[2]))
        .replace("__BLOB__", blob))

open(OUT, "w", encoding="utf-8").write(HTML)
shutil.copyfile(OUT, "index.html")
print(f"-> {OUT} ({len(HTML)/1024:,.0f} KB, geometry from {GLB}) and index.html")
