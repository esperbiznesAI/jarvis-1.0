const assert=require('node:assert/strict');
const THREE=require('./vendor/three.min.js');
const {World,SIZE,WATER_LEVEL}=require('./world.js');
const {createGeometry}=require('./water.js');
const world=new World();world.generate();
const columns=new Set(world.waterCells.map(({x,z})=>`${x},${z}`));
assert.ok(columns.size>100&&columns.size<500,'Only a bounded local basin contains water');
for(const {x,y,z} of world.waterCells){
  assert.ok(x>0&&x<SIZE-1&&z>0&&z<SIZE-1,'Lake is enclosed within the map');
  assert.equal(world.get(x,y,z),0,'Water never occupies solid terrain');
  assert.ok(y<WATER_LEVEL);
}
assert.equal(world.hasWater(34,5,23),true,'Connected part outside the original ellipse is filled');
assert.equal(world.hasWater(34,5,42),false,'Dry spawn area has no underground water');
const before=createGeometry(THREE,world);
for(let y=1;y<32;y++)world.set(34,y,42,0);
const after=createGeometry(THREE,world);
assert.deepEqual(after.attributes.position.array,before.attributes.position.array,'Digging dry terrain creates no water geometry');
assert.equal(world.waterContact({x:34.5,y:4.5,z:42.5}),null);

world.set(22,5,23,8);
assert.equal(world.hasWater(22,5,23),false,'Placed block removes precisely its water cell');
assert.equal(world.hasWater(22,4,23),true,'Lower cell remains filled');
assert.equal(world.hasWater(21,5,23),true,'Adjacent water remains');
world.set(22,5,23,0);
assert.equal(world.hasWater(22,5,23),false,'Mining does not regenerate displaced water');
assert.equal(world.waterContact({x:22.5,y:4.05,z:23.5}).surface,5,'Exposed lower cell has its actual local surface');
const edited=createGeometry(THREE,world);
const p=edited.attributes.position.array,n=edited.attributes.normal.array;
let foundLowerSurface=false;
for(let i=0;i<p.length;i+=9){
  const x=(p[i]+p[i+3]+p[i+6])/3,z=(p[i+2]+p[i+5]+p[i+8])/3;
  if(n[i+1]===1&&x>22&&x<23&&z>23&&z<24&&Math.abs(p[i+1]-5)<1e-6)foundLowerSurface=true;
}
assert.equal(foundLowerSurface,true,'Rendered water agrees with the lower physical surface');
for(let y=1;y<4;y++)world.set(22,y,23,0);
assert.equal(world.waterContact({x:22.5,y:1.1,z:23.5}),null,'A cavity entirely below the lake is dry');
before.dispose();after.dispose();edited.dispose();
console.log(`PASS: finite lake (${columns.size} columns), dry mining, displaced water, local surface geometry and dry space below lake`);
