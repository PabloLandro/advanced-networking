#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include <errno.h>
#include <unistd.h>
#include <poll.h>
#include <time.h>

#include "common.h"

static int sockfd = -1;
void set_sockfd (int s) {
    sockfd = s;
}

int set_ipv4_address(struct sockaddr_in * addr, const char * addr_s, uint16_t port) {
    /* Convert the address of the client to a string */
    memset(addr, 0, sizeof(*addr));
    if (inet_pton(AF_INET, addr_s, &addr->sin_addr) != 1) {
	fprintf(stderr, "invalid IPv4 address: %s\n", addr_s);
	return -1;
    }
    addr->sin_family = AF_INET;
    addr->sin_port = htons(port);
    return 0;
}

static int verbose = 0;

const char * snd_addr_s;
uint16_t snd_port = 3456;

const char * rcv_addr_s;
uint16_t rcv_port = 6543;

static char ** arg_vector;
static int arg_count;

int process_args (int argc, char *argv[]) {
    arg_vector = argv + 1;
    arg_count = arg_count;
    for (int i = 1; i < argc; ++i) {
	if (strncmp(argv[i], "ra=", 3) == 0) {
	    rcv_addr_s = argv[i] + 3;
	} else if (strncmp(argv[i], "rp=", 3) == 0) {
	    rcv_port = strtoul(argv[i] + 3, 0, 10);
	} else if (strncmp(argv[i], "sa=", 3) == 0) {
	    snd_addr_s = argv[i] + 3;
	} else if (strncmp(argv[i], "sp=", 3) == 0) {
	    snd_port = strtoul(argv[i] + 3, 0, 10);
	} else if (strcmp(argv[i], "-v") == 0) {
	    verbose = 1;
	} else {
	    fprintf(stderr,
                    "usage: %s [options]\n"
		    "options:\n"
		    "\tsa=<sender-addr>]\t\tIPv4 address of the sender\n"
		    "\tra=<receiver-addr>]\t\tIPv4 address of the receiver\n"
		    "\tsp=<sender-port>]\t\tport number of the sender (defailt 3456)\n"
		    "\trp=<receiver-port>]\t\tport number of the receiver (defailt 6543)\n"
		    "\t-v\t\t\t\t log transport-level actions onto standard error.\n",
		    argv[0]);
	    return -1;
	}
    }
    return 0;
}

ssize_t take_data_from_application(unsigned char * buf, size_t len) {
    ssize_t seg_len = read(STDIN_FILENO, buf, len);
    if (seg_len < 0) {
        print_perror("failed to read data from the standard input");
        return -1;
    }
    return seg_len;
}

int deliver_data_to_application(const unsigned char * buf, size_t len) {
    for (size_t written = 0; written < len;) {
	ssize_t w_res = write(STDOUT_FILENO, buf + written, len - written);
	if (w_res < 0) {
	    print_perror("failed to write to standard output");
	    return 0;
	}
	written += w_res;
    }
    return 1;
}

int send_packet(const unsigned char * buf, size_t len) {
    if (send(sockfd, buf, len, 0) < 0) {
        print_perror("failed to send network packet");
	return 0;
    }
    return 1;
}

ssize_t receive_packet(unsigned char * buf, size_t len) {
    return recv(sockfd, buf, len, 0);
}

#define MAX_SLP 100

struct sl_printer {
    status_line_printer printer;
    unsigned priority;
};

static unsigned SL_len = 0;
static struct sl_printer SL[MAX_SLP];

int add_status_line_printer(status_line_printer p, unsigned priority) {
    if (SL_len < MAX_SLP) {
	/* insertion-sort... */
	unsigned i = SL_len;
	while (i > 0 && SL[i-1].priority > priority) {
	    SL[i].printer = SL[i-1].printer;
	    SL[i].priority = SL[i-1].priority;
	    --i;
	}
	SL[i].printer = p;
	SL[i].priority = priority;
	++SL_len;
	return 1;
    }
    return 0;
}

FILE * sl_output = 0;

void set_status_line_output(FILE * output) {
    sl_output = output;
}

void print_perror(const char * msg) {
    int error_code = errno;
    if (verbose)
	 close_status_line();
    if (errno == 0)
	fprintf(stderr, "%s\n", msg);
    else
	fprintf(stderr, "%s: %s\n", msg, strerror(error_code));
}

void print_error(const char * format, ...) {
    if (verbose)
	 close_status_line();
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    fprintf(stderr, "\n");
}

void print_status_line(const char * format, ...) {
    if (verbose) {
	FILE * output = sl_output ? sl_output : stderr;
	va_list args;
	va_start(args, format);
	fprintf(output, " ");
	vfprintf(output, format, args);
	for (const struct sl_printer * p = SL; p != SL + SL_len; ++p) {
	    fprintf(output, "  ");
	    p->printer(output);
	}
	fprintf(output, "\r");
	fflush(output);
    }
}

void close_status_line() {
    if (verbose) {
	FILE * output = sl_output ? sl_output : stderr;
	fprintf(output,"\n");
    }    
};

/* Event Loop */
static int timeout_ms = TIMEOUT_MS;
void set_timeout_ms(int t) {
    timeout_ms = t;
}

int get_timeout_ms() {
    return timeout_ms;
}

int poll_stdin = 1;
void stop_application() {
    poll_stdin = 0;
}

void resume_application() {
    poll_stdin = 1;
}

struct pollfd pollfds[2];

void init_event_loop() {
    pollfds[0].fd = sockfd;
    pollfds[0].events = POLLIN | POLLERR | POLLHUP;
    pollfds[1].fd = STDIN_FILENO;
    pollfds[1].events = POLLIN | POLLERR | POLLHUP;
}

struct timespec timer_start;
int timer_active = 0;
int start_timer() {
    if (clock_gettime (CLOCK_MONOTONIC, &timer_start) < 0) {
	print_perror("could not get current time");
	return -1;
    }
    timer_active = 1;
    return 0;
}

void stop_timer() {
    timer_active = 0;
}

/* Wait for a network packet, an application input, or both.
 * Return:
 *
 *   -1 on error
 *    0 on timeout
 *    1 on network packet event
 *    2 on application input event
 *    3 on both network packet and application input events
 */
int event_loop() {
    int poll_timeout;
    if (timer_active) {
	struct timespec now;
	if (clock_gettime(CLOCK_MONOTONIC, &now) < 0) {
	    print_perror("failed to get current time");
	    return -1;
	}
	int elapsed = 1000*(now.tv_sec - timer_start.tv_sec)
		      + (now.tv_nsec - timer_start.tv_nsec)/1000000;
	if (elapsed >= timeout_ms)
	    return EVENT_TIMEOUT;
	poll_timeout = timeout_ms - elapsed;
    } else {
	poll_timeout = -1;
    }
    nfds_t nfds = poll_stdin ? 2 : 1;
    int poll_res = poll(pollfds, nfds, poll_timeout);
    if (poll_res < 0) {
	print_perror("failure while polling to receive ack from receiver");
	return -1;
    }
    if (poll_res == 0)
	return EVENT_TIMEOUT;
    /* check socket first */
    if (pollfds[0].revents & (POLLERR | POLLHUP)) {
	print_error("errors on socket\n");
	return -1;
    }
    int res = 0;
    if (pollfds[0].revents & POLLIN)
	res |= EVENT_PACKET;
    if (poll_stdin) {
	if (pollfds[1].revents & (POLLERR | POLLHUP)) {
	    print_error("errors on stdin\n");
	    return -1;
	}
	if (pollfds[1].revents & POLLIN)
	    res |= EVENT_INPUT;
    }
    return res;
}
