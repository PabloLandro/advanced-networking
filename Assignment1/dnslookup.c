/*
We will implement a protocol to transmit a set of binary strings from
A to B using UDP

We will establish the following constraints:
    - max_labels_len   = 63
    - max_names_len = 255
    - max_msg_len   = 512

Out message structure will be the following:
    - Number of strings (1 byte).
    ...
    - Length of i-th string (2 bytes).
    - Content of i-th string.
    ...
*/

/*
Usage:
    ./program [options] <query> [TYPE]

    Arguments:
        query The DNS query to solve
        TYPE The DNS record type for the query. Supported values are: A, AAAA,
            MX, CNAME, NS, TXT (default: A).
    Options:
        -s <server>, --server <server>
            The IPv4 address of the DNS resolver (default: 127.0.0.5)
        -r <retries>, --retries <retries>
            The maximum number of retries before declaring failure (default: 3)
        -t <timeout>, --timeout <timeout>
            The timeout for receiving the DNS reply in seconds (default: 1s)
        -h, --help
            Display this help and exit

*/

#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>

#define MAX_STR_LEN 2000
#define MAX_STR_CNT 200
#define MAX_MSG_LEN 10000

int get_type(const char *type_str) {
    if (type_str == NULL) return 0;

    // We use strcasecmp to make it case-insensitive (e.g., "mx" or "MX")
    if (strcasecmp(type_str, "A") == 0)      return 1;
    if (strcasecmp(type_str, "NS") == 0)     return 2;
    if (strcasecmp(type_str, "CNAME") == 0)  return 5;
    if (strcasecmp(type_str, "MX") == 0)     return 15;
    if (strcasecmp(type_str, "TXT") == 0)    return 16;

    return -1; // Return -1 if the type is unknown
}

char* get_type_name(int type) {
    switch (type) {
        case 1:  return "A";
        case 2:  return "NS";
        case 5:  return "CNAME";
        case 15: return "MX";
        case 16: return "TXT";
        case 28: return "AAAA";
        default: return "UNKNOWN";
    }
}

int create_msg(unsigned char *msg, char *domainname, char *type_str) {
    // 1. Header (12 bytes)
    memset(msg, 0, 12);
    uint16_t id = htons(0x1234);
    uint16_t flags = htons(0x0100); // Recursion Desired
    uint16_t qd_count = htons(1);

    memcpy(msg, &id, 2);
    memcpy(msg + 2, &flags, 2);
    memcpy(msg + 4, &qd_count, 2);
    // Bytes 6-11 remain 0 (Correct for a query)

    // 2. Question Name (Label format)
    unsigned char *qname = msg + 12;
    int lock = 0, i;
    char temp[256]; 
    strcpy(temp, domainname);
    strcat(temp, ".");

    int qname_ptr = 0;
    for (i = 0; i < strlen(temp); i++) {
        if (temp[i] == '.') {
            qname[qname_ptr++] = i - lock;
            for (; lock < i; lock++) {
                qname[qname_ptr++] = temp[lock];
            }
            lock++;
        }
    }
    qname[qname_ptr++] = 0; // End of name

    // 3. Type and Class
    int type = get_type(type_str);
    if (type == -1) type = 1; // Default to A
    
    uint16_t qtype = htons((uint16_t)type);
    uint16_t qclass = htons(1); // Internet class

    memcpy(qname + qname_ptr, &qtype, 2);
    memcpy(qname + qname_ptr + 2, &qclass, 2);

    return 12 + qname_ptr + 4;
}

void print_response(unsigned char *msg, size_t msg_len) {
    int query_count, answer_count, authority_count, additional_count, AA;
    
    // Header parsing
    query_count = msg[4] * 256 + msg[5];
    answer_count = msg[6] * 256 + msg[7];
    authority_count = msg[8] * 256 + msg[9];
    additional_count = msg[10] * 256 + msg[11];
    
    // AA is bit 2 of byte 2 (the 10th bit of the header)
    AA = (msg[2] & 0x04) >> 2;

    printf("QUERY: %d, ANSWER: %d, AUTHORITY: %d, ADDITIONAL: %d\n\n", 
            query_count, answer_count, authority_count, additional_count);

    unsigned char *reader = &msg[12];
	char domain[256];
    // --- QUERY SECTION ---
    if (query_count) {
        printf("QUERY SECTION:\n");
        for (int i = 0; i < query_count; i++) {
            int pos = 0;
            unsigned char *curr = reader;
            
            // Parse Name
            while (*curr != 0) {
                int len = *curr++;
                for (int j = 0; j < len; j++) domain[pos++] = *curr++;
                domain[pos++] = '.';
            }
            domain[pos - 1] = '\0';
            curr++; // skip null terminator

            // FIX: Type comes FIRST (curr[0], curr[1]), Class SECOND (curr[2], curr[3])
            uint16_t type  = (curr[0] << 8) | curr[1];
            uint16_t class = (curr[2] << 8) | curr[3];

            // Print in standard format: Name  Class  Type
            printf("%s.\tIN\t%s\n", domain, get_type_name(type));
            
            reader = curr + 4;
        }
    }

    // --- ANSWER SECTION ---
    if (answer_count > 0) {
        printf("\nANSWER SECTION:\n");
        for (int i = 0; i < answer_count; i++) {
            char ans_name[256];
            unsigned char *curr = reader;

            // Handle Name/Pointer
            if ((*curr & 0xC0) == 0xC0) {
                curr += 2; 
            } else {
                while (*curr != 0) curr += (*curr + 1);
                curr++;
            }

            uint16_t type  = (curr[0] << 8) | curr[1];
            uint16_t class = (curr[2] << 8) | curr[3];
            uint32_t ttl   = (curr[4] << 24) | (curr[5] << 16) | (curr[6] << 8) | curr[7];
            uint16_t rdlen = (curr[8] << 8) | curr[9];
            curr += 10; 

            // Use your domain variable from the query or parse ans_name
            printf("%s.\t%u\tIN\t%s\t", domain, ttl, get_type_name(type));

            printf("%u.%u.%u.%u\n", curr[0], curr[1], curr[2], curr[3]);

            reader = curr + rdlen;
        }
    }
}

void print_usage(FILE *stream) {
    fprintf(stream, "Usage:\n\n"
    "./program [options] <query> [TYPE]\n\n"
    "Arguments:\n"
        " query \tThe DNS query to solve\n"
        " TYPE \tThe DNS record type for the query. Supported values are: A, AAAA,\n"
            "\tMX, CNAME, NS, TXT (default: A).\n"
    "Options:\n"
        " -s <server>, --server <server>\n"
            "\tThe IPv4 address of the DNS resolver (default: 127.0.0.5)\n"
        " -r <retries>, --retries <retries>\n"
            "\tThe maximum number of retries before declaring failure (default: 3)\n"
        " -t <timeout>, --timeout <timeout>\n"
            "\tThe timeout for receiving the DNS reply in seconds (default: 1s)\n"
        " -h, --help\n"
            "\tDisplay this help and exit\n"

    );
}

int main (int argc, char *argv[]) {
    if (argc < 2 || argc > 7) {
        print_usage(stderr);
        return EXIT_FAILURE;
    }

    // Parse command line arguments
    char server[15] = "8.8.8.8";
    int retries = 3;
    int timeout = 1;
    // Read options
    int aux = 1;
    while (argv[aux][0] == '-') {
        switch (argv[aux][1]) {
            case 'h':
                print_usage(stdin);
                aux++;
                break;
            case 's':
                // copy server address from arguments to our char array
                memcpy(server, argv[aux+1], strlen((char*)argv[aux+1]));
                aux+=2;
                break;
            case 'r':
                retries = atoi(argv[aux+1]);
                aux+=2;
            case 't':
                timeout = atoi(argv[aux+1]);
                aux+=2;
                break;
        }
    }

    char *domainname = argv[aux++];
    char *type = argv[aux];


    // 1. Set destination address
    struct sockaddr_in dns_server;
    dns_server.sin_family = AF_INET;

    // Initialize the IP address
    if (!inet_pton(AF_INET, server, &dns_server.sin_addr)) {
        perror("Invalid destination address");
        return EXIT_FAILURE;
    }

    long port = 53;

    // We also set this to as network order quantity
    dns_server.sin_port = htons(port);

    // 2. Create UDP socket

    int sockfd;

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
        perror("UDP socket couldn't be created correctly");
        return EXIT_FAILURE;
    }

    // 3. Create the message
    unsigned char msg[MAX_MSG_LEN];
    
    int len = create_msg(msg, domainname, type);
    if (len < 0) {
        return EXIT_FAILURE;
    }

    // Set the timeout on the socket once before starting
    struct timeval tv;
    tv.tv_sec = timeout;
    tv.tv_usec = 0;
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) < 0) {
        perror("Error setting timeout");
        return EXIT_FAILURE;
    }

    // 4 & 5. Send and Receive with Retries
    unsigned char buf[1024];
    struct sockaddr_in addr;
    socklen_t slen = sizeof(addr);
    int n = -1;
    int current_retry = 0;

    while (current_retry <= retries) {
        if (sendto(sockfd, msg, len, 0, (const struct sockaddr *)&dns_server, sizeof(dns_server)) < 0) {
            perror("Failed to send request");
            return EXIT_FAILURE;
        }

        n = recvfrom(sockfd, buf, sizeof(buf), 0, (struct sockaddr *) &addr, &slen);

        if (n >= 0) {
            // Success! We have a response
            print_response(buf, n);
            break;
        } else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                // Timeout occurred
                current_retry++;
                if (current_retry <= retries) {
                    printf("Timeout. Retrying (%d/%d)...\n", current_retry, retries);
                } else {
                    printf("Failed after %d retries.\n", retries);
                }
            } else {
                // A different socket error occurred
                perror("recvfrom failed");
                return EXIT_FAILURE;
            }
        }
    }

}