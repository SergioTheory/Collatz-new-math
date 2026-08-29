"""
route3_constants.py — numeric pins for Route 3 (Theorem T3 in the paper).

Fixes the ONLY constants the Lean `Divergence.lean` interface needs:
  1. c_star      : per-block survival rate (paper Gate-2 band [0.51, 0.56])
  2. delta_d     : resolution-floor parameter gap  alpha - sigma*t*H2(1/sigma)
  3. I2(sigma)   : Cramer rate of Geom(2), e.g. I2(1.33) ~ 0.25498 bits

All use only the stdlib `math`; no Fourier machinery.
"""
import math

LAMBDA = math.log2(3.0)          # log_2(3) ~ 1.5849625


def h2(p: float) -> float:
    """Binary entropy in bits."""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def i2_cramer(sigma: float) -> float:
    """Cramer rate I2(sigma) of Geom(1/2) in BITS:
    I(σ) = sup_s [ s·σ − Λ(s) ] / ln 2,  Λ(s) = ln( e^s/(2 − e^s) ).
    For σ ∈ (1,2) the optimizer s ∈ (−∞, ln2)."""
    ln2 = math.log(2.0)
    smax = ln2 - 1e-9
    s_min = -3.0
    steps = 60000
    best_nats = 0.0
    for j in range(steps):
        s = s_min + (smax - s_min) * j / (steps - 1)
        es = math.exp(s)
        if es >= 2.0:
            break
        lam = math.log(es / (2.0 - es))          # nats
        val = s * sigma - lam                     # nats
        if val > best_nats:
            best_nats = val
    return best_nats / ln2                        # bits


def main() -> None:
    print("Route 3 constants (Theorem T3)")
    print("=" * 60)
    print(f"lambda = log_2 3 = {LAMBDA:.6f}")

    # --- I2 at the Zone-2 chord sigma = 4/3 ---
    s133 = 4.0 / 3.0
    I133 = i2_cramer(s133)
    print(f"I2(4/3) = {I133:.5f} bits   (paper: 0.25498)")

    # --- c_star = 2^{-B t I2(sigma)} for the paper's block scales ---
    t = 1.0 / LAMBDA          # max allowed t
    sigma = LAMBDA + (1.10 - 1.0) / t   # alpha=1.10 in window (1, 2/lambda)
    print(f"alpha=1.10, t=1/lambda -> sigma = {sigma:.5f}  (must be < 2: {sigma < 2})")
    I2s = i2_cramer(sigma)
    for B in (16, 32, 64, 128):
        cstar = 2.0 ** (-B * t * I2s)
        print(f"  B={B:>4}: c_star = 2^(-{B}*{t:.4f}*{I2s:.4f}) = {cstar:.6f}")

    # --- delta_d = alpha - sigma*t*H2(1/sigma) ---
    print("delta_d = alpha - sigma*t*H2(1/sigma) at allowed t in [(a-1)/(2-lam), 1/lam]:")
    for alpha in (1.05, 1.10, 1.15, 1.20, 1.25):
        tmin = (alpha - 1.0) / (2.0 - LAMBDA) + 1e-9
        tmax = 1.0 / LAMBDA
        for tt in (tmin, tmax):
            sig = LAMBDA + (alpha - 1.0) / tt
            delta = alpha - sig * tt * h2(1.0 / sig)
            tag = "min-t" if tt == tmin else "max-t"
            print(f"  alpha={alpha:.2f} {tag}: sigma={sig:.4f} delta_d={delta:.4f}")

    print()
    print("Paper reference values to match:")
    print("  c_star band          : [0.51, 0.56]  (Gate-2 measurement)")
    print("  delta_d reference    : ~0.5255")
    print("  I2(4/3)              : 0.25498 bits")


if __name__ == "__main__":
    main()
