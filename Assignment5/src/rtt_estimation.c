#include <stdint.h> 
#include <time.h>

#include "common.h"		/* for status_perror() */
#include "gbn.h"		/* for seq_t */

#ifndef DEFAULT_RTT
#define DEFAULT_RTT		500 /* milliseconds */
#endif
#ifndef DEFAULT_RTT_DEV
#define DEFAULT_RTT_DEV		100 /* milliseconds */
#endif

/* RTT estimation
 * all values are in milliseconds
 */
static double rtt = DEFAULT_RTT;		/* current estimate of the RTT */
static double rtt_dev = DEFAULT_RTT_DEV;	/* current estimate of the dev-RTT */

static seq_t rtt_expected_ack = 0;
static struct timespec rtt_start;

void rtt_timeout_event () {
    rtt_expected_ack = 0;
}

double rtt_estimate() {
    return rtt;
}

void rtt_print_status (FILE * output) {
    fprintf(output, "rtt=%.0lf~%.0lf to_ms=%d", rtt, rtt_dev, get_timeout_ms());
}

void rtt_segment_sent (seq_t seq) {
    if (rtt_expected_ack == 0) {
	if (clock_gettime(CLOCK_MONOTONIC, &rtt_start) < 0) {
	    print_perror("failed to get current time");
	    return;
	}
	rtt_expected_ack = seq + 1;
    }
}

void rtt_ack_received (seq_t seq) {
    if (seq < rtt_expected_ack)
	return;
    if (seq == rtt_expected_ack) {
	struct timespec now;
	if (clock_gettime(CLOCK_MONOTONIC, &now) < 0) {
	    print_perror("failed to get current time");
	    return;
	}
	double current = 1000.0*(now.tv_sec - rtt_start.tv_sec)
			 + 1.0*(now.tv_nsec - rtt_start.tv_nsec)/1000000.0;
	double dev_current = (rtt > current) ? rtt - current : current - rtt;

	rtt = 0.875*rtt + 0.125*current;
	rtt_dev = 0.75*rtt_dev + 0.25*dev_current;
	set_timeout_ms(rtt + 4*rtt_dev);
    }
    rtt_expected_ack = 0;
}
