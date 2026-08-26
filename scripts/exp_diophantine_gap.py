"""
Experiment DIOPHANTINE: Quantify the Diophantine gap for Collatz constraints.
For each d, compute the minimal |2^S - 3^d| over all admissible S,
and compare with the Baker-type lower bound.
"""
import numpy as np
from fractions import Fraction
from math import log2, log, log10
import sys

def continued_fraction_log2_3(precision=100):
    """Compute continued fraction of log2(3) to given precision."""
    from decimal import Decimal, getcontext
    getcontext().prec = precision
    from decimal import Decimal
    val = Decimal(3).ln() / Decimal(2).ln()
    cf = []
    for _ in range(precision // 3):
        a = int(val)
        cf.append(a)
        frac = val - a
        if frac == 0:
            break
        val = 1 / frac
    return cf

def convergents(cf, n):
    """Compute convergents of continued fraction."""
    convs = []
    p0, p1 = 0, 1
    q0, q1 = 1, 0
    for a in cf[:n]:
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        convs.append(Fraction(p1, q1))
    return convs

def main():
    print("=" * 70)
    print("DIOPHANTINE GAP: Collatz constraints vs Baker bounds")
    print("=" * 70)
    
    # Needs to handle potentially huge integers so python int is good
    sys.set_int_max_str_digits(1000000)
    cf = continued_fraction_log2_3(200)
    convs = convergents(cf, 50)
    
    print(f"\n{'d':>10} | {'S':>10} | {'|2^S - 3^d| (len)':>18} | {'Baker LB (len)':>18} | {'Gap (len)':>12}")
    print("-" * 75)
    
    for conv in convs[:20]:
        d = conv.denominator
        S = int(conv.numerator)
        if S <= 0 or d <= 0:
            continue
        # Use string lengths for display if the numbers get too big to print cleanly
        # But for small ones just display them, or use scientific notation for logs.
        # Wait, 3^d gets huge fast. d can be up to hundreds or thousands. 
        # So printing exact ints might be too wide. Let's compute exact difference and just print lengths or formatted strings.
        diff = abs(2**S - 3**d)
        
        diff_len = len(str(diff))
        
        # baker log10
        baker_log10 = d * log10(3) - 8.616 * log10(d)
        if baker_log10 < 0:
            baker_log10 = 0
            baker_len = 0
        else:
            baker_len = int(baker_log10) + 1
        
        # gap length is essentially diff_len if diff is overwhelmingly larger than baker_lb
        # or negative if diff < baker_lb
        if diff_len > baker_len + 1:
            gap_len = diff_len
        elif diff_len < baker_len:
            gap_len = -baker_len
        else:
            baker_lb_approx = 10**baker_log10 if baker_log10 < 300 else float('inf')
            if diff > baker_lb_approx:
                gap_len = len(str(int(diff - baker_lb_approx)))
            else:
                gap_len = -baker_len

        print(f"{d:>10} | {S:>10} | {diff_len:>18} | {baker_len:>18} | {gap_len:>12}")

if __name__ == "__main__":
    main()
