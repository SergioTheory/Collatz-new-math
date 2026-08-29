"""
cf_log2_3.py — Continued fractions of log_2(3) = ln 3 / ln 2.

Deliverables (Route 2, cycle exclusion):
  1. The partial-quotient expansion  [a0; a1, a2, ...]
  2. The convergents p_n / q_n  (nominators / denominators)
  3. The first denominator  q_n > 10^9  (the "no non-trivial cycle below
     10^9 steps" certificate threshold)
  4. The Eliahou-style triple of denominators appearing in the cycle-length
     lattice  K = a·q_i + b·q_j + c·q_k.

Uses only the stdlib `decimal` module for high-precision arithmetic.
"""
from decimal import Decimal, getcontext

PREC = 300
getcontext().prec = PREC

ALPHA = Decimal(3).ln() / Decimal(2).ln()   # log_2(3)


def cf_expand(x: Decimal, n: int) -> list[int]:
    """First n partial quotients of x."""
    terms: list[int] = []
    for _ in range(n):
        a = int(x)                     # floor
        terms.append(a)
        x = x - Decimal(a)
        if x == 0:
            break
        x = Decimal(1) / x
    return terms


def convergents(terms: list[int]) -> list[tuple[int, int]]:
    """Return [(p_n, q_n)] with p_n/q_n the n-th convergent."""
    p_prev, q_prev = 1, 0   # p_{-1}, q_{-1}
    p_cur,  q_cur  = terms[0], 1
    res = [(p_cur, q_cur)]
    for a in terms[1:]:
        p_new = a * p_cur + p_prev
        q_new = a * q_cur + q_prev
        res.append((p_new, q_new))
        p_prev, q_prev = p_cur, q_cur
        p_cur, q_cur = p_new, q_new
    return res


def main() -> None:
    terms = cf_expand(ALPHA, 70)
    print("log_2(3) =", ALPHA)
    print("partial quotients:", terms)
    print()
    convs = convergents(terms)
    print(f"{'n':>3} {'a_n':>4} {'p_n':>22} {'q_n':>22}  |log2(3)-p/q|")
    target = 10**9
    first_big = None
    for n, (p, q) in enumerate(convs):
        a = terms[n] if n < len(terms) else 0
        err = abs(ALPHA - Decimal(p) / Decimal(q))
        print(f"{n:>3} {a:>4} {p:>22} {q:>22} {err:.2e}")
        if q > target and first_big is None:
            first_big = (n, p, q)
    print()
    if first_big:
        n, p, q = first_big
        print(f"FIRST denominator > 10^9 : n={n}, p_n={p}, q_n={q}")
    else:
        print("no denominator > 10^9 in first 60 partials")


if __name__ == "__main__":
    main()