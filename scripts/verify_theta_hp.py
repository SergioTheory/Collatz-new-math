import mpmath as mp
import time, sys, math

# Reference values (log2|I|) from earlier double-precision runs:
# e15_out.txt (M<=1000, h=1,2,3), e13_out.txt brute (M=24 -> 1.1409*sqrt(2^23)),
# e19_results.txt (M=10000 -> 4633.249)
KNOWN = {
    (20, 1): 7.11, (30, 1): 13.54, (40, 1): 15.19, (50, 1): 23.02, (60, 1): 29.19,
    (70, 1): 31.79, (80, 1): 36.34, (90, 1): 42.54, (100, 1): 44.71, (150, 1): 68.80,
    (200, 1): 91.47, (300, 1): 138.72, (400, 1): 189.22, (500, 1): 233.67, (1000, 1): 473.48,
    (20, 2): -44.99, (100, 2): -7.84, (200, 2): 40.53, (500, 2): 181.79, (1000, 2): 420.47,
    (20, 3): 6.66, (100, 3): 45.15, (200, 3): 92.19, (500, 3): 233.81, (1000, 3): 473.04,
    (24, 1): 11.690,
    (10000, 1): 4633.249,
}


def compute_I_hp(M, h, prec):
    mp.mp.prec = prec
    mod_exact = 1 << (M + 1)
    mask = mod_exact - 1
    inv3 = pow(3, -1, mod_exact)
    two_pi = 2 * mp.pi

    inv3_pow = [0] * (M + 2)
    inv3_pow[0] = 1
    for i in range(1, M + 2):
        inv3_pow[i] = (inv3_pow[i - 1] * inv3) % mod_exact  # 3^{-i} mod 2^{M+1}

    base_phase = mp.mpf((h * inv3_pow[1]) & mask) / mod_exact
    Z = [mp.mpc(0)] * M
    Z[0] = mp.exp(mp.mpc(0, -two_pi * base_phase))

    I_mant = [None] * (M + 1)

    for j in range(1, M + 1):
        sum_Z = mp.mpc(0)
        for S in range(j - 1, M):
            sum_Z += Z[S]
        fval = (h * (((1 << M) * inv3_pow[j]) - 1)) & mask
        I_mant[j] = mp.exp(mp.mpc(0, two_pi * mp.mpf(fval) / mod_exact)) * sum_Z
        if j == M:
            break
        val = (h * inv3_pow[j + 1] * (1 << j)) & mask
        Z_curr = [mp.mpc(0)] * M
        running = mp.mpc(0)
        for S in range(1, M):
            running += Z[S - 1]
            if S >= j:
                Z_curr[S] = mp.exp(mp.mpc(0, -two_pi * mp.mpf(val) / mod_exact)) * running
                val = (val << 1) & mask
        Z = Z_curr

    total = mp.mpc(0)
    for d in range(1, M + 1):
        total += I_mant[d]
    mag = abs(total)
    log2_I = float(mp.log(mag, 2)) if mag > 0 else float('-inf')
    profile = [float(mp.log(abs(m), 2)) if m != 0 else float('-inf') for m in I_mant[1:]]
    return log2_I, profile


def main():
    print("=== INDEPENDENT HIGH-PRECISION VERIFICATION (mpmath, exact phases) ===", flush=True)
    tests = [
        (20, 1, 600), (24, 1, 600), (100, 1, 600), (200, 1, 600), (500, 1, 600),
        (1000, 1, 600), (1000, 2, 600), (1000, 3, 600),
        (2000, 1, 700), (5000, 1, 800), (10000, 1, 900),
    ]
    out = []
    for (M, h, prec) in tests:
        t0 = time.time()
        log2_I, prof = compute_I_hp(M, h, prec)
        dt = time.time() - t0
        theta = log2_I / (M - 1) if M > 1 else 0.0
        maxl = max(prof) if prof else float('-inf')
        depth = maxl - log2_I
        line = f"M={M:6d} h={h} | log2|I| = {log2_I:12.4f} | theta = {theta:.5f} | max_layer = {maxl:9.2f} | depth = {depth:7.1f} bits | time = {dt:7.1f}s"
        known = KNOWN.get((M, h))
        if known is not None:
            line += f" | double_ref = {known:9.4f} | diff = {log2_I - known:+.4f}"
        print(line, flush=True)
        out.append(line)
    with open("verify_theta_hp.txt", "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == '__main__':
    main()