(function (root) {
  'use strict';
  class CloudLayer {
    constructor(THREE, scene, size, hash) {
      this.elapsed = 0;
      this.clouds = [];
      this.margin = 120;
      this.span = size + this.margin * 2;
      this.height = 31;
      this.speed = .8;
      const material = new THREE.MeshBasicMaterial({ vertexColors: true });
      const faces = [
        { n:[1,0,0], v:[[1,0,1],[1,0,0],[1,1,0],[1,1,1]], color:0xe4e9ed },
        { n:[-1,0,0], v:[[0,0,0],[0,0,1],[0,1,1],[0,1,0]], color:0xf0f2f4 },
        { n:[0,1,0], v:[[0,1,1],[1,1,1],[1,1,0],[0,1,0]], color:0xffffff },
        { n:[0,-1,0], v:[[0,0,0],[1,0,0],[1,0,1],[0,0,1]], color:0xd8dfe5 },
        { n:[0,0,1], v:[[0,0,1],[1,0,1],[1,1,1],[0,1,1]], color:0xeaf0f3 },
        { n:[0,0,-1], v:[[1,0,0],[0,0,0],[0,1,0],[1,1,0]], color:0xe0e7ed }
      ];
      // Each footprint is a single slab: square corners, a flat top and no tiers.
      const footprints = [
        ['  ####      ','  ####      ','##########  ','##########  ','   #########','   #########','   ####     '],
        ['      ##### ','      ##### ','############','############','########    ','  ######    ','  ###       '],
        ['####        ','####  ####  ','##########  ','############','############','     #######','     ####   '],
        ['   ######   ','   ######   ','#########   ','############','############','####   #####','####   #####'],
        ['      ####  ','##########  ','##########  ','########    ','   #########','   #########','       #####'],
        ['#####       ','#########   ','#########   ','   #########','   #########','######  ####','######      ']
      ];
      const geometries = footprints.map(footprint => {
        const cells = new Set();
        footprint.forEach((row,z) => {
          for(let x=0;x<row.length;x++) if(row[x]==='#') cells.add(`${x-6},0,${z-3}`);
        });
        const positions = [], colors = [];
        for (const cell of cells) {
          const [x,y,z] = cell.split(',').map(Number);
          for (const face of faces) {
            if (cells.has(`${x+face.n[0]},${y+face.n[1]},${z+face.n[2]}`)) continue;
            const color = new THREE.Color(face.color);
            for (const i of [0,1,2,0,2,3]) {
              positions.push((x+face.v[i][0])*2.5,(y+face.v[i][1])*1.7,(z+face.v[i][2])*2.5);
              colors.push(color.r,color.g,color.b);
            }
          }
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
        geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
        geometry.computeBoundingSphere();
        return geometry;
      });
      for(let row=0;row<4;row++) for(let column=0;column<6;column++) {
        const i=row*6+column;
        const mesh = new THREE.Mesh(geometries[i%geometries.length],material);
        const x = -this.margin + (column+.5)*this.span/6 + (hash(i,61)-.5)*13;
        const y = this.height;
        const z = -65 + row*(size+130)/3 + (hash(i,63)-.5)*16;
        const scale = .8+hash(i,64)*.6;
        mesh.scale.set(scale, 1, scale);
        mesh.position.set(x,y,z);
        scene.add(mesh);
        this.clouds.push({mesh,x,y,z});
      }
    }
    update(dt) {
      this.elapsed += dt;
      for (const cloud of this.clouds) {
        cloud.mesh.position.x = ((cloud.x + this.margin + this.elapsed*this.speed) % this.span) - this.margin;
      }
    }
    inspect() {
      return {count:this.clouds.length,elapsed:this.elapsed,positions:this.clouds.map(({mesh})=>({x:mesh.position.x,y:mesh.position.y,z:mesh.position.z}))};
    }
  }
  root.VoxelClouds = {CloudLayer};
  if (typeof module !== 'undefined') module.exports = {CloudLayer};
})(typeof window !== 'undefined' ? window : globalThis);
