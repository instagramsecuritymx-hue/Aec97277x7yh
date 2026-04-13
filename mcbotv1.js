#!/usr/bin/env node
/**
 * Bot para PocketMine-MP
 * Protocolo 70 (MCPE 0.15.x) y protocolo 84 (MCPE 0.16-0.17)
 *
 * Uso: node mc.js <ip> <port> <nombre> <bots> <time> [mensajes] [intervalo_msg]
 *
 * Ejemplos:
 *   node mc.js 127.0.0.1 19132 Bot 1 0
 *   node mc.js 127.0.0.1 19132 Bot 5 60 "Hola server!" 3
 *   node mc.js 127.0.0.1 19132 Bot 3 0 "Hola!|Como están?|Soy un bot" 4
 *
 *   time=0 → sin límite de tiempo (Ctrl+C para parar)
 *   mensajes separados por | para rotarlos
 */
'use strict';

const dgram  = require('dgram');
const zlib   = require('zlib');
const crypto = require('crypto');

// ─── Argumentos ───────────────────────────────────────────────────────────────
const HOST          = process.argv[2] || '127.0.0.1';
const PORT          = parseInt(process.argv[3])  || 19132;
const NOMBRE        = process.argv[4] || 'Bot';
const BOTS          = parseInt(process.argv[5])  || 1;
const TIEMPO        = parseInt(process.argv[6])  || 0;
const MENSAJES_RAW  = process.argv[7] || 'Hola!';
const MSG_INTERVALO = parseInt(process.argv[8])  || 5;

const MENSAJES = MENSAJES_RAW.split('|').map(m => m.trim()).filter(Boolean);

let botsConectados  = 0;
let botsActivos     = [];
let tiempoTerminado = false;

console.log(`[Master] Servidor: ${HOST}:${PORT}`);
console.log(`[Master] Bots: ${BOTS}  Nombre base: "${NOMBRE}"`);
console.log(`[Master] Tiempo: ${TIEMPO > 0 ? TIEMPO + 's' : 'ilimitado (Ctrl+C para parar)'}`);
console.log(`[Master] Mensajes: ${MENSAJES.join(' | ')}  cada ${MSG_INTERVALO}s\n`);

// ─── Helpers ──────────────────────────────────────────────────────────────────
function generarNombre(base) {
  const c = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let s = '';
  for (let i = 0; i < 6; i++) s += c[Math.floor(Math.random() * c.length)];
  return `${base}_${s}`;
}

// ─── Writer / Reader ─────────────────────────────────────────────────────────
class W {
  constructor() { this.p = []; }
  u8(v)    { const b=Buffer.alloc(1); b[0]=v&0xff;             this.p.push(b); return this; }
  u16be(v) { const b=Buffer.alloc(2); b.writeUInt16BE(v>>>0);  this.p.push(b); return this; }
  i32be(v) { const b=Buffer.alloc(4); b.writeInt32BE(v|0);     this.p.push(b); return this; }
  u32be(v) { const b=Buffer.alloc(4); b.writeUInt32BE(v>>>0);  this.p.push(b); return this; }
  i32le(v) { const b=Buffer.alloc(4); b.writeInt32LE(v|0);     this.p.push(b); return this; }
  i64be(v) { const b=Buffer.alloc(8); b.writeBigInt64BE(BigInt(v)); this.p.push(b); return this; }
  u64be(v) { const b=Buffer.alloc(8); b.writeBigUInt64BE(BigInt(v)); this.p.push(b); return this; }
  f32be(v) { const b=Buffer.alloc(4); b.writeFloatBE(v);       this.p.push(b); return this; }
  tLE(v)   { const b=Buffer.alloc(3); b[0]=v&0xff; b[1]=(v>>8)&0xff; b[2]=(v>>16)&0xff; this.p.push(b); return this; }
  raw(b)   { this.p.push(Buffer.isBuffer(b)?b:Buffer.from(b)); return this; }
  magic()  { this.p.push(MAGIC); return this; }
  str(s)   { const b=Buffer.from(s,'utf8'); this.u16be(b.length); this.p.push(b); return this; }
  strRaw(b){ this.u16be(b.length); this.p.push(b); return this; }
  rakIP(ip, port) {
    this.u8(4);
    ip.split('.').forEach(p => this.u8((~parseInt(p)) & 0xff));
    this.u16be(port);
    return this;
  }
  buf() { return Buffer.concat(this.p); }
}

class R {
  constructor(b) { this.b=b; this.p=0; }
  left()  { return this.b.length - this.p; }
  u8()    { return this.b.readUInt8(this.p++); }
  u16be() { const v=this.b.readUInt16BE(this.p); this.p+=2; return v; }
  i32be() { const v=this.b.readInt32BE(this.p);  this.p+=4; return v; }
  u32be() { const v=this.b.readUInt32BE(this.p); this.p+=4; return v; }
  i32le() { const v=this.b.readInt32LE(this.p);  this.p+=4; return v; }
  i64be() { const v=this.b.readBigInt64BE(this.p); this.p+=8; return v; }
  u64be() { const v=this.b.readBigUInt64BE(this.p); this.p+=8; return v; }
  f32be() { const v=this.b.readFloatBE(this.p);  this.p+=4; return v; }
  tLE()   { const v=this.b[this.p]|(this.b[this.p+1]<<8)|(this.b[this.p+2]<<16); this.p+=3; return v; }
  bytes(n){ const v=this.b.slice(this.p,this.p+n); this.p+=n; return v; }
  skip(n) { this.p+=n; return this; }
  str()   { const n=this.u16be(); return this.bytes(n).toString('utf8'); }
}

const MAGIC = Buffer.from([
  0x00,0xFF,0xFF,0x00,0xFE,0xFE,0xFE,0xFE,
  0xFD,0xFD,0xFD,0xFD,0x12,0x34,0x56,0x78,
]);

// ─── Packet IDs ──────────────────────────────────────────────────────────────
// Protocol 84 (MCPE 0.16+) — inner IDs inside batch
const P84 = {
  LOGIN:           0x01,
  PLAY_STATUS:     0x02,
  DISCONNECT:      0x05,
  BATCH:           0x06,
  TEXT:            0x07,
  START_GAME:      0x09,
  MOVE_PLAYER:     0x10,
  CHUNK_RADIUS:    0x3d,
};

// Protocol 70 (MCPE 0.15.x) — packet IDs = base | 0x80
const P70 = {
  LOGIN:           0x8f,
  PLAY_STATUS:     0x90,
  DISCONNECT:      0x91,
  BATCH:           0x92,
  TEXT:            0x93,
  START_GAME:      0x95,
  MOVE_PLAYER:     0x9d,
  CHUNK_RADIUS:    0xc9,
};

// ─── EC Key ──────────────────────────────────────────────────────────────────
let ecKey = null;
try { ecKey = crypto.generateKeyPairSync('ec', { namedCurve: 'P-384' }); } catch(e) {}

function pubKeyB64() {
  return ecKey ? ecKey.publicKey.export({ type:'spki', format:'der' }).toString('base64') : 'AAAA';
}
function b64url(data) {
  const b = Buffer.isBuffer(data) ? data : Buffer.from(JSON.stringify(data));
  return b.toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
}
function derToRaw(der) {
  let o = 2;
  const rLen = der[o+1]; o += 2;
  const rRaw = der.slice(o, o+rLen); o += rLen;
  const sLen = der[o+1]; o += 2;
  const sRaw = der.slice(o, o+sLen);
  const r = Buffer.alloc(48,0), s = Buffer.alloc(48,0);
  const rT = rRaw[0]===0 ? rRaw.slice(1) : rRaw;
  const sT = sRaw[0]===0 ? sRaw.slice(1) : sRaw;
  rT.copy(r, 48-rT.length);
  sT.copy(s, 48-sT.length);
  return Buffer.concat([r,s]);
}
function makeJWT(payload) {
  const pub  = pubKeyB64();
  const h    = b64url({alg:'ES384', x5u:pub});
  const p    = b64url(payload);
  const data = h + '.' + p;
  if (!ecKey) return data + '.';
  try {
    const der = crypto.createSign('SHA384').update(data).sign(ecKey.privateKey);
    return data + '.' + derToRaw(der).toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
  } catch(e) { return data + '.'; }
}

// ─── Login packets ────────────────────────────────────────────────────────────
function buildLogin84(bot) {
  const pub  = pubKeyB64();
  const uuid = '00000000-0000-4000-8000-' + crypto.randomBytes(6).toString('hex');
  const now  = Math.floor(Date.now() / 1000);

  const chain = makeJWT({
    extraData: { displayName:bot.nombre, identity:uuid, XUID:'' },
    identityPublicKey: pub,
    nbf: now-60, exp: now+86400,
  });
  const skin = makeJWT({
    ClientRandomId: Number(bot.clientId & 0xFFFFFFFFn),
    ServerAddress: `${HOST}:${PORT}`,
    SkinData: Buffer.alloc(8192,0).toString('base64'),
    SkinId: 'Standard_Custom',
    CapeData: '',
  });

  const chainBuf = Buffer.from(JSON.stringify({chain:[chain]}), 'utf8');
  const skinBuf  = Buffer.from(skin, 'utf8');
  const inner    = new W().i32le(chainBuf.length).raw(chainBuf).i32le(skinBuf.length).raw(skinBuf).buf();
  const comp     = zlib.deflateSync(inner, {level:7});

  // Protocol 84: wrap with 0xfe
  const pkt = new W().u8(P84.LOGIN).i32be(84).i32be(comp.length).raw(comp).buf();
  return Buffer.concat([Buffer.from([0xfe]), pkt]);
}

function buildLogin70(bot) {
  return new W()
    .u8(P70.LOGIN)
    .str(bot.nombre)
    .i32be(70).i32be(70)
    .u64be(bot.clientId)
    .raw(crypto.randomBytes(16))
    .str(`${HOST}:${PORT}`)
    .str('')
    .str('Standard_Custom')
    .strRaw(Buffer.alloc(8192,0))
    .u8(0)
    .buf();
}

// ─── Batch builder ────────────────────────────────────────────────────────────
function buildBatch(packets, bot) {
  const inner = Buffer.concat(packets.map(p => {
    const lb = Buffer.alloc(4);
    lb.writeUInt32BE(p.length);
    return Buffer.concat([lb, p]);
  }));
  const comp = zlib.deflateSync(inner, {level:7});

  if (bot.proto >= 84) {
    // Protocol 84: 0xfe 0x06 [i32be length] [compressed]
    const raw = new W().u8(P84.BATCH).i32be(comp.length).raw(comp).buf();
    return Buffer.concat([Buffer.from([0xfe]), raw]);
  } else {
    // Protocol 70: 0x92 [i32be length] [compressed]
    return new W().u8(P70.BATCH).i32be(comp.length).raw(comp).buf();
  }
}

// ─── RakNet frame sender ──────────────────────────────────────────────────────
function _rakFrame(bot, payload, isSplit, splitCount, splitId, splitIdx) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const w = new W();
  w.u8(0x84);
  w.tLE(bot.sendSeq++);
  w.u8(0x60 | (isSplit ? 0x10 : 0x00));
  w.u16be(payload.length * 8);
  w.tLE(bot.msgIndex++);
  w.tLE(bot.orderIndex++);
  w.u8(0);
  if (isSplit) { w.u32be(splitCount); w.u16be(splitId); w.u32be(splitIdx); }
  w.raw(payload);
  const buf = w.buf();
  bot.sock.send(buf, 0, buf.length, PORT, HOST, () => {});
}

function sendReliableOrdered(bot, payload) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const MAX = 1400;
  if (payload.length <= MAX) { _rakFrame(bot, payload, false, 0, 0, 0); return; }
  const splitId = (bot.splitId++) & 0xFFFF;
  const count   = Math.ceil(payload.length / MAX);
  for (let i = 0; i < count; i++) {
    _rakFrame(bot, payload.slice(i*MAX, (i+1)*MAX), true, count, splitId, i);
  }
}

function sendACK(bot, nums) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const sorted = [...new Set(nums)].sort((a,b)=>a-b);
  const recs = [];
  for (let i=0; i<sorted.length; ) {
    let s=sorted[i], e=s;
    while (i+1<sorted.length && sorted[i+1]===sorted[i]+1) { i++; e=sorted[i]; }
    recs.push([s,e]); i++;
  }
  const w = new W().u8(0xC0).u16be(recs.length);
  for (const [s,e] of recs) s===e ? w.u8(1).tLE(s) : w.u8(0).tLE(s).tLE(e);
  const buf = w.buf();
  bot.sock.send(buf, 0, buf.length, PORT, HOST, () => {});
}

// Enviar paquete de juego empaquetado en batch
function sendGame(bot, pkt) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  sendReliableOrdered(bot, buildBatch([pkt], bot));
}

// ─── Game packets ─────────────────────────────────────────────────────────────
function buildChunkRadius(bot, r) {
  const id = bot.proto >= 84 ? P84.CHUNK_RADIUS : P70.CHUNK_RADIUS;
  return new W().u8(id).i32be(r).buf();
}

/**
 * MOVE_PLAYER
 * Formato protocolo 70 y 84:
 *   entityId(i64) x(f32) y+1.62(f32) z(f32) yaw(f32) headYaw(f32) pitch(f32) mode(u8) onGround(u8)
 */
function buildMovePlayer(bot) {
  const p  = bot.pos;
  const id = bot.proto >= 84 ? P84.MOVE_PLAYER : P70.MOVE_PLAYER;
  return new W()
    .u8(id)
    .i64be(bot.entityId)
    .f32be(p.x)
    .f32be(p.y + 1.62)
    .f32be(p.z)
    .f32be(p.yaw)
    .f32be(p.yaw)   // headYaw
    .f32be(p.pitch)
    .u8(0)           // mode: 0 = normal
    .u8(1)           // onGround: true
    .buf();
}

/**
 * TEXT (chat)
 * Tipo 1 = mensaje de chat del jugador
 * Formato: type(u8) source(str) message(str)
 */
function buildChat(bot, msg) {
  const id = bot.proto >= 84 ? P84.TEXT : P70.TEXT;
  return new W()
    .u8(id)
    .u8(1)           // TYPE_CHAT
    .str(bot.nombre) // source
    .str(msg)        // message
    .buf();
}

// ─── Movimiento libre ─────────────────────────────────────────────────────────
const MOVE_TICK_MS   = 100;   // ms entre cada posición enviada
const MOVE_CHANGE_MS = 2500;  // ms entre cambios de dirección
const MOVE_STEP      = 0.25;  // bloques por tick
const MOVE_RANGE     = 80;    // radio máximo desde spawn

function startMovement(bot) {
  if (bot.moveTimer || bot.isClosing) return;

  const ox = bot.pos.x, oz = bot.pos.z;
  let dir   = Math.random() * Math.PI * 2;
  let speed = MOVE_STEP;

  // Cambiar dirección periódicamente
  bot.dirTimer = setInterval(() => {
    if (bot.isClosing || tiempoTerminado) { clearInterval(bot.dirTimer); return; }
    dir   = Math.random() * Math.PI * 2;
    speed = MOVE_STEP * (0.6 + Math.random() * 0.8);
  }, MOVE_CHANGE_MS);

  // Mover cada tick
  bot.moveTimer = setInterval(() => {
    if (!bot.spawned || bot.isClosing || tiempoTerminado) {
      clearInterval(bot.moveTimer); clearInterval(bot.dirTimer);
      bot.moveTimer = null; bot.dirTimer = null;
      return;
    }

    const nx = bot.pos.x + Math.cos(dir) * speed;
    const nz = bot.pos.z + Math.sin(dir) * speed;
    const distSq = (nx - ox) ** 2 + (nz - oz) ** 2;

    if (distSq > MOVE_RANGE * MOVE_RANGE) {
      // Girar hacia el centro
      dir = Math.atan2(oz - bot.pos.z, ox - bot.pos.x);
    } else {
      bot.pos.x = nx;
      bot.pos.z = nz;
    }

    // Yaw Minecraft: Norte=180, Sur=0, Este=-90, Oeste=90
    bot.pos.yaw   = ((dir * 180 / Math.PI) + 90 + 360) % 360;
    bot.pos.pitch = 0;

    sendGame(bot, buildMovePlayer(bot));
  }, MOVE_TICK_MS);
}

// ─── Chat continuo ────────────────────────────────────────────────────────────
let msgIdx = 0;

function startChat(bot) {
  if (bot.chatTimer || bot.isClosing) return;

  // Retardo inicial aleatorio para que no hablen todos a la vez
  const delay = Math.floor(Math.random() * (MSG_INTERVALO * 1000));

  setTimeout(() => {
    if (bot.isClosing || tiempoTerminado) return;

    function enviarMensaje() {
      if (!bot.spawned || bot.isClosing || tiempoTerminado) return;
      const msg = MENSAJES[msgIdx % MENSAJES.length];
      msgIdx++;
      sendGame(bot, buildChat(bot, msg));
      console.log(`[${bot.nombre}] Chat → "${msg}"`);
    }

    enviarMensaje();
    bot.chatTimer = setInterval(enviarMensaje, MSG_INTERVALO * 1000);
  }, delay);
}

// ─── Spawn del bot ────────────────────────────────────────────────────────────
function onSpawn(bot) {
  if (bot.spawned) return;
  bot.spawned   = true;
  bot.connected = true;
  botsConectados++;
  botsActivos.push(bot);
  console.log(`[${bot.nombre}] Spauneado en ${bot.pos.x.toFixed(1)},${bot.pos.y.toFixed(1)},${bot.pos.z.toFixed(1)} (${botsConectados}/${BOTS})`);
  startMovement(bot);
  startChat(bot);
}

// ─── Procesamiento de paquetes de juego ───────────────────────────────────────
function mcpe(bot, data) {
  if (!data || data.length === 0 || bot.isClosing) return;

  // Para protocolo 84, los paquetes dentro del batch vienen sin 0xfe
  let pid = data[0];
  const r = new R(data); r.skip(1);

  // ── PLAY_STATUS ─────────────────────────────────────────────────────────────
  if (pid === P84.PLAY_STATUS || pid === P70.PLAY_STATUS) {
    const st = r.i32be();
    if (st === 0) {
      // Login aceptado → pedir chunks inmediatamente
      // Este es el momento correcto según el protocolo PocketMine-MP
      console.log(`[${bot.nombre}] Login aceptado (proto=${bot.proto}), pidiendo chunks...`);
      bot.connected = true;
      sendGame(bot, buildChunkRadius(bot, 8));
    }
    if (st === 3) {
      // Servidor confirmó spawn del jugador
      onSpawn(bot);
    }
    return;
  }

  // ── START_GAME ──────────────────────────────────────────────────────────────
  if (pid === P84.START_GAME || pid === P70.START_GAME) {
    try {
      r.i32be();             // seed
      r.u8();                // dimension
      r.i32be();             // generator
      r.i32be();             // gamemode
      bot.entityId = r.i64be();
      r.i32be(); r.i32be(); r.i32be();  // spawn X, Y, Z
      bot.pos.x = r.f32be();
      bot.pos.y = r.f32be();
      bot.pos.z = r.f32be();
      console.log(`[${bot.nombre}] START_GAME entityId=${bot.entityId} pos=(${bot.pos.x.toFixed(1)},${bot.pos.y.toFixed(1)},${bot.pos.z.toFixed(1)})`);
    } catch(e) {}

    // Reenviar chunk radius por si no se recibió el PLAY_STATUS 0
    sendGame(bot, buildChunkRadius(bot, 8));

    // Fallback: si en 5s no llega PLAY_STATUS(3), forzar spawn
    if (!bot.spawnFallback) {
      bot.spawnFallback = setTimeout(() => {
        if (!bot.spawned && !bot.isClosing && !tiempoTerminado) {
          console.log(`[${bot.nombre}] Fallback spawn activado`);
          onSpawn(bot);
        }
      }, 5000);
    }
    return;
  }

  // ── DISCONNECT ──────────────────────────────────────────────────────────────
  if (pid === P84.DISCONNECT || pid === P70.DISCONNECT) {
    try { console.log(`[${bot.nombre}] Kick: ${r.str()}`); }
    catch(e) { console.log(`[${bot.nombre}] Desconectado por el servidor`); }
    cerrarBot(bot);
    return;
  }
}

// ─── Procesamiento de batches ─────────────────────────────────────────────────
function handleBatch(bot, payload) {
  if (bot.isClosing) return;
  try {
    const r       = new R(payload);
    const compLen = r.i32be();
    const comp    = r.bytes(Math.min(compLen, r.left()));
    let inner;
    try       { inner = zlib.inflateSync(comp); }
    catch(e)  { inner = zlib.inflateRawSync(comp); }
    const ir = new R(inner);
    while (ir.left() >= 4) {
      const len = ir.u32be();
      if (len === 0 || len > ir.left()) break;
      const pkt = ir.bytes(len);
      // Para protocolo 84, los inner packets pueden tener prefijo 0xfe
      if (pkt[0] === 0xfe && pkt.length > 1) {
        mcpe(bot, pkt.slice(1));
      } else {
        mcpe(bot, pkt);
      }
    }
  } catch(e) {}
}

// ─── Procesamiento RakNet ─────────────────────────────────────────────────────
function innerPacket(bot, payload) {
  if (!payload || payload.length === 0 || bot.isClosing) return;
  const pid = payload[0];

  // Connected Ping
  if (pid === 0x00) {
    if (payload.length >= 9) {
      const t = payload.readBigInt64BE(1);
      _rakFrame(bot, new W().u8(0x03).i64be(t).i64be(BigInt(Date.now())).buf(), false,0,0,0);
    }
    return;
  }
  // Connected Pong
  if (pid === 0x03) return;
  // Disconnection Notification
  if (pid === 0x15) { cerrarBot(bot); return; }
  // New Incoming Connection (server handshake)
  if (pid === 0x10) { handleServerHandshake(bot, payload); return; }

  // Protocolo 84: batch lleva prefijo 0xfe → [0xfe][0x06][...]
  if (pid === 0xfe && payload.length > 1) {
    const inner = payload.slice(1);
    if (inner[0] === P84.BATCH) {
      handleBatch(bot, inner.slice(1));
      return;
    }
    mcpe(bot, inner);
    return;
  }

  // Protocolo 70: batch = 0x92
  if (pid === P70.BATCH) {
    handleBatch(bot, payload.slice(1));
    return;
  }

  // Protocolo 84: batch sin prefijo (por si acaso)
  if (pid === P84.BATCH) {
    handleBatch(bot, payload.slice(1));
    return;
  }

  mcpe(bot, payload);
}

function parseDataPkt(bot, msg) {
  if (bot.isClosing) return;
  const r = new R(msg);
  r.skip(1);
  const seq = r.tLE();
  bot.ackQueue.push(seq);

  while (r.left() > 0) {
    try {
      const flags   = r.u8();
      const rel     = (flags >> 5) & 7;
      const isSplit = (flags >> 4) & 1;
      const bits    = r.u16be();
      const blen    = Math.ceil(bits / 8);

      if ([2,3,4,6,7].includes(rel)) r.tLE();
      if ([1,3,4].includes(rel))     { r.tLE(); r.u8(); }

      let sc=0,si=0,sx=0;
      if (isSplit) { sc=r.u32be(); si=r.u16be(); sx=r.u32be(); }

      const payload = r.bytes(blen);
      if (isSplit) {
        if (!bot.splitMap.has(si)) bot.splitMap.set(si, new Array(sc).fill(null));
        bot.splitMap.get(si)[sx] = payload;
        if (bot.splitMap.get(si).every(x => x!==null)) {
          innerPacket(bot, Buffer.concat(bot.splitMap.get(si)));
          bot.splitMap.delete(si);
        }
      } else {
        innerPacket(bot, payload);
      }
    } catch(e) { break; }
  }
}

// ─── Server Handshake ─────────────────────────────────────────────────────────
function handleServerHandshake(bot, payload) {
  if (bot.isClosing) return;
  const r = new R(payload); r.skip(1);
  let pingTime = 0n;
  try {
    const ipVer = r.u8();
    r.skip(ipVer === 4 ? 6 : 18);
    r.skip(2);
    for (let i=0; i<10; i++) { const v=r.u8(); r.skip(v===4?6:18); }
    pingTime = r.i64be();
  } catch(e) {}

  const hw = new W().u8(0x13);
  hw.rakIP(HOST, PORT);
  for (let i=0; i<10; i++) hw.u8(4).u8(0x80).u8(0xFF).u8(0xFF).u8(0xFE).u16be(0);
  hw.i64be(pingTime).i64be(BigInt(Date.now()));
  _rakFrame(bot, hw.buf(), false,0,0,0);

  if (bot.phase === 'HANDSHAKING') {
    bot.phase = 'CONNECTED';
    setTimeout(() => {
      if (tiempoTerminado || bot.isClosing) return;
      sendReliableOrdered(bot, bot.proto >= 84 ? buildLogin84(bot) : buildLogin70(bot));
    }, 150);
  }
}

// ─── Cerrar bot ───────────────────────────────────────────────────────────────
function cerrarBot(bot) {
  if (bot.isClosing) return;
  bot.isClosing = true;
  bot.connected = false;
  bot.spawned   = false;

  clearTimeout(bot.spawnFallback);
  if (bot.moveTimer)         { clearInterval(bot.moveTimer);         bot.moveTimer = null; }
  if (bot.dirTimer)          { clearInterval(bot.dirTimer);          bot.dirTimer = null; }
  if (bot.chatTimer)         { clearInterval(bot.chatTimer);         bot.chatTimer = null; }
  if (bot.keepaliveInterval) { clearInterval(bot.keepaliveInterval); bot.keepaliveInterval = null; }

  if (bot.sock) {
    try { bot.sock.close(); } catch(e) {}
    bot.sock = null;
  }
  console.log(`[${bot.nombre}] Desconectado`);
}

// ─── Iniciar bot ──────────────────────────────────────────────────────────────
function iniciarBot(numero) {
  const bot = {
    id:               numero,
    nombre:           generarNombre(NOMBRE),
    phase:            'UNCONNECTED',
    clientId:         BigInt('0x' + crypto.randomBytes(8).toString('hex')),
    mtuSize:          1464,
    serverGUID:       0n,
    sendSeq:          0,
    msgIndex:         0,
    orderIndex:       0,
    splitId:          0,
    ackQueue:         [],
    splitMap:         new Map(),
    entityId:         0n,
    proto:            70,       // Asumir 70 por defecto (PocketMine 0.15)
    pos:              { x:0, y:64, z:0, yaw:0, pitch:0 },
    spawned:          false,
    connected:        false,
    moveTimer:        null,
    dirTimer:         null,
    chatTimer:        null,
    spawnFallback:    null,
    keepaliveInterval:null,
    isClosing:        false,
  };

  bot.sock = dgram.createSocket('udp4');

  bot.sock.on('message', (msg) => {
    if (tiempoTerminado || bot.isClosing || !msg.length) return;
    const pid = msg[0];

    // ACK/NACK — ignorar
    if (pid === 0xC0 || pid === 0xA0) return;

    // Data packets RakNet (0x80-0x8F)
    if (pid >= 0x80 && pid <= 0x8F) {
      parseDataPkt(bot, msg);
      if (bot.ackQueue.length && !bot.isClosing) {
        sendACK(bot, bot.ackQueue);
        bot.ackQueue = [];
      }
      return;
    }

    // Open Connection Reply 1
    if (pid === 0x06 && bot.phase === 'CONNECTING_1') {
      const r = new R(msg); r.skip(17);
      bot.serverGUID = r.u64be();
      r.skip(1);
      bot.mtuSize = r.u16be();
      bot.phase   = 'CONNECTING_2';
      const buf = new W().u8(0x07).magic().rakIP(HOST,PORT).u16be(bot.mtuSize).u64be(bot.clientId).buf();
      bot.sock.send(buf, 0, buf.length, PORT, HOST, ()=>{});
      return;
    }

    // Open Connection Reply 2
    if (pid === 0x08 && bot.phase === 'CONNECTING_2') {
      bot.phase = 'HANDSHAKING';
      _rakFrame(bot, new W().u8(0x09).u64be(bot.clientId).i64be(BigInt(Date.now())).u8(0).buf(), false,0,0,0);
      return;
    }

    // Unconnected Pong → detectar protocolo del servidor desde el MOTD
    if (pid === 0x1C && bot.phase === 'UNCONNECTED') {
      try {
        const r = new R(msg); r.skip(1+8+8+16);
        const motd = r.bytes(r.u16be()).toString('utf8');
        const parts = motd.split(';');
        // MOTD formato: MCPE;<name>;<protocol>;<version>;<players>;<max_players>
        if (parts.length >= 3) {
          const proto = parseInt(parts[2]);
          if (!isNaN(proto)) bot.proto = proto;
        }
        console.log(`[${bot.nombre}] MOTD="${motd.substring(0,60)}" proto=${bot.proto}`);
      } catch(e) {}
      bot.phase = 'CONNECTING_1';
      sendRequest1(bot);
      return;
    }
  });

  bot.sock.on('error', ()=>{});
  bot.sock.bind(0);

  // Ping inicial para detectar el servidor y obtener protocolo
  const pingBuf = new W().u8(0x01).i64be(BigInt(Date.now())).magic().u64be(bot.clientId).buf();
  bot.sock.send(pingBuf, 0, pingBuf.length, PORT, HOST, ()=>{});

  // Fallback: si no hubo respuesta al ping en 2s, intentar conectar directo
  setTimeout(() => {
    if (bot.phase === 'UNCONNECTED' && !tiempoTerminado && bot.sock && !bot.isClosing) {
      bot.phase = 'CONNECTING_1';
      sendRequest1(bot);
    }
  }, 2000);

  // Keepalive
  bot.keepaliveInterval = setInterval(() => {
    if (tiempoTerminado || !bot.connected || !bot.sock || bot.isClosing) {
      clearInterval(bot.keepaliveInterval); return;
    }
    _rakFrame(bot, new W().u8(0x00).i64be(BigInt(Date.now())).buf(), false,0,0,0);
  }, 5000);

  return bot;
}

function sendRequest1(bot) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const padding = Math.max(0, bot.mtuSize - 46);
  const buf = new W().u8(0x05).magic().u8(7).raw(Buffer.alloc(padding,0)).buf();
  bot.sock.send(buf, 0, buf.length, PORT, HOST, ()=>{});
}

// ─── Desconexión por tiempo ───────────────────────────────────────────────────
if (TIEMPO > 0) {
  setTimeout(() => {
    console.log(`\n[Master] ${TIEMPO}s cumplidos. Desconectando ${botsActivos.length} bots...`);
    tiempoTerminado = true;
    botsActivos.forEach(bot => {
      try {
        if (bot.connected && bot.sock && !bot.isClosing) {
          _rakFrame(bot, new W().u8(0x15).buf(), false,0,0,0);
          setTimeout(() => cerrarBot(bot), 150);
        } else {
          cerrarBot(bot);
        }
      } catch(e) { cerrarBot(bot); }
    });
    console.log(`[Master] Total conectados exitosamente: ${botsConectados}`);
    setTimeout(() => process.exit(0), 1500);
  }, TIEMPO * 1000);
} else {
  console.log('[Master] Sin límite de tiempo. Ctrl+C para detener.\n');
}

// ─── Lanzar bots ─────────────────────────────────────────────────────────────
console.log(`[Master] Lanzando ${BOTS} bot(s)...`);
for (let i = 0; i < BOTS; i++) {
  setTimeout(() => {
    if (!tiempoTerminado) iniciarBot(i);
  }, i * 200);
}

// ─── Ctrl+C ───────────────────────────────────────────────────────────────────
process.on('SIGINT', () => {
  console.log('\n[Master] Ctrl+C — cerrando bots...');
  tiempoTerminado = true;
  botsActivos.forEach(bot => cerrarBot(bot));
  setTimeout(() => process.exit(0), 500);
});
