# E6: polymer recursion (closed, 1-D) on the powers-of-two family.
# M(n, s) := mu_hat_n(2^s mod 3^n)
#   = sum_{a>=1} 2^{-a} * exp(-2*pi*i * (2^{s-a} mod 3^n)/3^n) * M(n-1, s-a)
# Band truncation: s in [-R, s_max]; error <= n * 2^{-(s+R)}.
# Negative exponents use modular inverse (pow(inv2, k, 3^n)).
# Base: M(0, s) = 1.
#
# Verification:
#   (a) brute-force IFS distribution for n <= 9 vs recursion (all s in band),
#   (b) anchors n=11,12,16,18 from journal E5.
# Outputs: c_cert(n)=min_s -ln|M(n,s)|/n, s*(n), s*/n, landscape f_n(beta).

import numpy as np
import json
import time

R = 120
A_MAX = 150
BETA_HI = 1.85
MARGIN = 40
N_MAX = 400

LO = -R
HI = int(np.floor(BETA_HI * N_MAX)) + MARGIN
NIDX = HI - LO + 1
JL = -R - A_MAX  # lowest source index j = s-a needed

print(f"band t in [{LO},{HI}], src j in [{JL},{HI}], A_MAX={A_MAX}")

# ---------------------------------------------------------------- brute force
def brute_force(n, s_list, a_max=60):
    """Exact IFS distribution on Z/3^n and mu_hat at xi = 2^s mod 3^n."""
    probs = {0: 1.0}
    for m in range(1, n + 1):
        p3 = 3 ** m
        inv2 = (p3 + 1) // 2
        new = {}
        for x, w in probs.items():
            base = (3 * x + 1) % p3
            for a in range(1, a_max + 1):
                y = (base * pow(inv2, a, p3)) % p3
                new[y] = new.get(y, 0.0) + w * 2 ** (-a)
        probs = new
    p3 = 3 ** n
    inv2 = (p3 + 1) // 2
    out = {}
    for s in s_list:
        xi = pow(2, s, p3) if s >= 0 else pow(inv2, -s, p3)
        val = sum(w * np.exp(-2j * np.pi * xi * x / p3) for x, w in probs.items())
        out[s] = val
    return out

# ---------------------------------------------------------------- recursion
M = np.ones(NIDX, dtype=np.complex128)  # level 0

cache = {}
results = []  # dicts for each n
landscape = {}  # n -> {beta -> -ln|M|/n}

for n in range(1, N_MAX + 1):
    p3 = 3 ** n
    inv2 = (p3 + 1) // 2
    # r_int[j] = 2^j mod 3^n for j in [JL, HI]
    r_int = np.empty(HI - JL + 1, dtype=object)
    # j >= 0
    v = 1
    for j in range(0, HI + 1):
        r_int[j - JL] = v
        v = (v * 2) % p3
    # j < 0
    v = 1
    for j in range(-1, JL - 1, -1):
        v = (v * inv2) % p3
        r_int[j - JL] = v
    r_float = r_int.astype(np.float64) / float(p3)
    phase = np.exp(-2j * np.pi * r_float)  # indexed by j - JL

    Mnew = np.zeros(NIDX, dtype=np.complex128)
    for a in range(1, A_MAX + 1):
        if LO + a > HI:
            break
        t_idx = np.arange(LO + a - LO, HI + 1 - LO)          # s idx in [a, NIDX-1]
        j_idx = t_idx - a                                     # j = s-a in [0, NIDX-1-a]
        Mnew[t_idx] += (2.0 ** (-a)) * phase[j_idx + (LO - JL)] * M[j_idx]
    M = Mnew

    # c_cert over s >= 0 (exact; for s<0 band truncation distorts)
    smax_n = int(np.floor(BETA_HI * n)) + MARGIN
    s_arr = np.arange(0, smax_n + 1)
    idx = s_arr - LO
    absM = np.abs(M[idx])
    logabs = np.where(absM > 1e-300, -np.log(absM), 300.0)
    c_arr = logabs / n
    kmin = int(np.argmin(c_arr))
    s_star = int(s_arr[kmin])
    c_cert = float(c_arr[kmin])
    results.append({"n": n, "c_cert": c_cert, "s*": s_star, "s*/n": s_star / n})

    if n in (50, 100, 150, 200, 250, 300, 400) or n <= 40:
        lp = {}
        for beta in np.arange(0.9, 1.71, 0.02):
            s = int(np.floor(beta * n))
            if s <= smax_n:
                lp[round(float(beta), 2)] = float(-np.log(max(absM[s], 1e-300)) / n)
        landscape[n] = lp

    if n in (11, 12, 16, 18) and n <= N_MAX:
        pass  # printed below

# ---------------------------------------------------------------- anchors
anchors = {11: (0.31307, 13), 12: (0.30268, 14), 16: (0.26298, 20), 18: (0.24894, 23)}
print("\n=== anchors vs recursion ===")
for n, (c_ref, s_ref) in anchors.items():
    row = results[n - 1]
    print(f"n={n}: rec c_cert={row['c_cert']:.6f} s*={row['s*']}  |  ref c={c_ref} s*={s_ref}  "
          f"dc={abs(row['c_cert']-c_ref):.2e} ds={abs(row['s*']-s_ref)}")

# ---------------------------------------------------------------- brute check
print("\n=== brute-force check (IFS distribution) ===")
for n in (2, 3, 5, 7, 9):
    s_list = [0, 1, 2, 3, 5, 8, 13]
    bf = brute_force(n, s_list)
    maxerr = 0.0
    for s in s_list:
        # recompute recursion value at exact level n via memoized run
        cache.clear()
        def Mrec(nn, ss, A=A_MAX):
            if nn == 0:
                return 1.0
            key = (nn, ss)
            if key in cache:
                return cache[key]
            p3 = 3 ** nn
            inv2 = (p3 + 1) // 2
            tot = 0j
            for a in range(1, A + 1):
                j = ss - a
                r = pow(2, j, p3) if j >= 0 else pow(inv2, -j, p3)
                tot += 2.0 ** (-a) * np.exp(-2j * np.pi * r / p3) * Mrec(nn - 1, j, A)
            cache[key] = tot
            return tot
        maxerr = max(maxerr, abs(Mrec(n, s) - bf[s]))
    print(f"n={n}: max |rec-brute| = {maxerr:.2e}")
    cache.clear()

# ---------------------------------------------------------------- tables
print("\n=== c_cert(n) table ===")
print("n    c_cert       s*   s*/n")
for row in results:
    if row["n"] % 10 == 0 or row["n"] in (11, 12, 13, 14, 15, 16, 18, 20, 25, 30, 35, 40, 50, 60, 80, 100, 120, 140, 160, 180, 200):
        print(f"{row['n']:>4} {row['c_cert']:.6f}  {row['s*']:>4} {row['s*/n']:.4f}")

print("\n=== landscape f_n(beta) (selected n) ===")
for n, lp in landscape.items():
    m = min(lp.values())
    bstar = min(lp, key=lp.get)
    print(f"n={n}: beta*={bstar:.2f} min_f={m:.6f}")
    print("  " + " ".join(f"{b}:{f:.4f}" for b, f in sorted(lp.items()) if abs(b - round(bstar, 2)) < 0.31))

with open("e6_results.json", "w") as f:
    json.dump({"results": results, "landscape": {str(k): v for k, v in landscape.items()},
               "params": {"R": R, "A_MAX": A_MAX, "N_MAX": N_MAX}}, f, indent=1)
print("\nsaved e6_results.json")
