(function (root) {
  'use strict';
  const {WATER_LEVEL,RADIUS} = typeof module!=='undefined' ? require('./world.js') : root.VoxelCore;

  class Controller {
    constructor(world) {
      this.world = world;
      this.player = { x: 34.5, y: 9.01, z: 42.5 };
      this.keys = new Set();
      this.flying = false;
      this.grounded = false;
      this.vy = 0;
      this.jumpBuffer = 0;
      this.shoreHop = false;
    }

    clearInput() { this.keys.clear(); this.jumpBuffer = 0; }
    requestJump() { this.jumpBuffer = .14; }
    toggleFlight() {
      this.flying = !this.flying;
      this.vy = 0;
      this.grounded = false;
      this.jumpBuffer = 0;
      this.shoreHop = false;
      return this.flying;
    }
    reset(x, y, z) {
      Object.assign(this.player, { x, y, z });
      this.flying = false;
      this.grounded = false;
      this.vy = 0;
      this.shoreHop = false;
      this.clearInput();
    }

    moveAxis(axis, amount) {
      const steps = Math.max(1, Math.ceil(Math.abs(amount) / .15));
      const step = amount / steps;
      for (let i = 0; i < steps; i++) {
        const old = this.player[axis];
        this.player[axis] += step;
        if (!this.world.collides(this.player)) continue;
        let safe = 0, unsafe = 1;
        for (let j = 0; j < 16; j++) {
          const mid = (safe + unsafe) / 2;
          this.player[axis] = old + step * mid;
          if (this.world.collides(this.player)) unsafe = mid;
          else safe = mid;
        }
        this.player[axis] = old + step * safe;
        return true;
      }
      return false;
    }

    shoreHeight(dx,dz,water){
      const length=Math.hypot(dx,dz);
      if(!length||this.player.y+1.58<water.surface+.1)return null;
      const x=this.player.x+dx/length*(RADIUS+.25),z=this.player.z+dz/length*(RADIUS+.25);
      const top=this.world.surface(Math.floor(x),Math.floor(z));
      if(top<water.surface-.05||top>water.surface+.6||top-this.player.y>1.6)return null;
      if(this.world.hasWater(Math.floor(x),top,Math.floor(z)))return null;
      if(this.world.collides({x,y:top+.01,z}))return null;
      return top;
    }

    climbSubmergedStep(dx,dz,water){
      const length=Math.hypot(dx,dz);
      if(!length)return false;
      const x=this.player.x+dx/length*(RADIUS+.25),z=this.player.z+dz/length*(RADIUS+.25);
      const top=this.world.surface(Math.floor(x),Math.floor(z));
      // Lift only onto an actual submerged ledge, keeping the body in the water.
      if(top<=this.player.y+.01||top-this.player.y>.6||top>water.surface-.1)return false;
      if(!this.world.hasWater(Math.floor(x),top,Math.floor(z)))return false;
      if(this.world.collides({x,y:top+.001,z})||this.world.collides({...this.player,y:top+.001}))return false;
      if(this.moveAxis('y',top+.001-this.player.y))return false;
      this.moveAxis('x',dx);this.moveAxis('z',dz);this.vy=0;
      return true;
    }

    step(dt, yaw) {
      const keys = this.keys;
      let forward = Number(keys.has('KeyW')) - Number(keys.has('KeyS'));
      let side = Number(keys.has('KeyD')) - Number(keys.has('KeyA'));
      const length = Math.hypot(forward, side) || 1;
      forward /= length;
      side /= length;
      let contact = this.world.waterContact(this.player);
      const swimming = !!contact;
      const running = keys.has('ShiftLeft') || keys.has('ShiftRight');
      const speed = this.flying ? (running ? 11 : 7.5) : swimming ? 3.6 : running ? 7.3 : 4.6;
      const dx=(-Math.sin(yaw)*forward+Math.cos(yaw)*side)*speed*dt;
      const dz=(-Math.cos(yaw)*forward-Math.sin(yaw)*side)*speed*dt;
      const blockedX=this.moveAxis('x',dx),blockedZ=this.moveAxis('z',dz);
      contact=this.world.waterContact(this.player);

      if (this.flying) {
        const up = Number(keys.has('Space'));
        const down = Number(keys.has('KeyC'));
        this.moveAxis('y', (up - down) * 6 * dt);
        this.player.y = Math.min(this.player.y, 52);
        this.vy = 0;
        this.grounded = false;
        this.jumpBuffer = 0;
        return;
      }

      if(this.shoreHop&&(this.grounded||(contact&&this.vy<0&&this.player.y<contact.surface-.35)))this.shoreHop=false;
      if(contact&&!this.shoreHop){
        this.jumpBuffer=0;
        if(keys.has('Space')&&(blockedX||blockedZ))this.climbSubmergedStep(dx,dz,contact);
        const bank=keys.has('Space')&&(blockedX||blockedZ)?this.shoreHeight(dx,dz,contact):null;
        if(bank!==null){
          // Only a nearby low bank gets an assist; apex is 0.18 blocks over it.
          this.vy=Math.sqrt(2*24*Math.max(0,bank+.18-this.player.y));
          this.shoreHop=true;
        }else{
          // Hold Space to float with the body in the water, never stand on it.
          const target=keys.has('Space')?Math.max(-1.8,Math.min(2.2,(contact.surface-1-this.player.y)*5)):-1.4;
          this.vy+=(target-this.vy)*(1-Math.exp(-8*dt));
        }
      }else if(!contact&&!this.shoreHop&&this.jumpBuffer>0&&this.grounded){
        this.vy=8;
        this.grounded = false;
        this.jumpBuffer = 0;
      }
      this.jumpBuffer = Math.max(0, this.jumpBuffer - dt);
      if(!contact||this.shoreHop)this.vy-=24*dt;
      this.vy=Math.max(this.vy,-30);
      const vertical = this.vy * dt;
      this.grounded = false;
      if (this.moveAxis('y', vertical)) {
        this.grounded = vertical < 0;
        this.vy = 0;
      }
    }
  }

  const api = { Controller, WATER_LEVEL };
  root.VoxelMovement = api;
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
