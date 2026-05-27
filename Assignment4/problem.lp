Maximize
	obj: m
Subject to
	10 m - lambda1 <= 0
	2 m - lambda2 <= 0
	15 m - lambda3 <= 0
	rx1_r1_r2 - rx1_r2_r1 + rx1_r1_r3 - rx1_r3_r1 - lambda1 = 0
	rx1_r2_r1 - rx1_r1_r2 + rx1_r2_r3 - rx1_r3_r2 + rx1_r2_r4 - rx1_r4_r2 = 0
	rx1_r3_r1 - rx1_r1_r3 + rx1_r3_r2 - rx1_r2_r3 + rx1_r3_r4 - rx1_r4_r3 = 0
	rx1_r4_r2 - rx1_r2_r4 + rx1_r4_r3 - rx1_r3_r4 + lambda1 = 0
	rx2_r1_r2 - rx2_r2_r1 + rx2_r1_r3 - rx2_r3_r1 + lambda2 = 0
	rx2_r2_r1 - rx2_r1_r2 + rx2_r2_r3 - rx2_r3_r2 + rx2_r2_r4 - rx2_r4_r2 = 0
	rx2_r3_r1 - rx2_r1_r3 + rx2_r3_r2 - rx2_r2_r3 + rx2_r3_r4 - rx2_r4_r3 = 0
	rx2_r4_r2 - rx2_r2_r4 + rx2_r4_r3 - rx2_r3_r4 - lambda2 = 0
	rx3_r1_r2 - rx3_r2_r1 + rx3_r1_r3 - rx3_r3_r1 = 0
	rx3_r2_r1 - rx3_r1_r2 + rx3_r2_r3 - rx3_r3_r2 + rx3_r2_r4 - rx3_r4_r2 = 0
	rx3_r3_r1 - rx3_r1_r3 + rx3_r3_r2 - rx3_r2_r3 + rx3_r3_r4 - rx3_r4_r3 - lambda3 = 0
	rx3_r4_r2 - rx3_r2_r4 + rx3_r4_r3 - rx3_r3_r4 + lambda3 = 0
	x1_r1_r2 - x1_r2_r1 + x1_r1_r3 - x1_r3_r1 = 1
	x1_r2_r1 - x1_r1_r2 + x1_r2_r3 - x1_r3_r2 + x1_r2_r4 - x1_r4_r2 = 0
	x1_r3_r1 - x1_r1_r3 + x1_r3_r2 - x1_r2_r3 + x1_r3_r4 - x1_r4_r3 = 0
	x1_r4_r2 - x1_r2_r4 + x1_r4_r3 - x1_r3_r4 = -1
	x2_r1_r2 - x2_r2_r1 + x2_r1_r3 - x2_r3_r1 = -1
	x2_r2_r1 - x2_r1_r2 + x2_r2_r3 - x2_r3_r2 + x2_r2_r4 - x2_r4_r2 = 0
	x2_r3_r1 - x2_r1_r3 + x2_r3_r2 - x2_r2_r3 + x2_r3_r4 - x2_r4_r3 = 0
	x2_r4_r2 - x2_r2_r4 + x2_r4_r3 - x2_r3_r4 = 1
	x3_r1_r2 - x3_r2_r1 + x3_r1_r3 - x3_r3_r1 = 0
	x3_r2_r1 - x3_r1_r2 + x3_r2_r3 - x3_r3_r2 + x3_r2_r4 - x3_r4_r2 = 0
	x3_r3_r1 - x3_r1_r3 + x3_r3_r2 - x3_r2_r3 + x3_r3_r4 - x3_r4_r3 = 1
	x3_r4_r2 - x3_r2_r4 + x3_r4_r3 - x3_r3_r4 = -1

\ Mutual exclusion outgoing
	x1_r1_r2 + x1_r1_r3 <= 1
	x1_r2_r1 + x1_r2_r3 + x1_r2_r4 <= 1
	x1_r3_r1 + x1_r3_r2 + x1_r3_r4 <= 1
	x1_r4_r2 + x1_r4_r3 <= 1
	x2_r1_r2 + x2_r1_r3 <= 1
	x2_r2_r1 + x2_r2_r3 + x2_r2_r4 <= 1
	x2_r3_r1 + x2_r3_r2 + x2_r3_r4 <= 1
	x2_r4_r2 + x2_r4_r3 <= 1
	x3_r1_r2 + x3_r1_r3 <= 1
	x3_r2_r1 + x3_r2_r3 + x3_r2_r4 <= 1
	x3_r3_r1 + x3_r3_r2 + x3_r3_r4 <= 1
	x3_r4_r2 + x3_r4_r3 <= 1

\ Mutual exclusion incoming
	x1_r2_r1 + x1_r3_r1 <= 1
	x1_r1_r2 + x1_r3_r2 + x1_r4_r2 <= 1
	x1_r1_r3 + x1_r2_r3 + x1_r4_r3 <= 1
	x1_r2_r4 + x1_r3_r4 <= 1
	x2_r2_r1 + x2_r3_r1 <= 1
	x2_r1_r2 + x2_r3_r2 + x2_r4_r2 <= 1
	x2_r1_r3 + x2_r2_r3 + x2_r4_r3 <= 1
	x2_r2_r4 + x2_r3_r4 <= 1
	x3_r2_r1 + x3_r3_r1 <= 1
	x3_r1_r2 + x3_r3_r2 + x3_r4_r2 <= 1
	x3_r1_r3 + x3_r2_r3 + x3_r4_r3 <= 1
	x3_r2_r4 + x3_r3_r4 <= 1

\ Mutual exclusion per edge
	x1_r1_r2 + x1_r2_r1 <= 1
	x1_r1_r3 + x1_r3_r1 <= 1
	x1_r2_r3 + x1_r3_r2 <= 1
	x1_r2_r4 + x1_r4_r2 <= 1
	x1_r3_r4 + x1_r4_r3 <= 1
	x2_r1_r2 + x2_r2_r1 <= 1
	x2_r1_r3 + x2_r3_r1 <= 1
	x2_r2_r3 + x2_r3_r2 <= 1
	x2_r2_r4 + x2_r4_r2 <= 1
	x2_r3_r4 + x2_r4_r3 <= 1
	x3_r1_r2 + x3_r2_r1 <= 1
	x3_r1_r3 + x3_r3_r1 <= 1
	x3_r2_r3 + x3_r3_r2 <= 1
	x3_r2_r4 + x3_r4_r2 <= 1
	x3_r3_r4 + x3_r4_r3 <= 1

\ Link capacities constraints
	rx1_r1_r2 + rx1_r2_r1 + rx2_r1_r2 + rx2_r2_r1 + rx3_r1_r2 + rx3_r2_r1 <= 3
	rx1_r1_r3 + rx1_r3_r1 + rx2_r1_r3 + rx2_r3_r1 + rx3_r1_r3 + rx3_r3_r1 <= 10
	rx1_r2_r3 + rx1_r3_r2 + rx2_r2_r3 + rx2_r3_r2 + rx3_r2_r3 + rx3_r3_r2 <= 8
	rx1_r2_r4 + rx1_r4_r2 + rx2_r2_r4 + rx2_r4_r2 + rx3_r2_r4 + rx3_r4_r2 <= 10
	rx1_r3_r4 + rx1_r4_r3 + rx2_r3_r4 + rx2_r4_r3 + rx3_r3_r4 + rx3_r4_r3 <= 10

\ Control of real value flow variables by corresponding indicators
	rx1_r1_r2 - 3 x1_r1_r2 <= 0
	rx1_r1_r3 - 10 x1_r1_r3 <= 0
	rx1_r2_r1 - 3 x1_r2_r1 <= 0
	rx1_r2_r3 - 8 x1_r2_r3 <= 0
	rx1_r2_r4 - 10 x1_r2_r4 <= 0
	rx1_r3_r1 - 10 x1_r3_r1 <= 0
	rx1_r3_r2 - 8 x1_r3_r2 <= 0
	rx1_r3_r4 - 10 x1_r3_r4 <= 0
	rx1_r4_r2 - 10 x1_r4_r2 <= 0
	rx1_r4_r3 - 10 x1_r4_r3 <= 0
	rx2_r1_r2 - 3 x2_r1_r2 <= 0
	rx2_r1_r3 - 10 x2_r1_r3 <= 0
	rx2_r2_r1 - 3 x2_r2_r1 <= 0
	rx2_r2_r3 - 8 x2_r2_r3 <= 0
	rx2_r2_r4 - 10 x2_r2_r4 <= 0
	rx2_r3_r1 - 10 x2_r3_r1 <= 0
	rx2_r3_r2 - 8 x2_r3_r2 <= 0
	rx2_r3_r4 - 10 x2_r3_r4 <= 0
	rx2_r4_r2 - 10 x2_r4_r2 <= 0
	rx2_r4_r3 - 10 x2_r4_r3 <= 0
	rx3_r1_r2 - 3 x3_r1_r2 <= 0
	rx3_r1_r3 - 10 x3_r1_r3 <= 0
	rx3_r2_r1 - 3 x3_r2_r1 <= 0
	rx3_r2_r3 - 8 x3_r2_r3 <= 0
	rx3_r2_r4 - 10 x3_r2_r4 <= 0
	rx3_r3_r1 - 10 x3_r3_r1 <= 0
	rx3_r3_r2 - 8 x3_r3_r2 <= 0
	rx3_r3_r4 - 10 x3_r3_r4 <= 0
	rx3_r4_r2 - 10 x3_r4_r2 <= 0
	rx3_r4_r3 - 10 x3_r4_r3 <= 0
Bounds
	0 <= lambda1 <= 10
	0 <= lambda2 <= 2
	0 <= lambda3 <= 15
Binary
	x1_r1_r2
	x1_r1_r3
	x1_r2_r1
	x1_r2_r3
	x1_r2_r4
	x1_r3_r1
	x1_r3_r2
	x1_r3_r4
	x1_r4_r2
	x1_r4_r3
	x2_r1_r2
	x2_r1_r3
	x2_r2_r1
	x2_r2_r3
	x2_r2_r4
	x2_r3_r1
	x2_r3_r2
	x2_r3_r4
	x2_r4_r2
	x2_r4_r3
	x3_r1_r2
	x3_r1_r3
	x3_r2_r1
	x3_r2_r3
	x3_r2_r4
	x3_r3_r1
	x3_r3_r2
	x3_r3_r4
	x3_r4_r2
	x3_r4_r3
End
