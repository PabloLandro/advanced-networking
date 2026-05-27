Maximize
        obj: m

Subject To
\ min-ratio: rate_i * m <= actual_flow_i = -lambda_i, so rate_i * m + lambda_i <= 0
        10 m + lambda1 <= 0
        2 m + lambda2 <= 0
        15 m + lambda3 <= 0
\ flow balance - demand 1 (src=r1, dst=r4)
        rx1_r1_r2 - rx1_r2_r1 + rx1_r1_r3 - rx1_r3_r1 + lambda1 = 0
        x1_r1_r2 - x1_r2_r1 + x1_r1_r3 - x1_r3_r1 = -1
        rx1_r2_r1 - rx1_r1_r2 + rx1_r2_r3 - rx1_r3_r2 + rx1_r2_r4 - rx1_r4_r2 = 0
        x1_r2_r1 - x1_r1_r2 + x1_r2_r3 - x1_r3_r2 + x1_r2_r4 - x1_r4_r2 = 0
        rx1_r3_r1 - rx1_r1_r3 + rx1_r3_r2 - rx1_r2_r3 + rx1_r3_r4 - rx1_r4_r3 = 0
        x1_r3_r1 - x1_r1_r3 + x1_r3_r2 - x1_r2_r3 + x1_r3_r4 - x1_r4_r3 = 0
        rx1_r4_r2 - rx1_r2_r4 + rx1_r4_r3 - rx1_r3_r4 - lambda1 = 0
        x1_r4_r2 - x1_r2_r4 + x1_r4_r3 - x1_r3_r4 = 1
\ flow balance - demand 2 (src=r4, dst=r1)
        rx2_r1_r2 - rx2_r2_r1 + rx2_r1_r3 - rx2_r3_r1 - lambda2 = 0
        x2_r1_r2 - x2_r2_r1 + x2_r1_r3 - x2_r3_r1 = 1
        rx2_r2_r1 - rx2_r1_r2 + rx2_r2_r3 - rx2_r3_r2 + rx2_r2_r4 - rx2_r4_r2 = 0
        x2_r2_r1 - x2_r1_r2 + x2_r2_r3 - x2_r3_r2 + x2_r2_r4 - x2_r4_r2 = 0
        rx2_r3_r1 - rx2_r1_r3 + rx2_r3_r2 - rx2_r2_r3 + rx2_r3_r4 - rx2_r4_r3 = 0
        x2_r3_r1 - x2_r1_r3 + x2_r3_r2 - x2_r2_r3 + x2_r3_r4 - x2_r4_r3 = 0
        rx2_r4_r2 - rx2_r2_r4 + rx2_r4_r3 - rx2_r3_r4 + lambda2 = 0
        x2_r4_r2 - x2_r2_r4 + x2_r4_r3 - x2_r3_r4 = -1
\ flow balance - demand 3 (src=r3, dst=r4)
        rx3_r1_r2 - rx3_r2_r1 + rx3_r1_r3 - rx3_r3_r1 = 0
        x3_r1_r2 - x3_r2_r1 + x3_r1_r3 - x3_r3_r1 = 0
        rx3_r2_r1 - rx3_r1_r2 + rx3_r2_r3 - rx3_r3_r2 + rx3_r2_r4 - rx3_r4_r2 = 0
        x3_r2_r1 - x3_r1_r2 + x3_r2_r3 - x3_r3_r2 + x3_r2_r4 - x3_r4_r2 = 0
        rx3_r3_r1 - rx3_r1_r3 + rx3_r3_r2 - rx3_r2_r3 + rx3_r3_r4 - rx3_r4_r3 + lambda3 = 0
        x3_r3_r1 - x3_r1_r3 + x3_r3_r2 - x3_r2_r3 + x3_r3_r4 - x3_r4_r3 = -1
        rx3_r4_r2 - rx3_r2_r4 + rx3_r4_r3 - rx3_r3_r4 - lambda3 = 0
        x3_r4_r2 - x3_r2_r4 + x3_r4_r3 - x3_r3_r4 = 1
\ mutual exclusion: at most one outgoing / one incoming edge used per node per demand
        x1_r1_r2 + x1_r1_r3 <= 1
        x1_r2_r1 + x1_r3_r1 <= 1
        x1_r2_r1 + x1_r2_r3 + x1_r2_r4 <= 1
        x1_r1_r2 + x1_r3_r2 + x1_r4_r2 <= 1
        x1_r3_r1 + x1_r3_r2 + x1_r3_r4 <= 1
        x1_r1_r3 + x1_r2_r3 + x1_r4_r3 <= 1
        x1_r4_r2 + x1_r4_r3 <= 1
        x1_r2_r4 + x1_r3_r4 <= 1
        x2_r1_r2 + x2_r1_r3 <= 1
        x2_r2_r1 + x2_r3_r1 <= 1
        x2_r2_r1 + x2_r2_r3 + x2_r2_r4 <= 1
        x2_r1_r2 + x2_r3_r2 + x2_r4_r2 <= 1
        x2_r3_r1 + x2_r3_r2 + x2_r3_r4 <= 1
        x2_r1_r3 + x2_r2_r3 + x2_r4_r3 <= 1
        x2_r4_r2 + x2_r4_r3 <= 1
        x2_r2_r4 + x2_r3_r4 <= 1
        x3_r1_r2 + x3_r1_r3 <= 1
        x3_r2_r1 + x3_r3_r1 <= 1
        x3_r2_r1 + x3_r2_r3 + x3_r2_r4 <= 1
        x3_r1_r2 + x3_r3_r2 + x3_r4_r2 <= 1
        x3_r3_r1 + x3_r3_r2 + x3_r3_r4 <= 1
        x3_r1_r3 + x3_r2_r3 + x3_r4_r3 <= 1
        x3_r4_r2 + x3_r4_r3 <= 1
        x3_r2_r4 + x3_r3_r4 <= 1
\ link capacities
        rx1_r1_r2 + rx1_r2_r1 + rx2_r1_r2 + rx2_r2_r1 + rx3_r1_r2 + rx3_r2_r1 <= 3
        rx1_r1_r3 + rx1_r3_r1 + rx2_r1_r3 + rx2_r3_r1 + rx3_r1_r3 + rx3_r3_r1 <= 10
        rx1_r2_r3 + rx1_r3_r2 + rx2_r2_r3 + rx2_r3_r2 + rx3_r2_r3 + rx3_r3_r2 <= 8
        rx1_r2_r4 + rx1_r4_r2 + rx2_r2_r4 + rx2_r4_r2 + rx3_r2_r4 + rx3_r4_r2 <= 10
        rx1_r3_r4 + rx1_r4_r3 + rx2_r3_r4 + rx2_r4_r3 + rx3_r3_r4 + rx3_r4_r3 <= 10
\ control: rx_{i,u,v} <= capacity(u,v) * x_{i,u,v}  (big-M, M = link capacity)
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
        -inf <= lambda1
        -inf <= lambda2
        -inf <= lambda3

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
