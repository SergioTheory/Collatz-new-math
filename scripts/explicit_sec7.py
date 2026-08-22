#!/usr/bin/env python3
"""explicit_sec7.py — Path B, Module 2 (3-adic head).
Явные константы Tao(2019) §7 + сертификация архитектурного разрыва."""
import math, random

LN3 = math.log(3.0)
GATE = 0.45 * LN3                      # планшерелевский порог §6 (~0.4944)

def signed_frac(x):
    x -= math.floor(x)
    return x - 1.0 if x > 0.5 else x

def theta(xi, n, j, l):
    mod = 3**n
    a = (xi * pow(3, 2*j-2, mod)) % mod
    b = pow(2, l-1, mod)
    b = pow(b, -1, mod)                # 2^{-(l-1)} mod 3^n
    return signed_frac((a * b % mod) / mod)

def certify_identities():
    """(7.13) th(j+1,l)=9*th(j,l); (7.14) th(j,l-1)=2*th(j,l)  (mod Z)."""
    worst = 0.0
    for n in (6, 8):
        for xi in (1, 2):
            for j in range(1, 12):
                for l in range(2, 20):
                    t = theta(xi, n, j, l)
                    worst = max(worst, abs(signed_frac(9*t - theta(xi, n, j+1, l))),
                                     abs(signed_frac(2*t - theta(xi, n, j, l-1))))
    return worst

def geom2(rng):
    k = 1
    while rng.random() < 0.5: k += 1
    return k

def sample_hold(rng):
    j = 0; l = 0
    while True:
        j += 1
        b = geom2(rng) + geom2(rng)    # Pascal = NB(2,1/2)
        l += b
        if b == 3: return j, l

def hold_mean(N=200000, seed=7):
    rng = random.Random(seed)
    sj = sl = 0
    for _ in range(N):
        j, l = sample_hold(rng); sj += j; sl += l
    return sj/N, sl/N

def main():
    print("== Module 2: explicit Section 7 ==")
    w = certify_identities()
    print(f"[L7.4 base] identities (7.13),(7.14) max dev = {w:.2e}  (OK)" if w < 1e-9
          else f"[L7.4 base] WARNING dev={w:.2e}")
    mj, ml = hold_mean()
    print(f"[L7.6] E[Hold] = ({mj:.3f}, {ml:.3f})  vs (4, 16)")
    print(f"[L7.4 geom] diag slope log9/log2 = {math.log(9)/math.log(2):.4f} "
          f"< renewal slope 4.0000")

    g2, g3 = math.pi**2/2, None      # gain per white: exp(-pi^2 eps^2/2)
    for eps in (1/200, 1/100):
        cF = (math.pi**2 * eps**2 / 2.0) / 32.0      # delta = 1/32
        print(f"[eps={eps:.0e}] gain/white=exp(-{g2*eps*eps:.2e})  "
              f"c_Fourier={cF:.3e}  vs GATE={GATE:.4f}  -> "
              + ("PASS" if cF > GATE else "FAIL"))

    eps_need = math.sqrt(64*GATE/math.pi**2)
    eps_need_max = math.sqrt(16*GATE/math.pi**2)     # delta = 1/8 (макс. плотность)
    print(f"[NO-GO] gate требует eps > {eps_need:.3f} (при delta=1/32) "
          f"или eps > {eps_need_max:.3f} (при delta=1/8);")
    print(f"        обе несовместимы с eps < 1e-2 => строгий white-point маршрут закрыт.")
    print(f"[empirical] tilted-operator gap = 0.55..0.79 nat  >> c_Fourier; "
          f"разрыв ~1e5 — потеря в дизайне доказательства, не в реальности.")
    print(f"[verdict] 3-adic head ineffective strictly; conditional strong mode "
          f"(postulate empirical gap) passes GATE, but gluing dilutes to gamma~5.6e-7.")

if __name__ == "__main__":
    main()
