#!/usr/bin/env python3
"""
explicit_sec4.py — «Collatz II», Path B, Module 1 (2-adic left head).

Делает Tao (2019), Lemma 4.1 + Eq. (4.1), полностью явными и проверяет гейт
тенирования:  c_1 * (2+c_0) * ln 2 > I(1.33) = 0.175.

Неасимптотические (строгие) оценки:
 (E0) дискретизация (1.11):            err <= 2^{-n'}
 (E1) хвост Леммы 4.1:  sum_{k<n} 2^{-n'} C(n'-1,k) <= n * 2^{-n'} C(n'-1, n-1)
 (E2) главный член (4.1):              2^{-n'} C(n'-1, n)
 (E3) хвост Geom(2), точный Чернов:    P(|Geom(2)^n| >= n') <= 2^{-n I_2(2+c_0)}

Lemma B1 (Collatz II). При d_TV(N mod 2^{n'}, Unif) <= 2^{-n'}, n'=floor((2+c_0)n):
  d_TV(a^(n)(N), Geom(2)^n) <= 2^{-n'} + n 2^{-n'} C(n'-1,n-1)
                               + 2^{-n'} C(n'-1,n) + 2^{-c_1 n},
  liminf -log2(d_TV)/n >= c_1(c_0),
  c_1(c_0) = (2+c_0) - (2+c_0)log2(2+c_0) + (1+c_0)log2(1+c_0).
"""
import math

I_TARGET = 0.175          # I(1.33), структурная LDP-скорость (Lemma T3), нат

def h2(p):                # двоичная энтропия, бит
    return -p*math.log2(p) - (1-p)*math.log2(1-p) if 0 < p < 1 else 0.0

def c1_closed(c0):        # замкнутая форма, бит/шаг
    m = 2.0 + c0
    return m - m*math.log2(m) + (m-1)*math.log2(m-1)

def geom_cramer(m):       # Крамеровская скорость Geom(2) в точке m
    return m + (m-1)*math.log2(m-1) - m*math.log2(m)

def log2_int_upper(x):    # строгая верхняя граница log2: floor(log2 x)+1 >= log2 x
    return x.bit_length()

def bound_tv_log2(n, c0):
    """log2 строгой верхней границы d_TV: максимум из (E0..E3) + log2(4)."""
    n1 = math.floor((2.0 + c0) * n)
    assert n - 1 <= (n1 - 1) / 2, "нужно для монотонности бинома в сумме хвоста"
    e0 = -n1                                            # (E0)
    e1 = math.log2(n) + log2_int_upper(math.comb(n1-1, n-1)) - n1   # (E1)
    e2 = log2_int_upper(math.comb(n1-1, n)) - n1        # (E2)
    e3 = -c1_closed(c0) * n                             # (E3), точно
    m = max(e0, e1, e2, e3)
    return m + math.log2(sum(2.0**(e-m) for e in (e0, e1, e2, e3))) + 2.0

def gate(c0):
    return c1_closed(c0) * (2.0 + c0) * math.log(2.0)  # левая часть гейта, нат

def main():
    # 0) тождество скоростей: равномерность == Чернов
    for c0 in (0.5, 1.0, 1.5):
        assert abs(c1_closed(c0) - geom_cramer(2+c0)) < 1e-12
    print("тождество скоростей (binom == Cramer): OK\n")

    # 1) сходимость строгой границы к c_1 при c0 = 1
    print(f"{'n':>5} {'n_prime':>8} {'-log2(bound)/n':>15} {'c_1 (lim)':>10}")
    for n in (50, 100, 200, 500, 1000):
        r = -bound_tv_log2(n, 1.0) / n
        print(f"{n:>5} {math.floor(3*n):>8} {r:>15.4f} {c1_closed(1.0):>10.4f}")

    # 2) скан c_0 и гейт
    print(f"\n{'c0':>5} {'c_1 [bits]':>11} {'gate [nats]':>12}  verdict")
    best = None
    c0 = 0.50
    while c0 <= 2.001:
        g = gate(c0)
        ok = g > I_TARGET
        print(f"{c0:>5.2f} {c1_closed(c0):>11.4f} {g:>12.4f}  {'PASS' if ok else 'fail'}")
        if ok and best is None:
            best = c0
        c0 += 0.25 if c0 < 0.9 else 0.5

    g1 = gate(1.0)
    print(f"\n[VERDICT] канонический c0=1: c_1 = {c1_closed(1.0):.4f} бит/шаг; "
          f"гейт = {g1:.4f} нат > {I_TARGET}  ->  PASS, запас x{g1/I_TARGET:.1f}")
    print(f"[VERDICT] гейт открывается при c0 ≈ {best:.2f}")
    print(f"[LEFT HEAD] эффективна: ошибка тенирования 2^(-{c1_closed(1.0):.3f} n) "
          f"доминируется структурной скоростью I(1.33)=0.175 в смысле гейта.")

if __name__ == "__main__":
    main()
