(function (root) {
  'use strict';
  const SIZE = 80, HEIGHT = 32, RADIUS = 0.29, BODY = 1.75, WATER_LEVEL = 5.72;
  const names = ['', 'Trawa', 'Ziemia', 'Kamień', 'Drewno', 'Liście', 'Piasek', 'Cegła', 'Deski', 'Jasny kamień'];
  function hash(x, z) { const n = Math.sin(x * 127.1 + z * 311.7) * 43758.5453; return n - Math.floor(n); }
  class World {
    constructor() { this.data = new Uint8Array(SIZE * SIZE * HEIGHT); this.water = new Uint8Array(this.data.length); this.waterCells = []; }
    index(x, y, z) { return x + SIZE * (z + SIZE * y); }
    inside(x, y, z) { return x >= 0 && z >= 0 && y >= 0 && x < SIZE && z < SIZE && y < HEIGHT; }
    get(x, y, z) { return this.inside(x, y, z) ? this.data[this.index(x, y, z)] : 0; }
    set(x, y, z, id) { if (!this.inside(x, y, z)) return false; const index=this.index(x,y,z); this.data[index] = id; if(id) this.water[index]=0; return true; }
    hasWater(x, y, z) { return this.inside(x,y,z) && this.water[this.index(x,y,z)] === 1; }
    waterTop(x, y, z) { return this.hasWater(x,y,z) ? Math.min(y+1,WATER_LEVEL) : null; }
    waterContact(p) {
      let depth=0, surface=-Infinity;
      for(let x=Math.floor(p.x-RADIUS);x<=Math.floor(p.x+RADIUS-1e-6);x++)
        for(let z=Math.floor(p.z-RADIUS);z<=Math.floor(p.z+RADIUS-1e-6);z++) {
          let columnDepth=0;
          for(let y=Math.floor(p.y);y<=Math.floor(p.y+BODY-1e-6);y++) {
            const top=this.waterTop(x,y,z);
            if(top===null)continue;
            const overlap=Math.max(0,Math.min(p.y+BODY,top)-Math.max(p.y,y));
            if(overlap>0){columnDepth+=overlap;surface=Math.max(surface,top);}
          }
          depth=Math.max(depth,columnDepth);
        }
      return depth>1e-6 ? {depth,surface} : null;
    }
    surface(x, z) { for (let y = HEIGHT - 1; y >= 0; y--) if (this.get(x, y, z)) return y + 1; return 0; }
    generate() {
      this.data.fill(0);this.water.fill(0);this.waterCells=[];
      const ground = new Uint8Array(SIZE*SIZE);
      for (let x = 0; x < SIZE; x++) for (let z = 0; z < SIZE; z++) {
        let h = Math.floor(7.8 + Math.sin(x * .12) * 1.6 + Math.cos(z * .15) * 1.4 + Math.sin((x + z) * .21) * .8);
        const pond = Math.hypot((x - 22) / 1.2, z - 23);
        if (pond < 10) h = Math.min(h, Math.floor(3.3 + pond * .25));
        if (Math.hypot(x - 34, z - 40) < 5) h = 8;
        ground[x+SIZE*z]=h+1;
        for (let y = 0; y <= h; y++) this.set(x, y, z, y === h ? (h < 6 ? 6 : 1) : y > h - 3 ? 2 : 3);
      }
      // Fill only the original connected lake basin; excavations never create water.
      const visited=new Uint8Array(SIZE*SIZE), pending=[[22,23]];
      for(let i=0;i<pending.length;i++){
        const [x,z]=pending[i];
        if(x<0||z<0||x>=SIZE||z>=SIZE)continue;
        const column=x+SIZE*z;
        if(visited[column])continue;
        visited[column]=1;
        if(ground[column]>=WATER_LEVEL)continue;
        for(let y=ground[column];y<WATER_LEVEL;y++){
          this.water[this.index(x,y,z)]=1;
          this.waterCells.push({x,y,z});
        }
        pending.push([x-1,z],[x+1,z],[x,z-1],[x,z+1]);
      }
      for (let x = 4; x < SIZE - 4; x += 3) for (let z = 4; z < SIZE - 4; z += 3) {
        const y = this.surface(x, z);
        if (y < 7 || Math.hypot(x - 34, z - 40) < 8 || hash(x, z) < .75) continue;
        const height = 4 + Math.floor(hash(z, x) * 2);
        for (let dy = 0; dy < height; dy++) this.set(x, y + dy, z, 4);
        for (let dx = -2; dx <= 2; dx++) for (let dz = -2; dz <= 2; dz++) for (let dy = -2; dy <= 1; dy++) {
          if (Math.abs(dx) + Math.abs(dz) + Math.max(0, dy) > 4) continue;
          if (!this.get(x + dx, y + height + dy, z + dz)) this.set(x + dx, y + height + dy, z + dz, 5);
        }
      }
    }
    collides(p) {
      if (p.x - RADIUS < 0 || p.z - RADIUS < 0 || p.x + RADIUS > SIZE || p.z + RADIUS > SIZE || p.y < 0) return true;
      for (let x = Math.floor(p.x - RADIUS); x <= Math.floor(p.x + RADIUS - 1e-6); x++)
        for (let z = Math.floor(p.z - RADIUS); z <= Math.floor(p.z + RADIUS - 1e-6); z++)
          for (let y = Math.floor(p.y + 1e-6); y <= Math.floor(p.y + BODY - 1e-6); y++)
            if (this.get(x, y, z)) return true;
      return false;
    }
    intersectsPlayer(x, y, z, p) {
      return x < p.x + RADIUS && x + 1 > p.x - RADIUS && y < p.y + BODY && y + 1 > p.y && z < p.z + RADIUS && z + 1 > p.z - RADIUS;
    }
    raycast(origin, direction, reach = 6) {
      let x = Math.floor(origin.x), y = Math.floor(origin.y), z = Math.floor(origin.z);
      const step = {}, delta = {}, t = {}, cell = { x, y, z };
      for (const axis of ['x', 'y', 'z']) {
        step[axis] = Math.sign(direction[axis]);
        delta[axis] = direction[axis] === 0 ? Infinity : Math.abs(1 / direction[axis]);
        t[axis] = direction[axis] === 0 ? Infinity : ((step[axis] > 0 ? cell[axis] + 1 : cell[axis]) - origin[axis]) / direction[axis];
      }
      let distance = 0, normal = { x: 0, y: 0, z: 0 };
      while (distance <= reach) {
        const id = this.get(cell.x, cell.y, cell.z);
        if (id) return { ...cell, id, normal, distance };
        const axis = t.x <= t.y && t.x <= t.z ? 'x' : t.y <= t.z ? 'y' : 'z';
        distance = t[axis];
        if (!Number.isFinite(distance)) break;
        cell[axis] += step[axis]; t[axis] += delta[axis];
        normal = { x: 0, y: 0, z: 0 }; normal[axis] = -step[axis];
      }
      return null;
    }
  }
  const api = { World, SIZE, HEIGHT, RADIUS, BODY, WATER_LEVEL, names, hash };
  root.VoxelCore = api;
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
