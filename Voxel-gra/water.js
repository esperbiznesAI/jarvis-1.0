(function(root){
  'use strict';
  function createGeometry(THREE, world){
    const positions=[],normals=[];
    const faces=[
      {n:[1,0,0],v:[[1,0,1],[1,0,0],[1,1,0],[1,1,1]]},
      {n:[-1,0,0],v:[[0,0,0],[0,0,1],[0,1,1],[0,1,0]]},
      {n:[0,1,0],v:[[0,1,1],[1,1,1],[1,1,0],[0,1,0]]},
      {n:[0,-1,0],v:[[0,0,0],[1,0,0],[1,0,1],[0,0,1]]},
      {n:[0,0,1],v:[[0,0,1],[1,0,1],[1,1,1],[0,1,1]]},
      {n:[0,0,-1],v:[[1,0,0],[0,0,0],[0,1,0],[1,1,0]]}
    ];
    for(const {x,y,z} of world.waterCells){
      const top=world.waterTop(x,y,z);
      if(top===null)continue;
      for(const face of faces){
        const nx=x+face.n[0],ny=y+face.n[1],nz=z+face.n[2];
        if(world.hasWater(nx,ny,nz))continue;
        if(world.get(nx,ny,nz)&&!(face.n[1]===1&&top<y+1))continue;
        for(const i of [0,1,2,0,2,3]){
          positions.push(x+face.v[i][0],face.v[i][1]?top:y,z+face.v[i][2]);
          normals.push(...face.n);
        }
      }
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    geometry.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
    geometry.computeBoundingSphere();
    return geometry;
  }
  root.VoxelWater={createGeometry};
  if(typeof module!=='undefined')module.exports={createGeometry};
})(typeof window!=='undefined'?window:globalThis);
