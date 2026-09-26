(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  function fatal(error) { $('fatal').hidden = false; console.error(error); }
  if (!window.THREE) { fatal(new Error('Nie można wczytać lokalnej biblioteki grafiki.')); return; }
  const { World, SIZE, HEIGHT, BODY, names, hash } = VoxelCore;
  const blockCount = names.length - 1;
  const world = new World(); world.generate();
  const movement = new VoxelMovement.Controller(world);
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' }); }
  catch (error) { fatal(error); return; }
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
  renderer.setSize(innerWidth, innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  $('viewport').appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#a5d7e8');
  scene.fog = new THREE.Fog('#a5d7e8', 32, 87);
  scene.add(new THREE.HemisphereLight(0xe5f5ff, 0x829057, 2));
  const sunlight = new THREE.DirectionalLight(0xffefd0, 2.2); sunlight.position.set(-25, 60, 15); scene.add(sunlight);
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, .06, 160);
  camera.rotation.order = 'YXZ';
  const atlas = document.createElement('canvas'); atlas.width = 176; atlas.height = 16;
  const ctx = atlas.getContext('2d');
  const colors = ['#80b54c','#977248','#997148','#8e9495','#e0d298','#927045','#b28b55','#558f39','#c3985e','#ab6853','#d8dfd9'];
  colors.forEach((color, tile) => {
    ctx.fillStyle = color; ctx.fillRect(tile * 16, 0, 16, 16);
    for (let i = 0; i < 65; i++) {
      const x = Math.floor(hash(i + tile * 100, 7) * 16), y = Math.floor(hash(i, tile + 9) * 16);
      ctx.fillStyle = i % 2 ? '#ffffff19' : '#16251018'; ctx.fillRect(tile * 16 + x, y, 1 + i % 3, 1 + i % 2);
    }
    if (tile === 1) {
      ctx.fillStyle = '#79aa45'; ctx.fillRect(tile * 16, 0, 16, 4);
      for (let x = 0; x < 16; x++) ctx.fillRect(tile * 16 + x, 3, 1, 1 + Math.floor(hash(x, 22) * 4));
    }
    if (tile === 5) { ctx.fillStyle = '#654b3260'; for (let x = 2; x < 16; x += 4) ctx.fillRect(tile * 16 + x, 0, 1, 16); }
    if (tile === 6) { ctx.strokeStyle = '#76573380'; ctx.strokeRect(tile * 16 + 3.5, 3.5, 9, 9); ctx.strokeRect(tile * 16 + 6.5, 6.5, 3, 3); }
    if (tile === 8) {
      for(let y=0;y<16;y+=4){ctx.fillStyle='#765636';ctx.fillRect(tile*16,y,16,1);ctx.fillStyle='#efd2a480';ctx.fillRect(tile*16,y+1,16,1);ctx.fillStyle='#977140';ctx.fillRect(tile*16+(y%8?11:4),y,1,4);}
      ctx.fillStyle='#805a3444';ctx.fillRect(tile*16+1,6,6,1);ctx.fillRect(tile*16+6,14,7,1);
    }
    if (tile === 9) { ctx.fillStyle = '#d9b291'; for (let y = 0; y < 16; y += 5) { ctx.fillRect(tile * 16, y, 16, 1); for (let x = y % 2 ? 4 : 0; x < 16; x += 8) ctx.fillRect(tile * 16 + x, y, 1, 5); } }
    if (tile === 10) {
      ctx.fillStyle='#9daea8';ctx.fillRect(tile*16,0,16,1);ctx.fillRect(tile*16,8,16,1);ctx.fillRect(tile*16+10,0,1,8);ctx.fillRect(tile*16+4,8,1,8);
      ctx.fillStyle='#f6f5e999';ctx.fillRect(tile*16,1,10,1);ctx.fillRect(tile*16+5,9,11,1);
    }
  });
  const texture = new THREE.CanvasTexture(atlas); texture.magFilter = THREE.NearestFilter; texture.minFilter = THREE.NearestFilter; texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.MeshLambertMaterial({ map: texture, vertexColors: true });
  const faces = [
    { n:[1,0,0], v:[[1,0,1],[1,0,0],[1,1,0],[1,1,1]], s:.83 },
    { n:[-1,0,0], v:[[0,0,0],[0,0,1],[0,1,1],[0,1,0]], s:.75 },
    { n:[0,1,0], v:[[0,1,1],[1,1,1],[1,1,0],[0,1,0]], s:1 },
    { n:[0,-1,0], v:[[0,0,0],[1,0,0],[1,0,1],[0,0,1]], s:.54 },
    { n:[0,0,1], v:[[0,0,1],[1,0,1],[1,1,1],[0,1,1]], s:.9 },
    { n:[0,0,-1], v:[[1,0,0],[0,0,0],[0,1,0],[1,1,0]], s:.8 }
  ];
  const tileFor = (id, face) => id === 1 ? (face === 2 ? 0 : face === 3 ? 2 : 1) : id === 4 ? (face === 2 || face === 3 ? 6 : 5) : ({ 2:2, 3:3, 5:7, 6:4, 7:9, 8:8, 9:10 })[id];
  const chunks = new Map();
  function buildChunk(cx, cz) {
    const key = `${cx},${cz}`, previous = chunks.get(key);
    if (previous) { scene.remove(previous); previous.geometry.dispose(); }
    const positions = [], normals = [], uvs = [], colors = [];
    for (let x = cx * 16; x < (cx + 1) * 16; x++) for (let z = cz * 16; z < (cz + 1) * 16; z++) for (let y = 0; y < HEIGHT; y++) {
      const id = world.get(x,y,z); if (!id) continue;
      faces.forEach((face, f) => {
        if (world.get(x + face.n[0], y + face.n[1], z + face.n[2])) return;
        const tile = tileFor(id, f), shade = face.s * (.93 + hash(x + y * 2, z) * .07);
        const coords = [[0,0],[1,0],[1,1],[0,1]];
        for (const i of [0,1,2,0,2,3]) {
          positions.push(x + face.v[i][0], y + face.v[i][1], z + face.v[i][2]); normals.push(...face.n);
          uvs.push((tile + .015 + coords[i][0] * .97) / 11, .015 + coords[i][1] * .97);
          colors.push(shade,shade,shade);
        }
      });
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions,3)); geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals,3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs,2)); geo.setAttribute('color', new THREE.Float32BufferAttribute(colors,3));
    geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, material); scene.add(mesh); chunks.set(key, mesh);
  }
  for (let x = 0; x < SIZE / 16; x++) for (let z = 0; z < SIZE / 16; z++) buildChunk(x,z);
  function rebuild(x,z) {
    const affected = new Set();
    for (const [dx,dz] of [[0,0],[1,0],[-1,0],[0,1],[0,-1]]) {
      const cx = Math.floor((x + dx) / 16), cz = Math.floor((z + dz) / 16);
      if (cx >= 0 && cz >= 0 && cx < SIZE / 16 && cz < SIZE / 16) affected.add(`${cx},${cz}`);
    }
    affected.forEach(key => buildChunk(...key.split(',').map(Number)));
    const previousWater=water.geometry;water.geometry=VoxelWater.createGeometry(THREE,world);previousWater.dispose();
  }
  const water = new THREE.Mesh(VoxelWater.createGeometry(THREE,world),new THREE.MeshPhongMaterial({ color:0x48b9ca, transparent:true, opacity:.58, shininess:90, depthWrite:false, side:THREE.DoubleSide }));
  scene.add(water);
  const sun = new THREE.Mesh(new THREE.BoxGeometry(6,6,1),new THREE.MeshBasicMaterial({ color:0xfff4bf, fog:false })); sun.position.set(10,43,-35); scene.add(sun);
  const clouds = new VoxelClouds.CloudLayer(THREE,scene,SIZE,hash);
  const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1.006,1.006,1.006)),new THREE.LineBasicMaterial({color:0x253c23, transparent:true, opacity:.8})); outline.visible=false; scene.add(outline);
  let selected = 1, active = false, fallback = false, yaw = .28, pitch = -.14, hit = null;
  const player = movement.player;
  const keys = movement.keys, direction = new THREE.Vector3();
  let toastTimer;
  function toast(text) { $('toast').textContent=text; $('toast').classList.add('visible'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),4000); }
  function iconFor(id) {
    const c=document.createElement('canvas'); c.width=48;c.height=48; const g=c.getContext('2d');
    g.imageSmoothingEnabled=false;
    function quad(points,tile,dark) { g.save();g.beginPath();points.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath();g.clip();const [a,b,,d]=points;g.transform((b[0]-a[0])/16,(b[1]-a[1])/16,(d[0]-a[0])/16,(d[1]-a[1])/16,a[0],a[1]);g.drawImage(atlas,tile*16,0,16,16,0,0,16,16);g.fillStyle=`rgba(0,0,0,${dark})`;g.fillRect(0,0,16,16);g.restore(); }
    quad([[24,4],[44,14],[24,24],[4,14]],tileFor(id,2),0);quad([[4,14],[24,24],[24,46],[4,36]],tileFor(id,0),.13);quad([[24,24],[44,14],[44,36],[24,46]],tileFor(id,0),.27);return c.toDataURL();
  }
  for(let id=1;id<=blockCount;id++){const button=document.createElement('button');button.className='slot';button.title=`${id} · ${names[id]}`;button.setAttribute('aria-label',`Wybierz: ${names[id]}`);button.innerHTML=`<span>${id}</span><img alt="" src="${iconFor(id)}">`;button.addEventListener('click',()=>select(id));$('hotbar').appendChild(button);}
  function select(id) { selected=id;$('selected-name').textContent=names[id];Array.from($('hotbar').children).forEach((b,i)=>b.setAttribute('aria-pressed',String(i+1===id))); }
  select(1);
  let positionLabel = '';
  function syncCamera(){camera.position.set(player.x,player.y+1.58,player.z);camera.rotation.set(pitch,yaw,0);camera.updateMatrixWorld();const next=`X: ${player.x.toFixed(1)} / Y: ${player.y.toFixed(1)} / Z: ${player.z.toFixed(1)}`;if(next!==positionLabel){positionLabel=next;$('position-value').textContent=next;}}
  function setActive(value){active=value;movement.clearInput();$('menu').hidden=value;document.body.classList.toggle('playing',value);if(value){$('play').innerHTML='Wróć do świata <span>→</span>';$('respawn').hidden=false;$('menu-title').innerHTML='Chwila<br><em>oddechu.</em>';$('menu-description').innerHTML='Twoja dolina czeka.<br>Kontynuuj, kiedy zechcesz.';}else{outline.visible=false;$('target-label').textContent='';}}
  function showFlightMode(){
    $('movement-mode').textContent=movement.flying?'Latanie · F: wyłącz':'Tryb swobodny · F: lot';
    $('flight-help').innerHTML=movement.flying?'<b>Spacja</b> ↑ <b>C</b> ↓ <b>F</b> lądowanie':'<b>F</b> latanie';
  }
  function useFallback(){fallback=true;$('fallback-note').hidden=false;setActive(true);toast('Strzałki: rozglądanie · Q: rozbij · E: postaw · Esc: menu');}
  async function start(){setActive(true);try{if(!renderer.domElement.requestPointerLock){useFallback();return;}await renderer.domElement.requestPointerLock();}catch(error){useFallback();}}
  $('play').addEventListener('click',start);
  $('help').addEventListener('click',()=>{document.exitPointerLock?.();setActive(false);});
  document.addEventListener('pointerlockchange',()=>{if(document.pointerLockElement===renderer.domElement){fallback=false;setActive(true);}else if(!fallback)setActive(false);});
  document.addEventListener('pointerlockerror',useFallback);
  document.addEventListener('mousemove',e=>{if(active&&document.pointerLockElement===renderer.domElement){yaw-=e.movementX*.0022;pitch=Math.max(-1.52,Math.min(1.52,pitch-e.movementY*.0022));}});
  function respawn(){const x=34.5,z=42.5;let y=world.surface(Math.floor(x),Math.floor(z))+.02;if(y+BODY>HEIGHT){y=HEIGHT+1;}movement.reset(x,y,z);showFlightMode();yaw=.28;pitch=-.14;syncCamera();toast('Jesteś z powrotem na polanie.');}
  $('respawn').addEventListener('click',()=>{respawn();start();});
  function updateTarget(){camera.getWorldDirection(direction);hit=world.raycast(camera.position,direction);outline.visible=active&&!!hit;if(hit){outline.position.set(hit.x+.5,hit.y+.5,hit.z+.5);$('target-label').textContent=names[hit.id];}else $('target-label').textContent='';}
  let lastAction=0;
  function editBlock(place){if(!active)return false;syncCamera();updateTarget();if(!hit)return false;if(performance.now()-lastAction<140)return false;lastAction=performance.now();
    if(place){const x=hit.x+hit.normal.x,y=hit.y+hit.normal.y,z=hit.z+hit.normal.z;if(!world.inside(x,y,z)){toast('To już granica tej małej doliny.');return false;}if(world.get(x,y,z)||world.intersectsPlayer(x,y,z,player)){toast('Zrób krok w tył — ten blok byłby za blisko.');return false;}world.set(x,y,z,selected);rebuild(x,z);}
    else{if(hit.y===0){toast('To podłoże doliny — nie da się go rozbić.');return false;}world.set(hit.x,hit.y,hit.z,0);rebuild(hit.x,hit.z);}updateTarget();return true;}
  renderer.domElement.addEventListener('mousedown',e=>{if(!active)return;if(e.button===0)editBlock(false);if(e.button===2)editBlock(true);});
  renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());
  addEventListener('wheel',e=>{if(active&&e.deltaY!==0){e.preventDefault();select(((selected-1+(e.deltaY>0?1:blockCount-1))%blockCount)+1);}},{passive:false});
  const controlled=new Set(['KeyW','KeyA','KeyS','KeyD','Space','ShiftLeft','ShiftRight','KeyC','KeyF','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','KeyQ','KeyE']);
  addEventListener('keydown',e=>{if(e.code==='Escape'){document.exitPointerLock?.();setActive(false);return;}if(!active)return;if(controlled.has(e.code))e.preventDefault();keys.add(e.code);if(!e.repeat&&e.code==='Space')movement.requestJump();if(!e.repeat&&e.code==='KeyF'){movement.toggleFlight();showFlightMode();toast(movement.flying?'Latanie włączone · Spacja: w górę · C: w dół · F: wyłącz':'Latanie wyłączone.');}if(/^Digit[1-9]$/.test(e.code))select(Number(e.code.slice(-1)));if(!e.repeat&&e.code==='KeyQ')editBlock(false);if(!e.repeat&&e.code==='KeyE')editBlock(true);});
  addEventListener('keyup',e=>keys.delete(e.code));
  function pause(){keys.clear();if(active){document.exitPointerLock?.();setActive(false);}}
  addEventListener('blur',pause);document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
  addEventListener('resize',()=>{renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();});
  function physics(dt){
    if(keys.has('ArrowLeft'))yaw+=dt*1.65;if(keys.has('ArrowRight'))yaw-=dt*1.65;if(keys.has('ArrowUp'))pitch=Math.min(1.52,pitch+dt*1.3);if(keys.has('ArrowDown'))pitch=Math.max(-1.52,pitch-dt*1.3);
    movement.step(dt,yaw);
    if(player.y<-5)respawn();
  }
  let previous=performance.now(),accumulator=0;
  function frame(now){requestAnimationFrame(frame);const dt=Math.min((now-previous)/1000,.075);previous=now;if(active){accumulator+=dt;while(accumulator>=1/120){physics(1/120);accumulator-=1/120;}}else accumulator=0;clouds.update(dt);syncCamera();if(active)updateTarget();renderer.render(scene,camera);}
  syncCamera();requestAnimationFrame(frame);
  // Optional browser integration shares the same selection state as the hotbar.
  if(document.modelContext?.registerTool){try{Promise.resolve(document.modelContext.registerTool({name:'select_building_block',description:'Select the block used for building in Klockowa Dolina.',inputSchema:{type:'object',properties:{block:{type:'integer',minimum:1,maximum:blockCount}},required:['block'],additionalProperties:false},annotations:{readOnlyHint:false},execute(input){if(!input||!Number.isInteger(input.block)||input.block<1||input.block>blockCount||Object.keys(input).some(k=>k!=='block'))throw new Error(`Expected block from 1 to ${blockCount}.`);select(input.block);return{selected, name:names[selected]};}})).catch(()=>{});}catch{}}
  // Read-only diagnostics make local gameplay verification reproducible.
  window.voxelGame=Object.freeze({inspect:()=>({ready:true,active,fallback,selected,player:{...player},grounded:movement.grounded,flying:movement.flying,hit:hit?{...hit}:null,blocks:world.data.reduce((n,id)=>n+Number(id>0),0),worldSize:SIZE,blockTypes:blockCount,clouds:clouds.inspect(),chunks:chunks.size,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles})});
})();
