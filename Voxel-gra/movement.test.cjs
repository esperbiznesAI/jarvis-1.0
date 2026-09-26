const assert = require('node:assert/strict');
const { World } = require('./world.js');
const { Controller, WATER_LEVEL } = require('./movement.js');
const dt = 1 / 120;
function advance(controller, seconds, yaw = 0) {
  for (let i = 0; i < Math.round(seconds / dt); i++) controller.step(dt, yaw);
}
const world = new World(); world.generate();

// A low-bank assist clears only the beach, without a high water jump.
const swimmer = new Controller(world);
swimmer.reset(14.5, 5.02, 23.5);
swimmer.keys.add('KeyW'); swimmer.keys.add('Space');
let peak=swimmer.player.y;
for(let i=0;i<90;i++){swimmer.step(dt,Math.PI/2);peak=Math.max(peak,swimmer.player.y);}
assert.ok(swimmer.player.x < 13.7, 'W + Space clears the bank horizontally');
assert.ok(peak<=6.2, 'Water exit does not launch above the beach');
swimmer.keys.delete('KeyW');advance(swimmer,1.5);
assert.ok(Math.abs(swimmer.player.y - 6) < .001, 'Land on the dry beach');
assert.equal(swimmer.grounded, true);
assert.equal(world.collides(swimmer.player), false);
assert.ok(swimmer.player.y<6.01,'Holding Space after exiting does not trigger another jump');

// Start in deep water and cross the submerged step before reaching the bank.
const crossing=new Controller(world);crossing.reset(22.5,WATER_LEVEL-1,23.5);
crossing.keys.add('KeyW');crossing.keys.add('Space');
let crossingPeak=crossing.player.y;
for(let i=0;i<480;i++){crossing.step(dt,Math.PI/2);crossingPeak=Math.max(crossingPeak,crossing.player.y);}
assert.ok(crossing.player.x<13.7,'Can cross the underwater ledge and exit from the middle of the lake');
assert.ok(Math.abs(crossing.player.y-6)<.001,'Full lake crossing ends on the dry bank');
assert.ok(crossingPeak<6.2,'Neither underwater step nor shore exit launches the player high');

// Holding Space at the lake surface submerges the body instead of bouncing.
const surface = new Controller(world);
surface.reset(22.5, WATER_LEVEL - .01, 23.5);
surface.keys.add('Space');surface.requestJump();advance(surface,5);
assert.ok(Math.abs(surface.player.y-(WATER_LEVEL-1))<.05,'Player floats with the body submerged');
assert.ok(Math.abs(surface.vy)<.05,'Floating settles without repeated bouncing');
const settled=surface.player.y;advance(surface,2);
assert.ok(Math.abs(surface.player.y-settled)<.05);

const shallow=new Controller(world);shallow.reset(14.5,5.02,23.5);
shallow.keys.add('Space');advance(shallow,4);
assert.ok(Math.abs(shallow.player.y-5)<.001,'Shallow water does not auto-jump from the lake floor');

const falling=new Controller(world);falling.reset(22.5,10,23.5);falling.keys.add('Space');
let entered=false;
for(let i=0;i<600;i++){
  falling.step(dt,0);
  if(falling.player.y<WATER_LEVEL-.1)entered=true;
  if(entered)assert.ok(falling.player.y<WATER_LEVEL,'Space cannot bounce back onto the water surface');
}
assert.ok(Math.abs(falling.player.y-(WATER_LEVEL-1))<.05);

const dryWorld=new World();dryWorld.generate();
for(let y=1;y<32;y++)dryWorld.set(34,y,42,0);
const miner=new Controller(dryWorld);miner.reset(34.5,4.5,42.5);
miner.keys.add('Space');miner.requestJump();advance(miner,.2);
assert.equal(dryWorld.waterContact(miner.player),null);
assert.ok(miner.player.y<4.1,'Below water level in dry land: gravity, not swimming');

// Flight escapes the lake, hovers without input and descends on C.
const flyer = new Controller(world);
flyer.reset(22.5, 4.05, 23.5);
assert.equal(world.collides(flyer.player), false);
flyer.toggleFlight(); flyer.keys.add('Space'); advance(flyer, 1);
assert.ok(flyer.player.y > 9.9, 'Flight rises from lake to above the bank');
flyer.clearInput(); const hoverY = flyer.player.y; advance(flyer, 1);
assert.equal(flyer.player.y, hoverY, 'No gravity or drift while flying');
flyer.keys.add('KeyC'); advance(flyer, .25);
assert.ok(flyer.player.y < hoverY - 1.4, 'C descends');
flyer.keys.add('Space'); const neutralY = flyer.player.y; advance(flyer, .2);
assert.equal(flyer.player.y, neutralY, 'Opposed vertical keys cancel');
flyer.clearInput(); flyer.toggleFlight(); advance(flyer, .2);
assert.ok(flyer.player.y < neutralY - .3, 'Turning flight off restores gravity');

// Flight still respects walls, floor and ceiling.
const room = new World();
for (let x = 1; x < 6; x++) for (let z = 1; z < 6; z++) {
  room.set(x, 0, z, 3); room.set(x, 5, z, 3);
}
for (let y = 1; y < 5; y++) for (let z = 1; z < 6; z++) room.set(5, y, z, 3);
const collision = new Controller(room); collision.reset(3.5, 1, 3.5); collision.toggleFlight();
collision.keys.add('Space'); advance(collision, 1);
assert.ok(collision.player.y <= 3.25001, 'Ceiling blocks flight');
assert.equal(room.collides(collision.player), false);
collision.clearInput(); collision.keys.add('KeyD'); advance(collision, 1);
assert.ok(collision.player.x <= 4.71001, 'Wall blocks flight');
collision.clearInput(); collision.keys.add('KeyC'); advance(collision, 1);
assert.ok(Math.abs(collision.player.y - 1) < .001, 'Floor blocks descent');
assert.equal(room.collides(collision.player), false);
collision.reset(3.5, 1, 3.5);
assert.equal(collision.flying, false); assert.equal(collision.vy, 0);
assert.equal(collision.keys.size, 0);
console.log('PASS: submerged swimming, gentle shore exit, no surface bouncing, shallow lake floor, dry underground gravity, flight and collisions');
