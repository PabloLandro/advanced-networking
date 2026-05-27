#ifndef GBN_H_INCLUDED
#define GBN_H_INCLUDED

#include <stdint.h>

#define GBN_MSS			1000	/* bytes */
#define GBN_HEADER		4	/* bytes */

#ifndef WINDOW_SIZE
#define WINDOW_SIZE		200	/* packets */
#endif

typedef uint32_t seq_t;

extern seq_t gbn_get_seq(const unsigned char * pkt);
extern void gbn_set_seq(unsigned char * pkt, seq_t s);

#endif
