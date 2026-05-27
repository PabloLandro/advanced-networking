#include "gbn.h"

seq_t gbn_get_seq(const unsigned char * pkt) {
    seq_t s = pkt[0];
    for (unsigned i = 1; i < 4; ++i)
	s = (s << 8) | pkt[i];
    return s;
}

void gbn_set_seq(unsigned char * pkt, seq_t s) {
    pkt[0] = (s >> 24) & 0xff;
    pkt[1] = (s >> 16) & 0xff;
    pkt[2] = (s >> 8) & 0xff;
    pkt[3] = s & 0xff;
}

