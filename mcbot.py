#!/usr/bin/env python3
"""
Bot para PocketMine-MP
Proto 70 (MCPE 0.15.x) y proto 84 (MCPE 0.16.x)

Uso:
  python bot.py <ip> <port> <nombre> <bots> <tiempo> [register] [mensajes] [intervalo]

Argumentos:
  ip          IP del servidor
  port        Puerto (normalmente 19132)
  nombre      Nombre base de los bots (se les añade sufijo aleatorio)
  bots        Cantidad de bots
  tiempo      Segundos de duracion (0 = sin limite)
  register    Como registrarse. Opciones:
                /register  → envia "/register <pass_aleatoria>"
                /r         → envia "/r <pass_aleatoria>"
                /registrar → envia "/registrar <pass_aleatoria>"
                mipass123  → envia "mipass123" tal cual (tu pones la contrasena)
                (vacio)    → no se registra
  mensajes    Texto a spamear. Usa - en vez de espacio, | para varios mensajes.
              Ejemplo: "Hola-mundo|Como-estan|Bot-activo"
  intervalo   Segundos entre cada mensaje de spam (por bot)

Ejemplos:
  python bot.py 127.0.0.1 19132 Bot 1 0
  python bot.py 127.0.0.1 19132 Bot 5 60 /r "Hola!" 3
  python bot.py 127.0.0.1 19132 Bot 3 0 /register "Hola!|Como-estan" 4
  python bot.py 127.0.0.1 19132 Bot 3 0 mipass123 "spam" 2
  python bot.py 127.0.0.1 19132 Bot 3 0 "" "solo-spam" 3
"""

import sys
import os
import random
import string
import struct
import zlib
import json
import socket
import threading
import time
import base64
import math
import signal

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

# ─── Argumentos ───────────────────────────────────────────────────────────────
HOST          = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT          = int(sys.argv[2]) if len(sys.argv) > 2 else 19132
NOMBRE        = sys.argv[3] if len(sys.argv) > 3 else 'Bot'
BOTS          = int(sys.argv[4]) if len(sys.argv) > 4 else 1
TIEMPO        = int(sys.argv[5]) if len(sys.argv) > 5 else 0
REGISTER_CMD  = sys.argv[6] if len(sys.argv) > 6 else ''
MENSAJES_RAW  = sys.argv[7] if len(sys.argv) > 7 else 'Hola!'
MSG_INTERVALO = int(sys.argv[8]) if len(sys.argv) > 8 else 5

# ─── Lógica de registro ───────────────────────────────────────────────────────
# Si el comando empieza con / → es un comando de registro, se genera pass aleatoria
# Si no empieza con / y no está vacío → es la contraseña directa, se envía tal cual
# Si está vacío → no se registra
REGISTER_USA_PASS = REGISTER_CMD.startswith('/')

def describir_registro():
    if not REGISTER_CMD:
        return '(sin registro)'
    if REGISTER_USA_PASS:
        return f'{REGISTER_CMD} <pass_aleatoria>'
    return f'"{REGISTER_CMD}" (contrasena fija)'

# ─── Procesar mensajes ────────────────────────────────────────────────────────
MENSAJES = [m.strip().replace('-', ' ') for m in MENSAJES_RAW.split('|') if m.strip()]

# ─── Estado global ────────────────────────────────────────────────────────────
bots_conectados  = 0
bots_activos     = []
tiempo_terminado = False
lock_global      = threading.Lock()

print(f"[Master] Servidor  : {HOST}:{PORT}")
print(f"[Master] Bots      : {BOTS}  nombre base: \"{NOMBRE}\"")
print(f"[Master] Tiempo    : {TIEMPO}s" if TIEMPO > 0 else "[Master] Tiempo    : ilimitado (Ctrl+C para parar)")
print(f"[Master] Registro  : {describir_registro()}")
print(f"[Master] Mensajes  : {' | '.join(MENSAJES)}  cada {MSG_INTERVALO}s")
print()

# ─── Utilidades ───────────────────────────────────────────────────────────────
CHARS = string.ascii_lowercase + string.digits

def generar_nombre(base):
    return f"{base}_{''.join(random.choices(CHARS, k=6))}"

def random_pass():
    return ''.join(random.choices(CHARS, k=8))

def construir_msg_registro():
    """Devuelve el mensaje exacto que el bot enviará para registrarse."""
    if not REGISTER_CMD:
        return None
    if REGISTER_USA_PASS:
        return f"{REGISTER_CMD} {random_pass()}"
    return REGISTER_CMD  # contraseña fija que puso el usuario

# ─── Skin de Steve (64x32 RGBA) ──────────────────────────────────────────────
def generate_steve_skin():
    buf = bytearray(64 * 32 * 4)

    def fill(x0, y0, x1, y1, r, g, b, a=255):
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * 64 + x) * 4
                buf[i] = r; buf[i+1] = g; buf[i+2] = b; buf[i+3] = a

    def px(x, y, r, g, b):
        i = (y * 64 + x) * 4
        buf[i] = r; buf[i+1] = g; buf[i+2] = b; buf[i+3] = 255

    SK = (198, 134, 66)
    HR = (92,  56,  35)
    SH = (67,  95, 175)
    PT = (53,  85, 105)
    BT = (38,  38,  38)

    fill(8,  0, 16,  8, *HR); fill(16, 0, 24,  8, *SK)
    fill( 0, 8,  8, 16, *SK); fill( 8, 8, 16, 16, *SK)
    fill(16, 8, 24, 16, *HR); fill(24, 8, 32, 16, *HR)
    fill(8, 0, 16, 4, *HR)
    fill( 9, 9, 11, 11, 255, 255, 255); px(9, 10, 33, 18, 7)
    fill(13, 9, 15, 11, 255, 255, 255); px(14, 10, 33, 18, 7)
    px(11, 11, *SK); px(12, 11, *SK)
    px(11, 12, 140, 80, 30); px(12, 12, 140, 80, 30)
    fill(10, 13, 14, 14, 140, 60, 20)
    fill(20, 16, 28, 20, *SH); fill(28, 16, 36, 20, *SH)
    fill(16, 20, 20, 32, *SH); fill(20, 20, 28, 32, *SH)
    fill(28, 20, 32, 32, *SH); fill(32, 20, 40, 32, *SH)
    fill(23, 20, 25, 32, 50, 75, 155)
    fill(44, 16, 48, 20, *SK); fill(48, 16, 52, 20, *SK)
    fill(40, 20, 44, 32, *SK); fill(44, 20, 48, 32, *SK)
    fill(48, 20, 52, 32, *SK); fill(52, 20, 56, 32, *SK)
    fill(44, 20, 48, 24, *SH); fill(40, 20, 44, 24, *SH)
    fill(48, 20, 52, 24, *SH); fill(52, 20, 56, 24, *SH)
    fill( 4, 16,  8, 20, *PT); fill( 8, 16, 12, 20, *PT)
    fill( 0, 20,  4, 32, *PT); fill( 4, 20,  8, 32, *PT)
    fill( 8, 20, 12, 32, *PT); fill(12, 20, 16, 32, *PT)
    fill( 0, 28,  4, 32, *BT); fill( 4, 28,  8, 32, *BT)
    fill( 8, 28, 12, 32, *BT); fill(12, 28, 16, 32, *BT)

    return base64.b64encode(bytes(buf)).decode('utf-8')

STEVE_SKIN = generate_steve_skin()

# ─── Writer / Reader ──────────────────────────────────────────────────────────
class W:
    def __init__(self): self.parts = []
    def u8(self, v):    self.parts.append(struct.pack('B', v & 0xFF)); return self
    def u16be(self, v): self.parts.append(struct.pack('>H', v & 0xFFFF)); return self
    def i32be(self, v): self.parts.append(struct.pack('>i', v)); return self
    def u32be(self, v): self.parts.append(struct.pack('>I', v & 0xFFFFFFFF)); return self
    def i32le(self, v): self.parts.append(struct.pack('<i', v)); return self
    def i64be(self, v): self.parts.append(struct.pack('>q', v)); return self
    def u64be(self, v): self.parts.append(struct.pack('>Q', v & 0xFFFFFFFFFFFFFFFF)); return self
    def f32be(self, v): self.parts.append(struct.pack('>f', v)); return self
    def t_le(self, v):  self.parts.append(bytes([v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF])); return self
    def raw(self, b):   self.parts.append(bytes(b)); return self
    def magic(self):    self.parts.append(MAGIC); return self
    def str_(self, s):
        b = s.encode('utf-8'); self.u16be(len(b)); self.parts.append(b); return self
    def str_raw(self, b):
        b = bytes(b); self.u16be(len(b)); self.parts.append(b); return self
    def rak_ip(self, ip, port):
        self.u8(4)
        for o in ip.split('.'): self.u8((~int(o)) & 0xFF)
        self.u16be(port); return self
    def buf(self): return b''.join(self.parts)


class R:
    def __init__(self, b): self.b = bytes(b); self.p = 0
    def left(self):   return len(self.b) - self.p
    def u8(self):     v = self.b[self.p]; self.p += 1; return v
    def u16be(self):  v = struct.unpack_from('>H', self.b, self.p)[0]; self.p += 2; return v
    def i32be(self):  v = struct.unpack_from('>i', self.b, self.p)[0]; self.p += 4; return v
    def u32be(self):  v = struct.unpack_from('>I', self.b, self.p)[0]; self.p += 4; return v
    def i64be(self):  v = struct.unpack_from('>q', self.b, self.p)[0]; self.p += 8; return v
    def u64be(self):  v = struct.unpack_from('>Q', self.b, self.p)[0]; self.p += 8; return v
    def f32be(self):  v = struct.unpack_from('>f', self.b, self.p)[0]; self.p += 4; return v
    def t_le(self):   v = self.b[self.p]|(self.b[self.p+1]<<8)|(self.b[self.p+2]<<16); self.p+=3; return v
    def bytes_(self, n): v = self.b[self.p:self.p+n]; self.p += n; return v
    def skip(self, n):   self.p += n; return self
    def str_(self):   n = self.u16be(); return self.bytes_(n).decode('utf-8', errors='replace')


MAGIC    = bytes([0x00,0xFF,0xFF,0x00,0xFE,0xFE,0xFE,0xFE,0xFD,0xFD,0xFD,0xFD,0x12,0x34,0x56,0x78])
MTU_LIST = [1492, 1464, 1400, 1200, 576]

# ─── IDs de paquetes ──────────────────────────────────────────────────────────
P70   = {'LOGIN':0x8f,'PLAY_STATUS':0x90,'DISCONNECT':0x91,'BATCH':0x92,'TEXT':0x93,'START_GAME':0x95,'MOVE_PLAYER':0x9d,'CHUNK_RADIUS':0xc9}
P84_A = {'LOGIN':0x01,'PLAY_STATUS':0x02,'DISCONNECT':0x05,'RSPACK_INFO':0x06,'RSPACK_STACK':0x07,'RSPACK_RESP':0x08,'TEXT':0x07,'START_GAME':0x09,'MOVE_PLAYER':0x10,'CHUNK_RADIUS':0x3d}
P84_B = {'LOGIN':0x01,'PLAY_STATUS':0x02,'SERVER_HS':0x03,'CLIENT_HS':0x04,'DISCONNECT':0x05,'RSPACK_INFO':0x06,'RSPACK_STACK':0x07,'RSPACK_RESP':0x08,'TEXT':0x09,'START_GAME':0x0b,'MOVE_PLAYER':0x13,'CHUNK_RADIUS':0x45}

# ─── EC Key para JWT ──────────────────────────────────────────────────────────
try:
    EC_KEY = ec.generate_private_key(ec.SECP384R1(), default_backend())
except Exception:
    EC_KEY = None

def pub_key_b64():
    if EC_KEY is None: return 'AAAA'
    return base64.b64encode(EC_KEY.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )).decode('utf-8')

def b64url(data):
    if isinstance(data, (dict, list)):
        data = json.dumps(data, separators=(',', ':')).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def der_sig_to_raw(der):
    o = 2
    rl = der[o+1]; o += 2; rr = der[o:o+rl]; o += rl
    sl = der[o+1]; o += 2; sr = der[o:o+sl]
    ra = bytearray(48); sa = bytearray(48)
    rt = rr[1:] if rr[0]==0 else rr
    st = sr[1:] if sr[0]==0 else sr
    ra[48-len(rt):] = rt; sa[48-len(st):] = st
    return bytes(ra) + bytes(sa)

def make_jwt(payload):
    pub  = pub_key_b64()
    data = b64url({'alg':'ES384','x5u':pub}) + '.' + b64url(payload)
    if EC_KEY is None: return data + '.'
    try:
        der = EC_KEY.sign(data.encode('utf-8'), ec.ECDSA(hashes.SHA384()))
        return data + '.' + base64.urlsafe_b64encode(der_sig_to_raw(der)).rstrip(b'=').decode('utf-8')
    except Exception:
        return data + '.'

# ─── Login paquetes ───────────────────────────────────────────────────────────
def build_login84(bot):
    pub  = pub_key_b64()
    uuid = '00000000-0000-4000-8000-' + os.urandom(6).hex()
    now  = int(time.time())
    chain = make_jwt({'extraData':{'displayName':bot['nombre'],'identity':uuid,'XUID':''},'identityPublicKey':pub,'nbf':now-60,'exp':now+86400})
    skin  = make_jwt({'ClientRandomId':bot['client_id']&0xFFFFFFFF,'ServerAddress':f"{HOST}:{PORT}",'SkinData':STEVE_SKIN,'SkinId':'Standard_Custom','CapeData':'','SkinGeometryName':'geometry.humanoid.custom','SkinGeometry':'','DeviceOS':1,'GameVersion':'0.15.10'})
    cb = json.dumps({'chain':[chain]}).encode('utf-8')
    sb = skin.encode('utf-8')
    raw  = W().i32le(len(cb)).raw(cb).i32le(len(sb)).raw(sb).buf()
    comp = zlib.compress(raw, level=7)
    return bytes([0xfe,0x01]) + W().i32be(84).i32be(len(comp)).raw(comp).buf()

def build_login70(bot):
    skin_buf = base64.b64decode(STEVE_SKIN)
    return (W().u8(P70['LOGIN']).str_(bot['nombre']).i32be(70).i32be(70)
               .u64be(bot['client_id']).raw(os.urandom(16))
               .str_(f"{HOST}:{PORT}").str_('').str_('Standard_Custom')
               .str_raw(skin_buf).u8(0).buf())

# ─── Batch builder ────────────────────────────────────────────────────────────
def build_batch(pkts, bot):
    inner = b''.join(struct.pack('>I', len(p)) + p for p in pkts)
    comp  = zlib.compress(inner, level=7)
    if bot['proto'] >= 84:
        return bytes([0xfe,0x06]) + W().i32be(len(comp)).raw(comp).buf()
    return W().u8(P70['BATCH']).i32be(len(comp)).raw(comp).buf()

# ─── RakNet ──────────────────────────────────────────────────────────────────
FRAME_STORE_MAX = 1024

def _udp_send(bot, buf):
    if bot['sock'] is None: return
    try: bot['sock'].sendto(buf, (HOST, PORT))
    except Exception: pass

def _rak_frame(bot, payload, is_split, split_count, split_id, split_idx):
    if bot['sock'] is None or bot['is_closing'] or tiempo_terminado: return
    seq = bot['send_seq']; bot['send_seq'] += 1
    w = W()
    w.u8(0x84).t_le(seq)
    w.u8(0x70 if is_split else 0x60)
    w.u16be(len(payload) * 8)
    mi = bot['msg_index']; bot['msg_index'] += 1
    oi = bot['order_index']; bot['order_index'] += 1
    w.t_le(mi).t_le(oi).u8(0)
    if is_split: w.u32be(split_count).u16be(split_id).u32be(split_idx)
    w.raw(payload)
    buf = w.buf()
    bot['sent_frames'][seq] = buf
    if len(bot['sent_frames']) > FRAME_STORE_MAX:
        del bot['sent_frames'][next(iter(bot['sent_frames']))]
    _udp_send(bot, buf)

def send_reliable_ordered(bot, payload):
    if bot['sock'] is None or bot['is_closing'] or tiempo_terminado: return
    MAX = (bot['mtu_size'] or 1464) - 60
    if len(payload) <= MAX:
        _rak_frame(bot, payload, False, 0, 0, 0); return
    sid = bot['split_id'] & 0xFFFF; bot['split_id'] += 1
    cnt = math.ceil(len(payload) / MAX)
    for i in range(cnt):
        _rak_frame(bot, payload[i*MAX:(i+1)*MAX], True, cnt, sid, i)

def send_game(bot, pkt):
    if bot['sock'] is None or bot['is_closing'] or tiempo_terminado: return
    send_reliable_ordered(bot, build_batch([pkt], bot))

# ─── ACK / NACK ──────────────────────────────────────────────────────────────
def send_ack(bot, nums):
    if bot['sock'] is None or bot['is_closing']: return
    sns = sorted(set(nums)); recs = []; i = 0
    while i < len(sns):
        s = e = sns[i]
        while i+1 < len(sns) and sns[i+1] == sns[i]+1: i += 1; e = sns[i]
        recs.append((s, e)); i += 1
    w = W().u8(0xC0).u16be(len(recs))
    for s, e in recs:
        w.u8(1).t_le(s) if s == e else w.u8(0).t_le(s).t_le(e)
    _udp_send(bot, w.buf())

def handle_nack(bot, msg):
    if bot['sock'] is None or bot['is_closing']: return
    try:
        r = R(msg); r.skip(1); cnt = r.u16be()
        for _ in range(cnt):
            single = r.u8(); s = r.t_le(); e = s if single else r.t_le()
            for seq in range(s, e+1):
                f = bot['sent_frames'].get(seq)
                if f and bot['sock'] and not bot['is_closing']:
                    _udp_send(bot, f)
    except Exception: pass

# ─── Paquetes de juego ────────────────────────────────────────────────────────
def get_ids(bot):
    if bot['proto'] < 84:
        return {'move':P70['MOVE_PLAYER'],'text':P70['TEXT'],'chunk':P70['CHUNK_RADIUS']}
    if bot['use_variant_a']:
        return {'move':P84_A['MOVE_PLAYER'],'text':P84_A['TEXT'],'chunk':P84_A['CHUNK_RADIUS']}
    return {'move':P84_B['MOVE_PLAYER'],'text':P84_B['TEXT'],'chunk':P84_B['CHUNK_RADIUS']}

def build_chunk_radius(bot):
    return W().u8(get_ids(bot)['chunk']).i32be(8).buf()

def build_move_player(bot):
    p = bot['pos']
    return (W().u8(get_ids(bot)['move']).i64be(bot['entity_id'])
               .f32be(p['x']).f32be(p['y']).f32be(p['z'])
               .f32be(p['yaw']).f32be(p['yaw']).f32be(p['pitch'])
               .u8(0).u8(1).buf())

def build_chat(bot, msg):
    return W().u8(get_ids(bot)['text']).u8(1).str_(bot['nombre']).str_(msg).buf()

def build_rspack_resp(bot, status):
    rid = P84_A['RSPACK_RESP'] if bot['use_variant_a'] else P84_B['RSPACK_RESP']
    return W().u8(rid).u8(status).u16be(0).buf()

# ─── Registro: solo cuando el bot ya está en el spawn (PLAY_STATUS=3) ─────────
def send_register(bot):
    """
    Envía el mensaje de registro. Lógica:
      - Si REGISTER_CMD empieza con /  → "<cmd> <pass_aleatoria>"
      - Si REGISTER_CMD es texto plano  → se envía tal cual (contraseña fija)
      - Si REGISTER_CMD está vacío      → no hace nada
    """
    if bot['register_sent'] or not REGISTER_CMD:
        return
    bot['register_sent'] = True

    msg = construir_msg_registro()

    def enviar(n):
        if bot['is_closing'] or tiempo_terminado: return
        send_game(bot, build_chat(bot, msg))
        print(f"[{bot['nombre']}] Registro #{n} -> \"{msg}\"")

    enviar(1)
    threading.Timer(0.8, lambda: enviar(2)).start()
    threading.Timer(2.0, lambda: enviar(3)).start()

# ─── Spam por bot: empieza tras MSG_INTERVALO segundos desde el spawn ─────────
def start_spam(bot):
    """
    Cada bot tiene su propio ciclo independiente.
    Espera MSG_INTERVALO segundos después del spawn y luego envía
    un mensaje cada MSG_INTERVALO segundos.
    """
    if bot['spam_active'] or bot['is_closing']: return
    bot['spam_active'] = True
    bot['spam_idx']    = 0

    def loop():
        # Esperar el intervalo antes del primer mensaje
        time.sleep(MSG_INTERVALO)
        while bot['spam_active'] and not bot['is_closing'] and not tiempo_terminado:
            msg = MENSAJES[bot['spam_idx'] % len(MENSAJES)]
            bot['spam_idx'] += 1
            send_game(bot, build_chat(bot, msg))
            print(f"[{bot['nombre']}] Spam -> \"{msg}\"")
            time.sleep(MSG_INTERVALO)
        bot['spam_active'] = False

    threading.Thread(target=loop, daemon=True).start()

# ─── Movimiento ───────────────────────────────────────────────────────────────
MOVE_TICK_S   = 0.1
MOVE_CHANGE_S = 3.0
MOVE_STEP     = 0.28
MOVE_RANGE    = 22
GRAVITY_RATE  = 0.12

def start_movement(bot):
    if bot['move_active'] or bot['is_closing']: return
    bot['move_active'] = True
    ox, oy, oz = bot['pos']['x'], bot['pos']['y'], bot['pos']['z']
    st = {'dir': random.random()*math.pi*2, 'spd': MOVE_STEP, 'velY': 0.0, 'last_dir': time.time()}

    def loop():
        while bot['move_active'] and not bot['is_closing'] and not tiempo_terminado:
            now = time.time()
            if now - st['last_dir'] >= MOVE_CHANGE_S:
                st['dir'] = random.random()*math.pi*2
                st['spd'] = MOVE_STEP*(0.6+random.random()*0.8)
                st['last_dir'] = now
            dx = bot['pos']['x']-ox; dz = bot['pos']['z']-oz
            if dx*dx + dz*dz > MOVE_RANGE*MOVE_RANGE:
                st['dir'] = math.atan2(oz-bot['pos']['z'], ox-bot['pos']['x'])
                st['spd'] = MOVE_STEP*1.2
            else:
                bot['pos']['x'] += math.cos(st['dir'])*st['spd']
                bot['pos']['z'] += math.sin(st['dir'])*st['spd']
            p = bot['pos']
            if p['y'] > oy+0.05:
                st['velY'] -= GRAVITY_RATE; p['y'] += st['velY']
                if p['y'] <= oy: p['y'] = oy; st['velY'] = 0.0
            elif p['y'] < oy-0.05:
                p['y'] += 0.2
                if p['y'] > oy: p['y'] = oy
            else:
                p['y'] = oy; st['velY'] = 0.0
            bot['pos']['yaw'] = ((st['dir']*180/math.pi)+90+360)%360
            send_game(bot, build_move_player(bot))
            time.sleep(MOVE_TICK_S)
        bot['move_active'] = False

    threading.Thread(target=loop, daemon=True).start()

# ─── Spawn: se llama con PLAY_STATUS=3 ───────────────────────────────────────
def on_spawn(bot):
    global bots_conectados
    if bot['spawned']: return
    bot['spawned'] = True
    with lock_global:
        bots_conectados += 1
        bots_activos.append(bot)
    p = bot['pos']
    print(f"[{bot['nombre']}] Spawneado pos=({p['x']:.1f},{p['y']:.1f},{p['z']:.1f}) total={bots_conectados}/{BOTS}")

    # Registro inmediato al entrar al mundo
    send_register(bot)

    # Movimiento inmediato
    start_movement(bot)

    # Spam empieza tras MSG_INTERVALO segundos (independiente por bot)
    start_spam(bot)

# ─── Procesamiento de paquetes MCPE ──────────────────────────────────────────
def mcpe(bot, data):
    if not data or bot['is_closing']: return
    pid = data[0]; r = R(data); r.skip(1)

    # PLAY_STATUS
    if pid == P70['PLAY_STATUS'] or pid == 0x02:
        st    = r.i32be()
        names = {0:'Login OK',1:'Cliente viejo',2:'Servidor lleno',3:'Spawneado',4:'Mundo viejo',5:'Cliente nuevo'}
        print(f"[{bot['nombre']}] PLAY_STATUS={st} ({names.get(st,'?')})")
        if st == 0:
            send_game(bot, build_chunk_radius(bot))
        elif st in (1, 2):
            cerrar_bot(bot)
        elif st == 3:
            # ─ Aqui es cuando el bot realmente entra al mundo ─
            on_spawn(bot)
        return

    # Resource packs proto 84 variante B
    if pid == 0x06 and bot['proto'] >= 84 and not bot['resource_pack_done'] and not bot['use_variant_a']:
        send_game(bot, build_rspack_resp(bot, 3)); return

    if pid == 0x07 and bot['proto'] >= 84 and not bot['resource_pack_done'] and not bot['use_variant_a']:
        bot['resource_pack_done'] = True
        send_game(bot, build_rspack_resp(bot, 4)); return

    # Server handshake MCPE
    if pid == 0x03 and bot['proto'] >= 84:
        send_game(bot, W().u8(0x04).buf())
        send_game(bot, build_chunk_radius(bot)); return

    # START_GAME: solo leemos posicion y pedimos chunks, NO registramos aqui
    if pid in (P70['START_GAME'], 0x09, 0x0b, 0x11):
        if bot['proto'] >= 84:
            bot['use_variant_a'] = (pid == 0x09)
        try:
            r.i32be(); r.u8(); r.i32be(); r.i32be()
            bot['entity_id'] = r.i64be()
            r.i32be(); r.i32be(); r.i32be()
            bot['pos']['x'] = r.f32be()
            bot['pos']['y'] = r.f32be()
            bot['pos']['z'] = r.f32be()
            p = bot['pos']
            print(f"[{bot['nombre']}] START_GAME eid={bot['entity_id']} pos=({p['x']:.1f},{p['y']:.1f},{p['z']:.1f})")
        except Exception:
            print(f"[{bot['nombre']}] START_GAME recibido")
        send_game(bot, build_chunk_radius(bot))
        # Fallback: si PLAY_STATUS=3 nunca llega en 10s, forzar spawn
        if bot['spawn_fallback'] is None:
            def fallback():
                if not bot['spawned'] and not bot['is_closing'] and not tiempo_terminado:
                    print(f"[{bot['nombre']}] Fallback spawn (PLAY_STATUS=3 no llego)")
                    on_spawn(bot)
            t = threading.Timer(10.0, fallback); t.daemon = True; t.start()
            bot['spawn_fallback'] = t
        return

    # Disconnect
    if pid in (P70['DISCONNECT'], 0x05):
        msg = ''
        try: msg = r.str_()
        except Exception: pass
        print(f"[{bot['nombre']}] Kick: \"{msg or '(sin mensaje)'}\"")
        cerrar_bot(bot); return

    # Paquetes desconocidos (solo logear una vez por tipo)
    if pid not in bot['unknown_logged']:
        bot['unknown_logged'].add(pid)

def handle_batch(bot, payload):
    if bot['is_closing']: return
    try:
        r = R(payload); cl = r.i32be(); comp = r.bytes_(min(cl, r.left()))
        try: inner = zlib.decompress(comp)
        except Exception: inner = zlib.decompress(comp, -15)
        ir = R(inner)
        while ir.left() >= 4:
            ln = ir.u32be()
            if ln == 0 or ln > ir.left(): break
            pkt = ir.bytes_(ln)
            mcpe(bot, pkt[1:] if pkt[0]==0xfe and len(pkt)>1 else pkt)
    except Exception: pass

def inner_packet(bot, payload):
    if not payload or bot['is_closing']: return
    pid = payload[0]
    if pid == 0x00:
        if len(payload) >= 9:
            t = struct.unpack_from('>q', payload, 1)[0]
            _rak_frame(bot, W().u8(0x03).i64be(t).i64be(int(time.time()*1000)).buf(), False,0,0,0)
        return
    if pid == 0x03: return
    if pid == 0x15: cerrar_bot(bot); return
    if pid == 0x10: handle_server_handshake(bot, payload); return
    if pid == 0xfe:
        if len(payload) < 2: return
        handle_batch(bot, payload[2:]) if payload[1]==0x06 else mcpe(bot, payload[1:])
        return
    if pid == P70['BATCH']:               handle_batch(bot, payload[1:]); return
    if pid == 0x06 and bot['proto'] >= 84: handle_batch(bot, payload[1:]); return
    mcpe(bot, payload)

def parse_data_pkt(bot, msg):
    if bot['is_closing']: return
    r = R(msg); r.skip(1); seq = r.t_le()
    bot['ack_queue'].append(seq)
    while r.left() > 0:
        try:
            flags = r.u8(); rel = (flags>>5)&7; is_split = (flags>>4)&1
            bits  = r.u16be(); blen = math.ceil(bits/8)
            if rel in (2,3,4,6,7): r.t_le()
            if rel in (1,3,4):     r.t_le(); r.u8()
            sc=si=sx=0
            if is_split: sc=r.u32be(); si=r.u16be(); sx=r.u32be()
            payload = r.bytes_(blen)
            if is_split:
                if si not in bot['split_map']: bot['split_map'][si]=[None]*sc
                bot['split_map'][si][sx] = payload
                if all(x is not None for x in bot['split_map'][si]):
                    inner_packet(bot, b''.join(bot['split_map'][si]))
                    del bot['split_map'][si]
            else:
                inner_packet(bot, payload)
        except Exception: break

def handle_server_handshake(bot, payload):
    if bot['is_closing']: return
    r = R(payload); r.skip(1); ping_time = 0
    try:
        v = r.u8(); r.skip(6 if v==4 else 18); r.skip(2)
        for _ in range(10): x = r.u8(); r.skip(6 if x==4 else 18)
        ping_time = r.i64be()
    except Exception: pass
    hw = W().u8(0x13).rak_ip(HOST, PORT)
    for _ in range(10): hw.u8(4).u8(0x80).u8(0xFF).u8(0xFF).u8(0xFE).u16be(0)
    hw.i64be(ping_time).i64be(int(time.time()*1000))
    _rak_frame(bot, hw.buf(), False,0,0,0)
    if bot['phase'] == 'HANDSHAKING':
        bot['phase'] = 'LOGIN'
        print(f"[{bot['nombre']}] Handshake OK -> login proto {bot['proto']}")
        def do_login():
            if tiempo_terminado or bot['is_closing']: return
            send_reliable_ordered(bot, build_login84(bot) if bot['proto']>=84 else build_login70(bot))
        threading.Timer(0.1, do_login).start()

def send_request1(bot):
    if bot['sock'] is None or bot['is_closing'] or tiempo_terminado: return
    mtu = MTU_LIST[bot['mtu_idx'] % len(MTU_LIST)]; bot['mtu_size'] = mtu
    padding = max(0, mtu - 28 - 1 - 16 - 1)
    _udp_send(bot, W().u8(0x05).magic().u8(7).raw(bytes(padding)).buf())

def cerrar_bot(bot):
    if bot['is_closing']: return
    bot['is_closing']  = True
    bot['connected']   = False
    bot['spawned']     = False
    bot['move_active'] = False
    bot['spam_active'] = False
    for attr in ('spawn_fallback','mtu_retry_t','req2_retry_t'):
        t = bot.get(attr)
        if t: t.cancel(); bot[attr] = None
    sock = bot['sock']; bot['sock'] = None
    if sock:
        try: sock.close()
        except Exception: pass
    print(f"[{bot['nombre']}] Desconectado")

def schedule_mtu_retry(bot):
    if bot['mtu_retry_t']: bot['mtu_retry_t'].cancel()
    def retry():
        if bot['phase'] != 'CONNECTING_1' or bot['is_closing'] or tiempo_terminado: return
        bot['mtu_idx'] = (bot['mtu_idx']+1) % len(MTU_LIST)
        print(f"[{bot['nombre']}] Sin Reply1, MTU={MTU_LIST[bot['mtu_idx']]}...")
        send_request1(bot); schedule_mtu_retry(bot)
    t = threading.Timer(3.0, retry); t.daemon=True; t.start(); bot['mtu_retry_t'] = t

# ─── Iniciar bot ──────────────────────────────────────────────────────────────
def iniciar_bot(numero):
    bot = {
        'id': numero, 'nombre': generar_nombre(NOMBRE),
        'phase': 'UNCONNECTED',
        'client_id': int.from_bytes(os.urandom(8), 'big'),
        'mtu_size': MTU_LIST[0], 'mtu_idx': 0, 'server_guid': 0,
        'send_seq': 0, 'msg_index': 0, 'order_index': 0, 'split_id': 0,
        'ack_queue': [], 'split_map': {}, 'sent_frames': {},
        'entity_id': 0, 'proto': 70, 'use_variant_a': False,
        'resource_pack_done': False,
        'pos': {'x':0.,'y':64.,'z':0.,'yaw':0.,'pitch':0.},
        'spawned': False, 'connected': False,
        'move_active': False, 'spam_active': False, 'spam_idx': 0,
        'spawn_fallback': None, 'mtu_retry_t': None, 'req2_retry_t': None,
        'is_closing': False, 'register_sent': False,
        'unknown_logged': set(), 'sock': None, '_req2flip': False,
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind(('', 0))
    bot['sock'] = sock

    def recv_loop():
        while not bot['is_closing'] and not tiempo_terminado:
            try:
                msg, _ = sock.recvfrom(65535)
            except BlockingIOError:
                time.sleep(0.001); continue
            except Exception:
                break
            if not msg: continue
            pid = msg[0]

            if pid == 0xC0: continue
            if pid == 0xA0: handle_nack(bot, msg); continue
            if 0x80 <= pid <= 0x8F:
                parse_data_pkt(bot, msg)
                if bot['ack_queue'] and not bot['is_closing']:
                    send_ack(bot, bot['ack_queue']); bot['ack_queue'] = []
                continue

            if pid == 0x06 and bot['phase'] == 'CONNECTING_1':
                if len(msg) >= 2:
                    m = struct.unpack_from('>H', msg, len(msg)-2)[0]
                    bot['mtu_size'] = m if 576 <= m <= 1500 else 1400
                try:
                    if len(msg) >= 25: bot['server_guid'] = struct.unpack_from('>Q', msg, 17)[0]
                except Exception: pass
                bot['phase'] = 'CONNECTING_2'
                if bot['mtu_retry_t']: bot['mtu_retry_t'].cancel(); bot['mtu_retry_t'] = None
                print(f"[{bot['nombre']}] Reply1 MTU={bot['mtu_size']} -> Request2")
                req2std = W().u8(0x07).magic().rak_ip(HOST,PORT).u16be(bot['mtu_size']).u64be(bot['client_id']).buf()
                req2alt = W().u8(0x07).magic().rak_ip(HOST,PORT).u64be(bot['client_id']).u16be(bot['mtu_size']).buf()
                _udp_send(bot, req2std); bot['_req2flip'] = False
                def send_req2():
                    if bot['phase']!='CONNECTING_2' or bot['is_closing']: return
                    bot['_req2flip'] = not bot['_req2flip']
                    _udp_send(bot, req2alt if bot['_req2flip'] else req2std)
                    t = threading.Timer(2.0, send_req2); t.daemon=True; t.start(); bot['req2_retry_t']=t
                t = threading.Timer(2.0, send_req2); t.daemon=True; t.start(); bot['req2_retry_t']=t
                continue

            if pid == 0x08 and bot['phase'] == 'CONNECTING_2':
                if bot['req2_retry_t']: bot['req2_retry_t'].cancel(); bot['req2_retry_t'] = None
                bot['phase'] = 'HANDSHAKING'
                print(f"[{bot['nombre']}] Reply2 OK -> Client Connect")
                _rak_frame(bot, W().u8(0x09).u64be(bot['client_id']).i64be(int(time.time()*1000)).u8(0).buf(), False,0,0,0)
                continue

            if pid == 0x1C and bot['phase'] == 'UNCONNECTED':
                try:
                    r2 = R(msg); r2.skip(1+8+8+16)
                    motd  = r2.bytes_(r2.u16be()).decode('utf-8', errors='replace')
                    parts = motd.split(';')
                    if len(parts) >= 3 and parts[2].isdigit():
                        p = int(parts[2])
                        if p > 0: bot['proto'] = p
                    srv = (parts[1] if len(parts)>1 else '?').strip()[:40]
                    print(f"[{bot['nombre']}] Server: \"{srv}\" proto={bot['proto']}")
                except Exception: pass
                if bot['mtu_retry_t']: bot['mtu_retry_t'].cancel(); bot['mtu_retry_t'] = None
                bot['phase'] = 'CONNECTING_1'
                send_request1(bot); schedule_mtu_retry(bot)
                continue

    threading.Thread(target=recv_loop, daemon=True).start()

    _udp_send(bot, W().u8(0x01).i64be(int(time.time()*1000)).magic().u64be(bot['client_id']).buf())

    ping_count = [0]
    def ping_loop():
        while bot['phase']=='UNCONNECTED' and not bot['is_closing'] and not tiempo_terminado:
            time.sleep(0.5); ping_count[0] += 1
            if ping_count[0] >= 4:
                if bot['phase']=='UNCONNECTED':
                    print(f"[{bot['nombre']}] Sin pong -> proto 70 directo")
                    bot['proto']=70; bot['phase']='CONNECTING_1'
                    send_request1(bot); schedule_mtu_retry(bot)
                return
            _udp_send(bot, W().u8(0x01).i64be(int(time.time()*1000)).magic().u64be(bot['client_id']).buf())
    threading.Thread(target=ping_loop, daemon=True).start()

    def keepalive():
        while not bot['is_closing'] and not tiempo_terminado:
            time.sleep(5.0)
            if bot['is_closing'] or tiempo_terminado: break
            if bot['phase']=='LOGIN' or bot['spawned']:
                _rak_frame(bot, W().u8(0x00).i64be(int(time.time()*1000)).buf(), False,0,0,0)
    threading.Thread(target=keepalive, daemon=True).start()

    return bot

# ─── Tiempo limite ────────────────────────────────────────────────────────────
def tiempo_limite():
    global tiempo_terminado
    time.sleep(TIEMPO)
    print(f"\n[Master] {TIEMPO}s cumplidos — desconectando {len(bots_activos)} bots...")
    tiempo_terminado = True
    for bot in list(bots_activos):
        try:
            if bot['sock'] and not bot['is_closing']:
                _rak_frame(bot, W().u8(0x15).buf(), False,0,0,0)
                threading.Timer(0.2, lambda b=bot: cerrar_bot(b)).start()
            else:
                cerrar_bot(bot)
        except Exception:
            cerrar_bot(bot)
    print(f"[Master] Total conectados: {bots_conectados}")
    time.sleep(1.5); os._exit(0)

if TIEMPO > 0:
    threading.Thread(target=tiempo_limite, daemon=True).start()
else:
    print('[Master] Sin limite. Ctrl+C para parar.\n')

# ─── Señal Ctrl+C ─────────────────────────────────────────────────────────────
def signal_handler(sig, frame):
    global tiempo_terminado
    print('\n[Master] Ctrl+C — cerrando...')
    tiempo_terminado = True
    for bot in list(bots_activos): cerrar_bot(bot)
    time.sleep(0.5); os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ─── Lanzar bots ─────────────────────────────────────────────────────────────
print(f"[Master] Lanzando {BOTS} bot(s)...\n")
for i in range(BOTS):
    threading.Timer(i * 0.3, lambda idx=i: iniciar_bot(idx) if not tiempo_terminado else None).start()

try:
    while True: time.sleep(1)
except SystemExit:
    pass
