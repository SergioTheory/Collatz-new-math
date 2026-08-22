import expedition_B_lift as B

x_core, S, d = B.compute_R2(B.get_zone2_core())

# Let's run collatz_peak from crt_solver
def collatz_peak(n, max_steps=2000000):
    ob = n.bit_length()
    cur = n
    pb = ob
    s = 0
    while cur > 1 and s < max_steps:
        cur = cur * 3 + 1 if (cur & 1) else (cur >> 1)
        s += 1
        cb = cur.bit_length()
        if cb > pb: pb = cb
    return pb, s, (cur <= 1)

pb, s, conv = collatz_peak(x_core)
print(f"Full trajectory:")
print(f"Start bits: {x_core.bit_length()}")
print(f"Peak bits: {pb}")
print(f"Total steps: {s}")
print(f"Ratio (Start/Steps): {x_core.bit_length() / s:.4f}")
print(f"Ratio (Peak/Steps): {pb / s:.4f}")
