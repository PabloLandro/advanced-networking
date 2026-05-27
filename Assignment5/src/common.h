#ifndef COMMON_H_INCLUDED
#define COMMON_H_INCLUDED

#include <netinet/in.h>
#include <stdint.h>
#include <stdio.h>

#ifndef TIMEOUT_MS
#define TIMEOUT_MS		1000	/* milliseconds */
#endif

extern void set_sockfd (int s);
extern int sender();
extern int receiver();

extern int set_ipv4_address(struct sockaddr_in * addr, const char * addr_s, uint16_t port);

extern const char * snd_addr_s;
extern uint16_t snd_port;

extern const char * rcv_addr_s;
extern uint16_t rcv_port;

extern int process_args (int argc, char *argv[]);

/* Communication from/to the application layer */
extern int deliver_data_to_application(const unsigned char * buf, size_t len);
extern ssize_t take_data_from_application(unsigned char * buf, size_t len);

/* Communication from/to the network layer */
extern int send_packet(const unsigned char * buf, size_t len);
extern ssize_t receive_packet(unsigned char * buf, size_t len);

/* Logging and error reporting */
extern void print_perror(const char * msg);
extern void print_error(const char * format, ...);

#define MAX_SEGMENT_SIZE 1000

extern void status_line_on();
extern void status_line_off();

typedef void (*status_line_printer)(FILE *output);
int add_status_line_printer(status_line_printer p, unsigned priority);

void print_status_line(const char * format, ...);
extern void close_status_line();

/* Event Loop */

extern void set_timeout_ms(int t);
extern int get_timeout_ms();

extern void stop_application();
extern void resume_application();

extern void init_event_loop();

extern int start_timer();
extern void stop_timer();

/* Wait for a network packet, an application input, or both.
 * Return:
 *
 *   -1 on error
 *    0 on timeout
 *    1 on network packet event
 *    2 on application input event
 *    3 on both network packet and application input events
 */
enum event_type {
    EVENT_ERROR = -1,
    EVENT_TIMEOUT = 0,
    EVENT_PACKET = 1,
    EVENT_INPUT = 2
};

extern int event_loop();

#endif

