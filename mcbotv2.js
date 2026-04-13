#!/usr/bin/env node
/**
 * Bot para PocketMine-MP - Con soporte para espacios usando -
 * Proto 70 (MCPE 0.15.x) y proto 84 (MCPE 0.16.x)
 *
 * Uso: node mc.js <ip> <port> <nombre> <bots> <time> [register_cmd] [mensajes] [intervalo_msg]
 *
 * Ejemplos:
 *   node mc.js 127.0.0.1 19132 Bot 1 0
 *   node mc.js 127.0.0.1 19132 Bot 5 60 "/r" "Hola!" 3
 *   node mc.js 127.0.0.1 19132 Bot 3 0 "/register" "Hola!|Como-están?|Bot-aquí" 4
 *   node mc.js 127.0.0.1 19132 Bot 3 0 "" "spam" 4
 *
 *   NOTA: Para enviar espacios en los mensajes, usa - (guión) como reemplazo
 *   Ejemplo: "Hola-como-estas" se enviará como "Hola como estas"
 *   Para enviar múltiples mensajes, sepáralos con | (pipe)
 *   Ejemplo: "Hola-mundo|Como-están|Bot-aquí"
 *
 *   register_cmd: "/r", "/register" o "" (vacío = solo envía la contraseña de 8 dígitos)
 *   time=0 = sin límite (Ctrl+C para parar)
 */
'use strict';

const dgram  = require('dgram');
const zlib   = require('zlib');
const crypto = require('crypto');

// ─── Argumentos ───────────────────────────────────────────────────────────────
const HOST          = process.argv[2]  || '127.0.0.1';
const PORT          = parseInt(process.argv[3])  || 19132;
const NOMBRE        = process.argv[4]  || 'Bot';
const BOTS          = parseInt(process.argv[5])  || 1;
const TIEMPO        = parseInt(process.argv[6])  || 0;
const REGISTER_CMD  = process.argv[7]  !== undefined ? process.argv[7] : '';
const MENSAJES_RAW  = process.argv[8]  || 'Hola!';
const MSG_INTERVALO = parseInt(process.argv[9])  || 5;

// ─── Función para convertir - en espacio en los mensajes ──────────────────────
function convertirEspacios(texto) {
    if (!texto) return '';
    // Reemplazar - por espacio
    return texto.replace(/-/g, ' ');
}

// Procesar mensajes: separar por | y luego convertir - a espacio en cada uno
const MENSAJES_RAW_SPLIT = MENSAJES_RAW.split('|').filter(m => m.trim());
const MENSAJES = MENSAJES_RAW_SPLIT.map(m => convertirEspacios(m.trim()));

console.log(`[Master] Mensajes convertidos:`);
MENSAJES.forEach((m, i) => console.log(`   ${i+1}: "${m}"`));

let botsConectados  = 0;
let botsActivos     = [];
let tiempoTerminado = false;

console.log(`[Master] Servidor  : ${HOST}:${PORT}`);
console.log(`[Master] Bots      : ${BOTS}  Nombre base: "${NOMBRE}"`);
console.log(`[Master] Tiempo    : ${TIEMPO > 0 ? TIEMPO + 's' : 'ilimitado (Ctrl+C para parar)'}`);
console.log(`[Master] Register  : ${REGISTER_CMD !== '' ? REGISTER_CMD + ' <pass8>' : '(solo contraseña)'}`);
console.log(`[Master] Mensajes  : ${MENSAJES.join(' | ')}  cada ${MSG_INTERVALO}s\n`);

// ─── Utilidades ───────────────────────────────────────────────────────────────
function generarNombre(base) {
  const c = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let s = '';
  for (let i = 0; i < 6; i++) s += c[Math.floor(Math.random() * c.length)];
  return `${base}_${s}`;
}

function randomPass8() {
  const c = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let s = '';
  for (let i = 0; i < 8; i++) s += c[Math.floor(Math.random() * c.length)];
  return s;
}

// ─── Skin de Steve (64x32 RGBA) ──────────────────────────────────────────────
function generateSteveSkin() {
  const buf  = Buffer.alloc(64 * 32 * 4, 0);
  const fill = (x0, y0, x1, y1, r, g, b, a) => {
    a = a === undefined ? 255 : a;
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const i = (y * 64 + x) * 4;
        buf[i] = r; buf[i+1] = g; buf[i+2] = b; buf[i+3] = a;
      }
    }
  };
  const px = (x, y, r, g, b) => {
    const i = (y * 64 + x) * 4;
    buf[i] = r; buf[i+1] = g; buf[i+2] = b; buf[i+3] = 255;
  };

  // Paleta Steve
  const SK = [198, 134, 66];   // skin (cara/brazos)
  const HR = [92,  56,  35];   // cabello marrón
  const SH = [67,  95, 175];   // camisa azul
  const PT = [53,  85, 105];   // pantalón
  const BT = [38,  38,  38];   // bota oscura

  // ── Cabeza (y=0-16) ──────────────────────────────────────────────────────
  fill(8,  0, 16,  8, ...HR);   // top cabeza (pelo)
  fill(16, 0, 24,  8, ...SK);   // bottom cabeza (piel)
  fill( 0, 8,  8, 16, ...SK);   // lado derecho
  fill( 8, 8, 16, 16, ...SK);   // frente
  fill(16, 8, 24, 16, ...HR);   // lado izquierdo
  fill(24, 8, 32, 16, ...HR);   // parte trasera
  fill(8, 0, 16, 4, ...HR);
  // frente: cara con rasgos
  fill( 9, 9, 11, 11, 255, 255, 255);
  px(9, 10, 33,  18,  7);
  fill(13, 9, 15, 11, 255, 255, 255);
  px(14, 10, 33, 18,  7);
  px(11, 11, ...SK); px(12, 11, ...SK);
  px(11, 12, 140, 80, 30); px(12, 12, 140, 80, 30);
  fill(10, 13, 14, 14, 140, 60, 20);

  // ── Cuerpo (y=16-32, x=16-40) ────────────────────────────────────────────
  fill(20, 16, 28, 20, ...SH);
  fill(28, 16, 36, 20, ...SH);
  fill(16, 20, 20, 32, ...SH);
  fill(20, 20, 28, 32, ...SH);
  fill(28, 20, 32, 32, ...SH);
  fill(32, 20, 40, 32, ...SH);
  fill(23, 20, 25, 32, 50, 75, 155);

  // ── Brazo derecho (x=40-56, y=16-32) ────────────────────────────────────
  fill(44, 16, 48, 20, ...SK);
  fill(48, 16, 52, 20, ...SK);
  fill(40, 20, 44, 32, ...SK);
  fill(44, 20, 48, 32, ...SK);
  fill(48, 20, 52, 32, ...SK);
  fill(52, 20, 56, 32, ...SK);
  fill(44, 20, 48, 24, ...SH);
  fill(40, 20, 44, 24, ...SH);
  fill(48, 20, 52, 24, ...SH);
  fill(52, 20, 56, 24, ...SH);

  // ── Pierna derecha (x=0-16, y=16-32) ────────────────────────────────────
  fill( 4, 16,  8, 20, ...PT);
  fill( 8, 16, 12, 20, ...PT);
  fill( 0, 20,  4, 32, ...PT);
  fill( 4, 20,  8, 32, ...PT);
  fill( 8, 20, 12, 32, ...PT);
  fill(12, 20, 16, 32, ...PT);
  fill( 0, 28,  4, 32, ...BT);
  fill( 4, 28,  8, 32, ...BT);
  fill( 8, 28, 12, 32, ...BT);
  fill(12, 28, 16, 32, ...BT);

  return buf.toString('base64');
}

const STEVE_SKIN = generateSteveSkin();

// ─── Writer / Reader ──────────────────────────────────────────────────────────
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
    ip.split('.').forEach(o => this.u8((~parseInt(o)) & 0xff));
    this.u16be(port);
    return this;
  }
  buf() { return Buffer.concat(this.p); }
}

class R {
  constructor(b) { this.b=b; this.p=0; }
  left()   { return this.b.length - this.p; }
  u8()     { return this.b.readUInt8(this.p++); }
  u16be()  { const v=this.b.readUInt16BE(this.p); this.p+=2; return v; }
  i32be()  { const v=this.b.readInt32BE(this.p);  this.p+=4; return v; }
  u32be()  { const v=this.b.readUInt32BE(this.p); this.p+=4; return v; }
  i64be()  { const v=this.b.readBigInt64BE(this.p); this.p+=8; return v; }
  u64be()  { const v=this.b.readBigUInt64BE(this.p); this.p+=8; return v; }
  f32be()  { const v=this.b.readFloatBE(this.p);  this.p+=4; return v; }
  tLE()    { const v=this.b[this.p]|(this.b[this.p+1]<<8)|(this.b[this.p+2]<<16); this.p+=3; return v; }
  bytes(n) { const v=this.b.slice(this.p,this.p+n); this.p+=n; return v; }
  skip(n)  { this.p+=n; return this; }
  str()    { const n=this.u16be(); return this.bytes(n).toString('utf8'); }
}

const MAGIC = Buffer.from([
  0x00,0xFF,0xFF,0x00,0xFE,0xFE,0xFE,0xFE,
  0xFD,0xFD,0xFD,0xFD,0x12,0x34,0x56,0x78,
]);

const MTU_LIST = [1492, 1464, 1400, 1200, 576];

// ─── IDs de paquetes ──────────────────────────────────────────────────────────
const P70 = {
  LOGIN:          0x8f,
  PLAY_STATUS:    0x90,
  DISCONNECT:     0x91,
  BATCH:          0x92,
  TEXT:           0x93,
  START_GAME:     0x95,
  MOVE_PLAYER:    0x9d,
  CHUNK_RADIUS:   0xc9,
};

const P84_A = {
  LOGIN:          0x01,
  PLAY_STATUS:    0x02,
  DISCONNECT:     0x05,
  RSPACK_INFO:    0x06,
  RSPACK_STACK:   0x07,
  RSPACK_RESP:    0x08,
  TEXT:           0x07,
  START_GAME:     0x09,
  MOVE_PLAYER:    0x10,
  CHUNK_RADIUS:   0x3d,
};

const P84_B = {
  LOGIN:          0x01,
  PLAY_STATUS:    0x02,
  SERVER_HS:      0x03,
  CLIENT_HS:      0x04,
  DISCONNECT:     0x05,
  RSPACK_INFO:    0x06,
  RSPACK_STACK:   0x07,
  RSPACK_RESP:    0x08,
  TEXT:           0x09,
  START_GAME:     0x0b,
  MOVE_PLAYER:    0x13,
  CHUNK_RADIUS:   0x45,
};

// ─── EC Key para JWT ──────────────────────────────────────────────────────────
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
  const rLen = der[o+1]; o+=2; const rRaw = der.slice(o, o+rLen); o+=rLen;
  const sLen = der[o+1]; o+=2; const sRaw = der.slice(o, o+sLen);
  const r = Buffer.alloc(48,0), s = Buffer.alloc(48,0);
  const rT = rRaw[0]===0?rRaw.slice(1):rRaw; const sT = sRaw[0]===0?sRaw.slice(1):sRaw;
  rT.copy(r, 48-rT.length); sT.copy(s, 48-sT.length);
  return Buffer.concat([r,s]);
}
function makeJWT(payload) {
  const pub  = pubKeyB64();
  const data = b64url({ alg:'ES384', x5u:pub }) + '.' + b64url(payload);
  if (!ecKey) return data + '.';
  try {
    const der = crypto.createSign('SHA384').update(data).sign(ecKey.privateKey);
    return data + '.' + derToRaw(der).toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
  } catch(e) { return data + '.'; }
}

// ─── Login Proto 84 con skin de Steve ────────────────────────────────────────
function buildLogin84(bot) {
  const pub  = pubKeyB64();
  const uuid = '00000000-0000-4000-8000-' + crypto.randomBytes(6).toString('hex');
  const now  = Math.floor(Date.now() / 1000);

  const chain = makeJWT({
    extraData: { displayName: bot.nombre, identity: uuid, XUID: '' },
    identityPublicKey: pub,
    nbf: now - 60,
    exp: now + 86400,
  });

  const skin = makeJWT({
    ClientRandomId:   Number(bot.clientId & 0xFFFFFFFFn),
    ServerAddress:    `${HOST}:${PORT}`,
    SkinData:         STEVE_SKIN,
    SkinId:           'Standard_Custom',
    CapeData:         '',
    SkinGeometryName: 'geometry.humanoid.custom',
    SkinGeometry:     '',
    DeviceOS:         1,
    GameVersion:      '0.15.10',
  });

  const chainBuf = Buffer.from(JSON.stringify({ chain: [chain] }), 'utf8');
  const skinBuf  = Buffer.from(skin, 'utf8');

  const raw  = new W().i32le(chainBuf.length).raw(chainBuf).i32le(skinBuf.length).raw(skinBuf).buf();
  const comp = zlib.deflateSync(raw, { level: 7 });

  return Buffer.concat([
    Buffer.from([0xfe, 0x01]),
    new W().i32be(84).i32be(comp.length).raw(comp).buf(),
  ]);
}

// ─── Login Proto 70 con skin de Steve ────────────────────────────────────────
function buildLogin70(bot) {
  const skinBuf = Buffer.from(STEVE_SKIN, 'base64');
  return new W()
    .u8(P70.LOGIN)
    .str(bot.nombre)
    .i32be(70).i32be(70)
    .u64be(bot.clientId)
    .raw(crypto.randomBytes(16))
    .str(`${HOST}:${PORT}`)
    .str('')
    .str('Standard_Custom')
    .strRaw(skinBuf)
    .u8(0)
    .buf();
}

// ─── Batch builder ────────────────────────────────────────────────────────────
function buildBatch(pkts, bot) {
  const inner = Buffer.concat(pkts.map(p => {
    const lb = Buffer.alloc(4); lb.writeUInt32BE(p.length); return Buffer.concat([lb, p]);
  }));
  const comp = zlib.deflateSync(inner, { level: 7 });
  if (bot.proto >= 84) {
    return Buffer.concat([Buffer.from([0xfe, 0x06]), new W().i32be(comp.length).raw(comp).buf()]);
  }
  return new W().u8(P70.BATCH).i32be(comp.length).raw(comp).buf();
}

// ─── RakNet frame sender ──────────────────────────────────────────────────────
const FRAME_STORE_MAX = 1024;

function _rakFrame(bot, payload, isSplit, splitCount, splitId, splitIdx) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const seq = bot.sendSeq++;
  const w   = new W();
  w.u8(0x84).tLE(seq);
  w.u8(isSplit ? 0x70 : 0x60);
  w.u16be(payload.length * 8);
  w.tLE(bot.msgIndex++).tLE(bot.orderIndex++).u8(0);
  if (isSplit) { w.u32be(splitCount); w.u16be(splitId); w.u32be(splitIdx); }
  w.raw(payload);
  const buf = w.buf();

  bot.sentFrames.set(seq, buf);
  if (bot.sentFrames.size > FRAME_STORE_MAX) {
    bot.sentFrames.delete(bot.sentFrames.keys().next().value);
  }
  bot.sock.send(buf, 0, buf.length, PORT, HOST, () => {});
}

function sendReliableOrdered(bot, payload) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const MAX = (bot.mtuSize || 1464) - 60;
  if (payload.length <= MAX) { _rakFrame(bot, payload, false, 0, 0, 0); return; }
  const sid = (bot.splitId++) & 0xFFFF;
  const cnt = Math.ceil(payload.length / MAX);
  for (let i = 0; i < cnt; i++) {
    _rakFrame(bot, payload.slice(i * MAX, (i + 1) * MAX), true, cnt, sid, i);
  }
}

function sendGame(bot, pkt) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  sendReliableOrdered(bot, buildBatch([pkt], bot));
}

// ─── ACK / NACK ───────────────────────────────────────────────────────────────
function sendACK(bot, nums) {
  if (!bot.sock || bot.isClosing) return;
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

function handleNACK(bot, msg) {
  if (!bot.sock || bot.isClosing) return;
  try {
    const r = new R(msg); r.skip(1);
    const cnt = r.u16be();
    for (let i=0; i<cnt; i++) {
      const single = r.u8(); const s = r.tLE(); const e = single ? s : r.tLE();
      for (let seq=s; seq<=e; seq++) {
        const f = bot.sentFrames.get(seq);
        if (f && bot.sock && !bot.isClosing) bot.sock.send(f, 0, f.length, PORT, HOST, ()=>{});
      }
    }
  } catch(e) {}
}

// ─── Paquetes de juego ────────────────────────────────────────────────────────
function getProtoIds(bot) {
  if (bot.proto < 84) return { move: P70.MOVE_PLAYER, text: P70.TEXT, chunk: P70.CHUNK_RADIUS };
  return bot.useVariantA
    ? { move: P84_A.MOVE_PLAYER, text: P84_A.TEXT, chunk: P84_A.CHUNK_RADIUS }
    : { move: P84_B.MOVE_PLAYER, text: P84_B.TEXT, chunk: P84_B.CHUNK_RADIUS };
}

function buildChunkRadius(bot) {
  return new W().u8(getProtoIds(bot).chunk).i32be(8).buf();
}

function buildMovePlayer(bot) {
  const p = bot.pos;
  return new W()
    .u8(getProtoIds(bot).move)
    .i64be(bot.entityId)
    .f32be(p.x).f32be(p.y).f32be(p.z)
    .f32be(p.yaw).f32be(p.yaw).f32be(p.pitch)
    .u8(0).u8(1)
    .buf();
}

function buildChat(bot, msg) {
  return new W().u8(getProtoIds(bot).text).u8(1).str(bot.nombre).str(msg).buf();
}

function buildResourcePackResponse(bot, status) {
  const id = bot.useVariantA ? P84_A.RSPACK_RESP : P84_B.RSPACK_RESP;
  return new W().u8(id).u8(status).u16be(0).buf();
}

// ─── Registro automático MEJORADO ─────────────────────────────────────────────
function sendRegister(bot) {
  if (bot.registerSent) return;
  bot.registerSent = true;

  const pass = randomPass8();
  let msg;
  if (REGISTER_CMD === '') {
    msg = pass;
  } else {
    msg = REGISTER_CMD + ' ' + pass;
  }

  // Enviar inmediatamente cuando el bot está spawned
  if (bot.spawned && !bot.isClosing && !tiempoTerminado) {
    // Múltiples intentos para asegurar el envío
    const sendAttempt = (attempt) => {
      if (!bot.spawned || bot.isClosing || tiempoTerminado) return;
      sendGame(bot, buildChat(bot, msg));
      console.log(`[${bot.nombre}] Register → "${msg}" (intento ${attempt})`);
    };
    
    // Enviar inmediatamente
    sendAttempt(1);
    
    // Reenviar después de 1 segundo por si acaso
    setTimeout(() => sendAttempt(2), 1000);
    
    // Último reenvío después de 2.5 segundos
    setTimeout(() => sendAttempt(3), 2500);
  } else {
    // Si no está spawned aún, esperar y luego enviar
    const waitForSpawn = setInterval(() => {
      if (bot.spawned && !bot.isClosing && !tiempoTerminado) {
        clearInterval(waitForSpawn);
        sendGame(bot, buildChat(bot, msg));
        console.log(`[${bot.nombre}] Register (deferred) → "${msg}"`);
        // Reenviar después de 1 segundo
        setTimeout(() => {
          if (bot.spawned && !bot.isClosing && !tiempoTerminado) {
            sendGame(bot, buildChat(bot, msg));
            console.log(`[${bot.nombre}] Register (retry) → "${msg}"`);
          }
        }, 1000);
      }
    }, 500);
    
    // Timeout para no esperar indefinidamente
    setTimeout(() => clearInterval(waitForSpawn), 10000);
  }
}

// ─── Movimiento con gravedad y retorno ────────────────────────────────────────
const MOVE_TICK_MS   = 100;
const MOVE_CHANGE_MS = 3000;
const MOVE_STEP      = 0.28;
const MOVE_RANGE     = 22;
const GRAVITY_RATE   = 0.12;

function startMovement(bot) {
  if (bot.moveTimer || bot.isClosing) return;

  const ox = bot.pos.x;
  const oy = bot.pos.y;
  const oz = bot.pos.z;

  let dir = Math.random() * Math.PI * 2;
  let spd = MOVE_STEP;
  let velY = 0;

  bot.dirTimer = setInterval(() => {
    if (bot.isClosing || tiempoTerminado) { clearInterval(bot.dirTimer); return; }
    dir = Math.random() * Math.PI * 2;
    spd = MOVE_STEP * (0.6 + Math.random() * 0.8);
  }, MOVE_CHANGE_MS);

  bot.moveTimer = setInterval(() => {
    if (!bot.spawned || bot.isClosing || tiempoTerminado) {
      clearInterval(bot.moveTimer); clearInterval(bot.dirTimer);
      bot.moveTimer = bot.dirTimer = null; return;
    }

    const dx = bot.pos.x - ox;
    const dz = bot.pos.z - oz;
    const dist2 = dx * dx + dz * dz;

    if (dist2 > MOVE_RANGE * MOVE_RANGE) {
      dir = Math.atan2(oz - bot.pos.z, ox - bot.pos.x);
      spd = MOVE_STEP * 1.2;
    } else {
      const nx = bot.pos.x + Math.cos(dir) * spd;
      const nz = bot.pos.z + Math.sin(dir) * spd;
      bot.pos.x = nx;
      bot.pos.z = nz;
    }

    if (bot.pos.y > oy + 0.05) {
      velY -= GRAVITY_RATE;
      bot.pos.y += velY;
      if (bot.pos.y <= oy) {
        bot.pos.y = oy;
        velY = 0;
      }
    } else if (bot.pos.y < oy - 0.05) {
      bot.pos.y += 0.2;
      if (bot.pos.y > oy) bot.pos.y = oy;
    } else {
      bot.pos.y = oy;
      velY = 0;
    }

    bot.pos.yaw = ((dir * 180 / Math.PI) + 90 + 360) % 360;
    sendGame(bot, buildMovePlayer(bot));
  }, MOVE_TICK_MS);
}

// ─── Chat continuo (spam) MEJORADO ─────────────────────────────────────────
let globalMsgIdx = 0;

function startChat(bot) {
  if (bot.chatTimer || bot.isClosing) return;
  
  // Pequeño delay aleatorio antes de empezar el spam (entre 0.5 y 3 segundos)
  const initialDelay = Math.floor(Math.random() * 2500) + 500;
  
  setTimeout(() => {
    if (bot.isClosing || tiempoTerminado) return;
    
    // Función para enviar un mensaje con confirmación
    const sendMessage = (message, retryCount = 0) => {
      if (!bot.spawned || bot.isClosing || tiempoTerminado) return;
      
      sendGame(bot, buildChat(bot, message));
      console.log(`[${bot.nombre}] Chat → "${message}"${retryCount > 0 ? ` (retry ${retryCount})` : ''}`);
      
      // Si es el primer intento, programar un retry después de 0.5 segundos
      if (retryCount === 0) {
        setTimeout(() => {
          if (bot.spawned && !bot.isClosing && !tiempoTerminado) {
            // Enviar de nuevo para asegurar
            sendGame(bot, buildChat(bot, message));
            console.log(`[${bot.nombre}] Chat → "${message}" (confirmation)`);
          }
        }, 500);
      }
    };
    
    // Enviar primer mensaje
    const firstMsg = MENSAJES[globalMsgIdx % MENSAJES.length];
    globalMsgIdx++;
    sendMessage(firstMsg);
    
    // Configurar intervalo para mensajes siguientes
    bot.chatTimer = setInterval(() => {
      if (!bot.spawned || bot.isClosing || tiempoTerminado) {
        if (bot.chatTimer) clearInterval(bot.chatTimer);
        return;
      }
      
      const msg = MENSAJES[globalMsgIdx % MENSAJES.length];
      globalMsgIdx++;
      sendMessage(msg);
      
    }, MSG_INTERVALO * 1000);
    
  }, initialDelay);
}

// ─── Spawn MEJORADO ────────────────────────────────────────────────────
function onSpawn(bot) {
  if (bot.spawned) return;
  bot.spawned = true;
  botsConectados++;
  botsActivos.push(bot);
  console.log(`[${bot.nombre}] ✓ En juego — pos=(${bot.pos.x.toFixed(1)},${bot.pos.y.toFixed(1)},${bot.pos.z.toFixed(1)}) total=${botsConectados}/${BOTS}`);

  // Enviar registro inmediatamente cuando se hace spawn
  sendRegister(bot);
  
  // Pequeño delay antes de iniciar movimiento y chat
  setTimeout(() => {
    if (!bot.isClosing && !tiempoTerminado) {
      startMovement(bot);
      startChat(bot);
    }
  }, 500);
}

// ─── Procesamiento de paquetes de juego ───────────────────────────────────────
function mcpe(bot, data) {
  if (!data || data.length === 0 || bot.isClosing) return;
  const pid = data[0];
  const r   = new R(data); r.skip(1);

  if (pid === P70.PLAY_STATUS || pid === 0x02) {
    const st = r.i32be();
    const names = { 0:'Login OK', 1:'Cliente viejo', 2:'Servidor lleno', 3:'Spawneado', 4:'Mundo viejo', 5:'Cliente nuevo' };
    console.log(`[${bot.nombre}] PLAY_STATUS=${st} (${names[st] || '?'})`);
    if (st === 0) {
      sendGame(bot, buildChunkRadius(bot));
    } else if (st === 1 || st === 2) {
      cerrarBot(bot);
    } else if (st === 3) {
      onSpawn(bot);
    }
    return;
  }

  if (pid === 0x06 && bot.proto >= 84 && !bot.resourcePackDone && !bot.useVariantA) {
    console.log(`[${bot.nombre}] Resource pack info → confirmando`);
    sendGame(bot, buildResourcePackResponse(bot, 3));
    return;
  }

  if (pid === 0x07 && bot.proto >= 84 && !bot.resourcePackDone && !bot.useVariantA) {
    console.log(`[${bot.nombre}] Resource pack stack → completado`);
    bot.resourcePackDone = true;
    sendGame(bot, buildResourcePackResponse(bot, 4));
    return;
  }

  if (pid === 0x03 && bot.proto >= 84) {
    console.log(`[${bot.nombre}] Server handshake recibido → respondiendo`);
    sendGame(bot, new W().u8(0x04).buf());
    sendGame(bot, buildChunkRadius(bot));
    return;
  }

  if (pid === P70.START_GAME || pid === 0x09 || pid === 0x0b || pid === 0x11) {
    if (bot.proto >= 84) {
      bot.useVariantA = (pid === 0x09);
      console.log(`[${bot.nombre}] START_GAME id=0x${pid.toString(16)} → variante ${bot.useVariantA ? 'A' : 'B'}`);
    }
    try {
      r.i32be();
      r.u8();
      r.i32be();
      r.i32be();
      bot.entityId = r.i64be();
      r.i32be(); r.i32be(); r.i32be();
      bot.pos.x = r.f32be();
      bot.pos.y = r.f32be();
      bot.pos.z = r.f32be();
      console.log(`[${bot.nombre}] START_GAME eid=${bot.entityId} pos=(${bot.pos.x.toFixed(1)},${bot.pos.y.toFixed(1)},${bot.pos.z.toFixed(1)})`);
    } catch(e) {
      console.log(`[${bot.nombre}] START_GAME recibido (sin pos)`);
    }
    sendGame(bot, buildChunkRadius(bot));
    if (!bot.spawnFallback) {
      bot.spawnFallback = setTimeout(() => {
        if (!bot.spawned && !bot.isClosing && !tiempoTerminado) {
          console.log(`[${bot.nombre}] Fallback: forzando spawn`);
          onSpawn(bot);
        }
      }, 8000);
    }
    return;
  }

  if (pid === P70.DISCONNECT || pid === 0x05) {
    let msg = '';
    try { msg = r.str(); } catch(e) {}
    console.log(`[${bot.nombre}] Kick: "${msg || '(sin mensaje)'}"`);
    cerrarBot(bot);
    return;
  }

  if (!bot._unknownLogged) bot._unknownLogged = {};
  if (!bot._unknownLogged[pid]) {
    bot._unknownLogged[pid] = true;
    const hex = data.slice(0, Math.min(8, data.length)).toString('hex');
    console.log(`[${bot.nombre}] Pkt desconocido: 0x${pid.toString(16).padStart(2,'0')} [${hex}...]`);
  }
}

// ─── Descomprimir batch y procesar paquetes ───────────────────────────────────
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
      mcpe(bot, (pkt[0] === 0xfe && pkt.length > 1) ? pkt.slice(1) : pkt);
    }
  } catch(e) {}
}

// ─── Procesar payload de RakNet ───────────────────────────────────────────────
function innerPacket(bot, payload) {
  if (!payload || payload.length === 0 || bot.isClosing) return;
  const pid = payload[0];

  if (pid === 0x00) {
    if (payload.length >= 9) {
      const t = payload.readBigInt64BE(1);
      _rakFrame(bot, new W().u8(0x03).i64be(t).i64be(BigInt(Date.now())).buf(), false,0,0,0);
    }
    return;
  }
  if (pid === 0x03) return;
  if (pid === 0x15) { cerrarBot(bot); return; }
  if (pid === 0x10) { handleServerHandshake(bot, payload); return; }

  if (pid === 0xfe) {
    if (payload.length < 2) return;
    const next = payload[1];
    if (next === 0x06) {
      handleBatch(bot, payload.slice(2));
    } else {
      mcpe(bot, payload.slice(1));
    }
    return;
  }

  if (pid === P70.BATCH) { handleBatch(bot, payload.slice(1)); return; }
  if (pid === 0x06 && bot.proto >= 84) { handleBatch(bot, payload.slice(1)); return; }

  mcpe(bot, payload);
}

// ─── Parsear data packet RakNet ───────────────────────────────────────────────
function parseDataPkt(bot, msg) {
  if (bot.isClosing) return;
  const r   = new R(msg); r.skip(1);
  const seq = r.tLE();
  bot.ackQueue.push(seq);

  while (r.left() > 0) {
    try {
      const flags    = r.u8();
      const rel      = (flags >> 5) & 7;
      const isSplit  = (flags >> 4) & 1;
      const bits     = r.u16be();
      const blen     = Math.ceil(bits / 8);

      if ([2,3,4,6,7].includes(rel)) r.tLE();
      if ([1,3,4].includes(rel))     { r.tLE(); r.u8(); }

      let sc=0, si=0, sx=0;
      if (isSplit) { sc=r.u32be(); si=r.u16be(); sx=r.u32be(); }

      const payload = r.bytes(blen);
      if (isSplit) {
        if (!bot.splitMap.has(si)) bot.splitMap.set(si, new Array(sc).fill(null));
        bot.splitMap.get(si)[sx] = payload;
        if (bot.splitMap.get(si).every(x => x !== null)) {
          innerPacket(bot, Buffer.concat(bot.splitMap.get(si)));
          bot.splitMap.delete(si);
        }
      } else {
        innerPacket(bot, payload);
      }
    } catch(e) { break; }
  }
}

// ─── Server Handshake (New Incoming Connection 0x10) ─────────────────────────
function handleServerHandshake(bot, payload) {
  if (bot.isClosing) return;
  const r = new R(payload); r.skip(1);
  let pingTime = 0n;
  try {
    const v = r.u8(); r.skip(v===4?6:18); r.skip(2);
    for (let i=0; i<10; i++) { const x=r.u8(); r.skip(x===4?6:18); }
    pingTime = r.i64be();
  } catch(e) {}

  const hw = new W().u8(0x13);
  hw.rakIP(HOST, PORT);
  for (let i=0; i<10; i++) hw.u8(4).u8(0x80).u8(0xFF).u8(0xFF).u8(0xFE).u16be(0);
  hw.i64be(pingTime).i64be(BigInt(Date.now()));
  _rakFrame(bot, hw.buf(), false,0,0,0);

  if (bot.phase === 'HANDSHAKING') {
    bot.phase = 'LOGIN';
    console.log(`[${bot.nombre}] RakNet handshake OK → enviando login (proto ${bot.proto})`);
    setTimeout(() => {
      if (tiempoTerminado || bot.isClosing) return;
      const loginPkt = bot.proto >= 84 ? buildLogin84(bot) : buildLogin70(bot);
      sendReliableOrdered(bot, loginPkt);
    }, 100);
  }
}

// ─── Open Connection Request 1 ────────────────────────────────────────────────
function sendRequest1(bot) {
  if (!bot.sock || bot.isClosing || tiempoTerminado) return;
  const mtu     = MTU_LIST[bot.mtuIdx % MTU_LIST.length];
  bot.mtuSize   = mtu;
  const padding = Math.max(0, mtu - 28 - 1 - 16 - 1);
  const buf     = new W().u8(0x05).magic().u8(7).raw(Buffer.alloc(padding, 0)).buf();
  bot.sock.send(buf, 0, buf.length, PORT, HOST, () => {});
}

// ─── Cerrar bot ───────────────────────────────────────────────────────────────
function cerrarBot(bot) {
  if (bot.isClosing) return;
  bot.isClosing = true;
  bot.connected = false;
  bot.spawned   = false;
  clearTimeout(bot.spawnFallback);
  clearTimeout(bot.mtuRetryT);
  clearTimeout(bot.req2RetryT);
  if (bot.moveTimer)         { clearInterval(bot.moveTimer);         bot.moveTimer=null; }
  if (bot.dirTimer)          { clearInterval(bot.dirTimer);          bot.dirTimer=null; }
  if (bot.chatTimer)         { clearInterval(bot.chatTimer);         bot.chatTimer=null; }
  if (bot.keepaliveInterval) { clearInterval(bot.keepaliveInterval); bot.keepaliveInterval=null; }
  if (bot.sock) { try { bot.sock.close(); } catch(e) {} bot.sock=null; }
  console.log(`[${bot.nombre}] Desconectado`);
}

// ─── Iniciar bot ──────────────────────────────────────────────────────────────
function iniciarBot(numero) {
  const bot = {
    id: numero,
    nombre: generarNombre(NOMBRE),
    phase: 'UNCONNECTED',
    clientId: BigInt('0x' + crypto.randomBytes(8).toString('hex')),
    mtuSize: MTU_LIST[0],
    mtuIdx: 0,
    serverGUID: 0n,
    sendSeq: 0, msgIndex: 0, orderIndex: 0, splitId: 0,
    ackQueue: [], splitMap: new Map(), sentFrames: new Map(),
    entityId: 0n,
    proto: 70,
    useVariantA: false,
    resourcePackDone: false,
    pos: { x:0, y:64, z:0, yaw:0, pitch:0 },
    spawned: false, connected: false,
    moveTimer: null, dirTimer: null, chatTimer: null,
    spawnFallback: null, mtuRetryT: null, req2RetryT: null,
    keepaliveInterval: null, isClosing: false,
    registerSent: false,
    _unknownLogged: {},
  };

  bot.sock = dgram.createSocket('udp4');

  bot.sock.on('message', (msg) => {
    if (tiempoTerminado || bot.isClosing || !msg.length) return;
    const pid = msg[0];

    if (pid === 0xC0) return;
    if (pid === 0xA0) { handleNACK(bot, msg); return; }

    if (pid >= 0x80 && pid <= 0x8F) {
      parseDataPkt(bot, msg);
      if (bot.ackQueue.length && !bot.isClosing) {
        sendACK(bot, bot.ackQueue); bot.ackQueue = [];
      }
      return;
    }

    if (pid === 0x06 && bot.phase === 'CONNECTING_1') {
      if (msg.length >= 2) {
        const m = msg.readUInt16BE(msg.length - 2);
        bot.mtuSize = (m >= 576 && m <= 1500) ? m : 1400;
      }
      try {
        if (msg.length >= 25) bot.serverGUID = msg.readBigUInt64BE(17);
      } catch(e) {}

      bot.phase = 'CONNECTING_2';
      clearTimeout(bot.mtuRetryT);
      console.log(`[${bot.nombre}] Reply1 OK → MTU=${bot.mtuSize}, enviando Request2`);
      const req2std = new W().u8(0x07).magic().rakIP(HOST, PORT).u16be(bot.mtuSize).u64be(bot.clientId).buf();
      const req2alt = new W().u8(0x07).magic().rakIP(HOST, PORT).u64be(bot.clientId).u16be(bot.mtuSize).buf();
      bot.sock.send(req2std, 0, req2std.length, PORT, HOST, () => {});
      bot._req2flip = false;

      const sendReq2 = () => {
        if (bot.phase !== 'CONNECTING_2' || bot.isClosing) return;
        bot._req2flip = !bot._req2flip;
        const pkt = bot._req2flip ? req2alt : req2std;
        bot.sock.send(pkt, 0, pkt.length, PORT, HOST, () => {});
        bot.req2RetryT = setTimeout(sendReq2, 2000);
      };
      bot.req2RetryT = setTimeout(sendReq2, 2000);
      return;
    }

    if (pid === 0x08 && bot.phase === 'CONNECTING_2') {
      clearTimeout(bot.req2RetryT);
      bot.phase = 'HANDSHAKING';
      console.log(`[${bot.nombre}] Reply2 OK → enviando Client Connect`);
      _rakFrame(bot, new W().u8(0x09).u64be(bot.clientId).i64be(BigInt(Date.now())).u8(0).buf(), false,0,0,0);
      return;
    }

    if (pid === 0x1C && bot.phase === 'UNCONNECTED') {
      try {
        const r = new R(msg); r.skip(1 + 8 + 8 + 16);
        const motd  = r.bytes(r.u16be()).toString('utf8');
        const parts = motd.split(';');
        if (parts.length >= 3) {
          const p = parseInt(parts[2]);
          if (!isNaN(p) && p > 0) bot.proto = p;
        }
        const srvName = (parts[1] || '?').replace(/\n/g, ' ').replace(/§./g, '').trim().substring(0, 40);
        console.log(`[${bot.nombre}] Servidor: "${srvName}" proto=${bot.proto}`);
      } catch(e) {}
      clearTimeout(bot.mtuRetryT);
      bot.phase = 'CONNECTING_1';
      sendRequest1(bot);
      scheduleMtuRetry(bot);
      return;
    }
  });

  bot.sock.on('error', () => {});
  bot.sock.bind(0);

  const pingBuf = new W().u8(0x01).i64be(BigInt(Date.now())).magic().u64be(bot.clientId).buf();
  bot.sock.send(pingBuf, 0, pingBuf.length, PORT, HOST, () => {});

  let pingCount = 0;
  const pingInterval = setInterval(() => {
    if (bot.phase !== 'UNCONNECTED' || bot.isClosing || tiempoTerminado) {
      clearInterval(pingInterval); return;
    }
    pingCount++;
    if (pingCount >= 4) {
      clearInterval(pingInterval);
      if (bot.phase === 'UNCONNECTED') {
        console.log(`[${bot.nombre}] Sin pong, conectando directo (proto 70)`);
        bot.proto = 70;
        bot.phase = 'CONNECTING_1';
        sendRequest1(bot);
        scheduleMtuRetry(bot);
      }
      return;
    }
    const pb = new W().u8(0x01).i64be(BigInt(Date.now())).magic().u64be(bot.clientId).buf();
    bot.sock.send(pb, 0, pb.length, PORT, HOST, () => {});
  }, 500);

  bot.keepaliveInterval = setInterval(() => {
    if (tiempoTerminado || bot.isClosing) { clearInterval(bot.keepaliveInterval); return; }
    if (bot.phase === 'LOGIN' || bot.spawned) {
      _rakFrame(bot, new W().u8(0x00).i64be(BigInt(Date.now())).buf(), false,0,0,0);
    }
  }, 5000);

  return bot;
}

function scheduleMtuRetry(bot) {
  clearTimeout(bot.mtuRetryT);
  bot.mtuRetryT = setTimeout(() => {
    if (bot.phase !== 'CONNECTING_1' || bot.isClosing || tiempoTerminado) return;
    bot.mtuIdx = (bot.mtuIdx + 1) % MTU_LIST.length;
    const mtu = MTU_LIST[bot.mtuIdx];
    console.log(`[${bot.nombre}] Sin Reply1, probando MTU=${mtu}...`);
    sendRequest1(bot);
    scheduleMtuRetry(bot);
  }, 3000);
}

// ─── Tiempo límite ────────────────────────────────────────────────────────────
if (TIEMPO > 0) {
  setTimeout(() => {
    console.log(`\n[Master] ${TIEMPO}s cumplidos. Desconectando ${botsActivos.length} bots...`);
    tiempoTerminado = true;
    botsActivos.forEach(bot => {
      try {
        if (bot.sock && !bot.isClosing) {
          _rakFrame(bot, new W().u8(0x15).buf(), false,0,0,0);
          setTimeout(() => cerrarBot(bot), 200);
        } else cerrarBot(bot);
      } catch(e) { cerrarBot(bot); }
    });
    console.log(`[Master] Total conectados: ${botsConectados}`);
    setTimeout(() => process.exit(0), 1500);
  }, TIEMPO * 1000);
} else {
  console.log('[Master] Sin límite de tiempo. Ctrl+C para detener.\n');
}

// ─── Lanzar bots ─────────────────────────────────────────────────────────────
console.log(`[Master] Lanzando ${BOTS} bot(s)...`);
for (let i = 0; i < BOTS; i++) {
  setTimeout(() => { if (!tiempoTerminado) iniciarBot(i); }, i * 300);
}

process.on('SIGINT', () => {
  console.log('\n[Master] Ctrl+C — cerrando...');
  tiempoTerminado = true;
  botsActivos.forEach(bot => cerrarBot(bot));
  setTimeout(() => process.exit(0), 500);
});
