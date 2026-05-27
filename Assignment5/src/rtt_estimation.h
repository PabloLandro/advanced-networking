#ifndef RTT_ESTIMATION_H_INCLUDED
#define RTT_ESTIMATION_H_INCLUDED

#include <stdint.h>

extern double rtt_estimate ();
extern void rtt_timeout_event ();
extern void rtt_segment_sent (uint32_t seq);
extern void rtt_ack_received (uint32_t seq);
extern void rtt_print_status (FILE * output);
#endif
