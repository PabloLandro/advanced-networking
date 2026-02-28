/*
We will implement a protocol to transmit a set of binary strings from
A to B using UDP

We will establish the following constraints:
    - max_str_len   = 2000
    - max_str_count = 200
    - max_msg_len   = 10000

Out message structure will be the following:
    - Number of strings (1 byte).
    ...
    - Length of i-th string (2 bytes).
    - Content of i-th string.
    ...
*/

/*
Usage:
    ./program dest_ip dest_port [S1 S2 ...]
*/

#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#define MAX_STR_LEN 2000
#define MAX_STR_CNT 200
#define MAX_MSG_LEN 10000

int create_msg (unsigned char *msg, size_t max_len, int S_len, char *S[]) {
    assert (max_len > 0);
    if (S_len < 0 || S_len > MAX_STR_CNT) {
        fprintf(stderr, "max total length exceeded\n");
        return EXIT_FAILURE;
    }
    msg[0] = S_len;
    size_t offset = 1;
    for (int i = 0; i < S_len; i++) {
        size_t len = strlen(S[i]);
        if (offset + len + 2 > max_len) {
            fprintf(stderr, "maximal total length exceeded\n");
            return EXIT_FAILURE;
        }
        if (len > MAX_STR_CNT) {
            fprintf(stderr, "invalid string length\n");
            return EXIT_FAILURE;
        }
        msg[offset++] = len / 256; //(len << 8)
        msg[offset++] = len % 256;
        memcpy(msg + offset, S[i], len);
        offset += len;
    }
    return 0;
}

int main (int argc, char *argv[]) {

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <dst_ip> <dst_port>\n", argv[0]);
        return EXIT_FAILURE;
    }

    // 1. Set destination address
    struct sockaddr_in dns_server;
    dns_server.sin_family = AF_INET;

    // Initialize the IP address
    if (!inet_pton(AF_INET, argv[1], &dns_server.sin_addr)) {
        perror("Invalid destination address");
        return EXIT_FAILURE;
    }

    long port = strtol(argv[2], NULL, 10);

    if (errno != 0 || port < 0 || port > 65535) {
        perror("Invalud port number");
        return EXIT_FAILURE;
    }

    // We also set this to as network order quantity
    dns_server.sin_port = htons(port);

    // 2. Create UDP socket

    int sockfd;

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
        perror("UDP socket couldn't be created correctly");
        return EXIT_FAILURE;
    }

    if (bind(sockfd, &dns_server, 0) == -1) {
        perror("Socket couldn't be bound correctly");
        return EXIT_FAILURE;
    }

    // 3. Create the message
    unsigned char msg[MAX_MSG_LEN];
    
    int len = create_msg(msg, MAX_MSG_LEN, argc-3, argv+3);
    if (len < 0) {
        return EXIT_FAILURE;
    }

    // 4. Send the message to the set address

    sendto(sockfd ,msg, len, 0, (struct sockdaddr *)&dns_server, 0);
}