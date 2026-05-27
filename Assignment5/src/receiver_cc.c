#include <stddef.h>
#include <unistd.h>
#include <assert.h>

#include "common.h"
#include "gbn.h"

struct packet {
    size_t size;		/* total size, including header */
    unsigned char bytes[GBN_HEADER + GBN_MSS];
    struct packet * next;	/* next available buffer, in free list */
};

#define PKT_BUF_SIZE 500

struct packet P_storage[PKT_BUF_SIZE];
struct packet * P[PKT_BUF_SIZE];
struct packet * free_packets = 0;

struct packet * allocate_packet_buffer() {
    assert(free_packets);
    struct packet * p = free_packets;
    free_packets = free_packets->next;
    return p;
}

void free_packet_buffer(struct packet * p) {
    p->next = free_packets;
    free_packets = p;
}

enum receiver_state {
    OPEN = 0,
    CLOSING = 1,
    CLOSED = 2
};

int receiver () {
    /* stats/counters */
    size_t packets = 0;
    size_t segments = 0;
    size_t seq_violations = 0;
    size_t total_size = 0;
    
    seq_t expected_seq = 0;

    unsigned char ack_pkt[GBN_HEADER];

    for (int i = 0; i < PKT_BUF_SIZE; ++i) {
	P_storage[i].next = free_packets;
	free_packets = &(P_storage[i]);
    }
    for (int i = 0; i < PKT_BUF_SIZE; ++i)
	P[i] = 0;

    enum receiver_state state = OPEN;
    while (state == OPEN) {
	print_status_line("seg=%zu  size=%zu  pkt=%zu  expected=%u  seq_err=%zu\r",
			  segments, total_size, packets, expected_seq, seq_violations);
	/* extract packet buffer p from the free list */
	struct packet * p = allocate_packet_buffer(); 
	ssize_t pkt_len = receive_packet(p->bytes, GBN_HEADER + GBN_MSS);
	if (pkt_len < 0) {
	    print_perror("failed to receive network packet");
            return -1;
	}
	if (pkt_len == 0) {
	    fprintf(stderr, "received invalid, zero-length packet from sender\n");
	    return -1;
	}
	if (pkt_len < GBN_HEADER) {
	    fprintf(stderr, "received invalid packet\n");
            return -1;
	}
	++packets;
	p->size = pkt_len;
	seq_t seg_seq = gbn_get_seq(p->bytes);
	if (seg_seq != expected_seq) {
	    ++seq_violations;
	    gbn_set_seq(ack_pkt, expected_seq);
	    if (! send_packet(ack_pkt, GBN_HEADER)) {
		print_perror("failed to send ack to sender");
		return -1;
	    }
	    if (seg_seq > expected_seq && free_packets != 0) {
		/* it's a seq number in the future, and we have space to
		   store the packet */
		P[seg_seq % PKT_BUF_SIZE] = p;
	    } else {
		free_packet_buffer(p);
	    }
	} else {		/* in-sequence segment */
	    do {
		++segments;
		size_t seg_len = p->size - GBN_HEADER;
		total_size += seg_len;
		/* deliver the data segment in p to the application */
		if (! deliver_data_to_application(p->bytes, seg_len)) {
		    print_perror("failed to send data packet to receiver");
		    return -1;
		}
		P[expected_seq % PKT_BUF_SIZE] = 0;
		/* check whether this was the last packet */
		if (seg_len == 0) 
		    state = CLOSING;
		/* recycle p */
		free_packet_buffer(p);
		++expected_seq;
		p = P[expected_seq % PKT_BUF_SIZE];
	    } while (p != 0);
	    gbn_set_seq(ack_pkt, expected_seq);
	    if (! send_packet(ack_pkt, GBN_HEADER)) {
		print_perror("failed to send ack to sender");
		return -1;
	    }
	}
    }
    return 0;
}

