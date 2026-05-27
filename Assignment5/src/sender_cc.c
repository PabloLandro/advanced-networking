#include <stddef.h>
#include <unistd.h>
#include <assert.h>

#include "common.h"
#include "gbn.h"
#include "rtt_estimation.h"

struct packet {
    size_t size;
    unsigned char bytes[GBN_HEADER + GBN_MSS];
};

enum sender_state {
    OPEN,
    CLOSING,
    CLOSED
};

int sender () {
    /* statistics and counters */
    size_t packets = 0;
    size_t acks = 0;
    size_t timeouts = 0;
    size_t segments = 0;
    size_t total_size = 0;
    size_t fast_retransmissions = 0;

    struct packet P[WINDOW_SIZE];


    seq_t base = 0;
    seq_t next_seq = 0;

    /* fast retransmission: we resend the base as soon as we get a
     * triple NACKs (duplicate, base acks).  This is to recover
     * quickly before the timeout expires.  However, we perform this
     * retransmission only once per timeout period on the same base
     * sequence number (see the use of fast_retransmit_base below).
     */
    int nack_count = 0;
    seq_t fast_retransmit_base = 0;

    enum sender_state state = OPEN;

    add_status_line_printer(rtt_print_status, 1);
    init_event_loop();

    while (state != CLOSED) {
	print_status_line("base=%u  seg=%zu  size=%zu  pkt=%zu  ack=%zu  fr=%zu  to=%zu",
			  base, segments, total_size, packets, acks, fast_retransmissions, timeouts);
	int ev = event_loop();

	if (ev == EVENT_ERROR)
	    return -1;

	if (ev == EVENT_TIMEOUT) {  	/* retransmit all pending packets */
	    ++timeouts;
	    rtt_timeout_event();
	    for (seq_t i = base; i < next_seq; ++i) {
			struct packet * pkt = &(P[i % WINDOW_SIZE]);
			if (! send_packet(pkt->bytes, pkt->size)) {
				print_perror("failed to send data to the receiver");
				return -1;
			}
			rtt_segment_sent(i);
			++packets;
	    }
	    if (start_timer() < 0)
			return -1;
	    /* reset the fast-retransmit trigger */
	    fast_retransmit_base = base;
	    nack_count = 0;
	    if (start_timer() < 0)
			return -1;
	    continue;
	}

	if (ev & EVENT_PACKET) {	/* reading ack */
	    unsigned char ack_pkt[GBN_HEADER];
	    ssize_t ack_res = receive_packet(ack_pkt, GBN_HEADER);
	    if (ack_res < 0) {
			print_perror("failed to read ack packet");
			return -1;
	    }
	    if (ack_res < GBN_HEADER) {
			print_error("invalid ack packet\n");
	    } else {
			++acks;
			seq_t ack_seq = gbn_get_seq(ack_pkt);
			rtt_ack_received(ack_seq);
			if (ack_seq == base) {
				if (++nack_count >= 3 && fast_retransmit_base <= base) {
				/* fast retransmission */
				nack_count = 0;
				fast_retransmit_base = base + 1;
				fast_retransmissions += 1;
				struct packet * pkt = &(P[base % WINDOW_SIZE]);
				if (! send_packet(pkt->bytes, pkt->size)) {
					print_perror("failed to send data to the receiver");
					return -1;
				}
				rtt_segment_sent(base);
				++packets;
				if (start_timer() < 0)
					return -1;
				}
			} else if (ack_seq > base && ack_seq <= next_seq) {	/* valid ack */
				base = ack_seq;
				nack_count = 0;
				if (base != next_seq) {
					/* we still have pending acks, so, we restart the timer */
					if (start_timer() < 0)
						return -1;
				} else if (state == CLOSING) {
					/* no more pending acks, if CLOSING, we shutdown the sender */
					state = CLOSED;
					goto sender_shutdown;
				} else {
					/* no more acks, but still taking application data */
					stop_timer();
				}
				resume_application();
			}
	    }
	}

	if (ev & EVENT_INPUT) {
	    assert(next_seq < base + WINDOW_SIZE);
	    struct packet * pkt = &(P[next_seq % WINDOW_SIZE]);
	    gbn_set_seq(pkt->bytes, next_seq);
	    ssize_t seg_len = take_data_from_application(pkt->bytes + GBN_HEADER, GBN_MSS);
	    if (seg_len < 0)
			return -1;
	    if (seg_len == 0) {
			/* No more application data: we close the stream. */
			stop_application();
			if (base != next_seq) {
				/* If we still have pending acks, we go into the
				* CLOSING state, and loop back to wait for those
				* acks and, if necessary, retransmit as ususal. */
				state = CLOSING;
			} else {
				/* No pending acks, so shutdown immediately */
				state = CLOSED;
				goto sender_shutdown;
			}
	    } else {
			pkt->size = GBN_HEADER + seg_len;
			++segments;
			total_size += seg_len;
			if (! send_packet(pkt->bytes, pkt->size)) {
				print_perror("failed to send data to the receiver");
				return -1;
			}
			++packets;
			rtt_segment_sent(next_seq);
			if (next_seq == base) 
				if (start_timer() < 0)
					return -1;
			++next_seq;
			if (next_seq == base + WINDOW_SIZE)
				stop_application();
	    }
	}
    }
	sender_shutdown:
    /* We now send the "FIN" packet.  This is just an empty packet.
     * We then immediately exit without waiting for an ack. */
    struct packet * pkt = &(P[base % WINDOW_SIZE]);
    gbn_set_seq(pkt->bytes, next_seq);
    pkt->size = GBN_HEADER;
    if (! send_packet(pkt->bytes, GBN_HEADER)) {
		print_perror("failed to send FIN packet to the receiver");
		return -1;
    }
    return 0;
}
