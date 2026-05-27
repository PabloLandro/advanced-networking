CFLAGS = -Wall -g

IMPL = cc

.PHONY: all
all: sender receiver

SND_OBJS = sender.o common.o gbn.o rtt_estimation.o sender_$(IMPL).o
sender: $(SND_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(SND_OBJS)

RCV_OBJS = receiver.o common.o gbn.o receiver_$(IMPL).o
receiver: $(RCV_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(RCV_OBJS)

.PHONY: clean
clean:
	rm -f sender receiver *.o

## Dependencies, generated with gcc -MM *.c
#
common.o: common.c common.h
gbn.o: gbn.c gbn.h
receiver.o: receiver.c common.h
receiver_cc.o: receiver_cc.c common.h gbn.h
rtt_estimation.o: rtt_estimation.c common.h gbn.h
sender.o: sender.c common.h
sender_timeout.o: sender_timeout.c common.h
