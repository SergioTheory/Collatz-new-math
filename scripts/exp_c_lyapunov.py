"""
Experiment C: Explicit Lyapunov Function (LP)
Attempt to find a potential psi: Z/2^m Z -> R such that
L(N) = log2(N) + psi(N mod 2^m) is strictly decreasing for N < X_learn.
"""
import numpy as np
from scipy.optimize import linprog
import time

def collatz_step(x):
    x = 3 * x + 1
    while x % 2 == 0:
        x //= 2
    return x

def solve_lyapunov(m, X_learn):
    mod = 2**m
    # We only care about odd classes
    odds = [x for x in range(mod) if x % 2 != 0]
    idx = {x: i for i, x in enumerate(odds)}
    n_vars = len(odds)
    
    # We want: psi[N] - psi[col(N)] - epsilon >= log2(col(N)/N)
    # LP: minimize -epsilon subject to A_ub * x <= b_ub
    # Let x = [psi_1, ..., psi_{2^{m-1}}, epsilon]
    # -psi[N] + psi[col(N)] + epsilon <= -log2(col(N)/N)
    
    transitions = {}
    for N in range(3, X_learn, 2):
        col_N = collatz_step(N)
        i = idx[N % mod]
        j = idx[col_N % mod]
        
        val = -np.log2(col_N / N)
        if (i, j) not in transitions or val < transitions[(i, j)]:
            transitions[(i, j)] = val  # keep the most restrictive constraint
            
    A = []
    b = []
    for (i, j), val in transitions.items():
        row = np.zeros(n_vars + 1)
        row[i] = -1
        row[j] = 1
        row[-1] = 1  # epsilon
        A.append(row)
        b.append(val)
        
    A = np.array(A)
    b = np.array(b)
    
    c = np.zeros(n_vars + 1)
    c[-1] = -1  # minimize -epsilon
    
    # bounds
    bounds = [(None, None)] * n_vars + [(None, None)]
    
    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    
    if res.success:
        return res.x[-1], res.x[:-1]
    else:
        return -float('inf'), None

def main():
    print("Experiment C: Explicit Lyapunov Function (LP)")
    print("Testing if a local 2-adic potential can compensate Archimedean jumps.")
    
    X_learn = 100000
    
    print(f"X_learn = {X_learn}")
    print(f"{'m':>3} | {'2^(m-1) states':>15} | {'Max epsilon (margin)':>22} | {'Status':>10}")
    print("-" * 60)
    
    for m in range(2, 13):
        t0 = time.time()
        eps, psi = solve_lyapunov(m, X_learn)
        elapsed = time.time() - t0
        
        status = "SUCCESS" if eps > 0 else "NO-GO"
        
        print(f"{m:3d} | {2**(m-1):15d} | {eps:22.6f} | {status:>10}  ({elapsed:.1f}s)")
        
        if eps > 0:
            print(f"\n>>> FOUND VALID LYAPUNOV FUNCTION AT m={m} FOR N < {X_learn}!")
            print(">>> Testing up to 10^7...")
            # We would test it here
            break

if __name__ == "__main__":
    main()
