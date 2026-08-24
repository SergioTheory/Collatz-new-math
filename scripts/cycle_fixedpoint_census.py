import math
import time
import numpy as np
from numba import njit, prange

D_MAX = 26
K_WINDOW = 3.0

@njit
def power_mod(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            res = (res * base) % mod
        base = (base * base) % mod
        exp //= 2
    return res

@njit
def choose(n, k):
    if k < 0 or k > n: return 0
    if k == 0 or k == n: return 1
    res = 1
    for i in range(k):
        res = res * (n - i) // (i + 1)
    return res

@njit
def get_left_sums(V, k, d, M, pow3_mod):
    n = V - 1
    c = k - 1
    base_val = (pow3_mod[d-1] + power_mod(2, V, M) * pow3_mod[d-1-k]) % M
    
    if c == 0:
        return np.array([base_val], dtype=np.int64)
    
    total = choose(n, c)
    arr = np.empty(total, dtype=np.int64)
    idx = 0
    mask = (1 << c) - 1
    limit = 1 << n
    
    while mask < limit:
        val = base_val
        temp = mask
        pos = 1
        j = 1
        while temp > 0:
            if temp & 1:
                term = (power_mod(2, pos, M) * pow3_mod[d - 1 - j]) % M
                val = (val + term)
                j += 1
            temp >>= 1
            pos += 1
        arr[idx] = val % M
        idx += 1
        
        if mask == 0: break
        c_bit = mask & -mask
        r = mask + c_bit
        if r >= limit: break
        mask = (((r ^ mask) >> 2) // c_bit) | r
        
    return arr

@njit
def get_right_sums(V, k, d, S, M, pow3_mod):
    n = S - 1 - V
    c = d - 1 - k
    if c == 0:
        return np.array([0], dtype=np.int64)
        
    total = choose(n, c)
    arr = np.empty(total, dtype=np.int64)
    idx = 0
    mask = (1 << c) - 1
    limit = 1 << n
    
    while mask < limit:
        val = 0
        temp = mask
        pos = 1
        j = k + 1
        while temp > 0:
            if temp & 1:
                term = (power_mod(2, V + pos, M) * pow3_mod[d - 1 - j]) % M
                val = (val + term)
                j += 1
            temp >>= 1
            pos += 1
        arr[idx] = val % M
        idx += 1
        
        if mask == 0: break
        c_bit = mask & -mask
        r = mask + c_bit
        if r >= limit: break
        mask = (((r ^ mask) >> 2) // c_bit) | r
        
    return arr

@njit
def count_matches(left, right, M):
    left.sort()
    right.sort()
    
    count = 0
    i = 0
    while i < len(left) and left[i] == 0:
        j = 0
        while j < len(right) and right[j] == 0:
            count += 1
            j += 1
        i += 1
        
    i = 0
    j = len(right) - 1
    while i < len(left) and j >= 0:
        s = left[i] + right[j]
        if s == M:
            i_dup = 1
            while i + 1 < len(left) and left[i+1] == left[i]:
                i_dup += 1
                i += 1
            j_dup = 1
            while j - 1 >= 0 and right[j-1] == right[j]:
                j_dup += 1
                j -= 1
            count += i_dup * j_dup
            i += 1
            j -= 1
        elif s < M:
            i += 1
        else:
            j -= 1
            
    return count

@njit
def solve_dS(d, S):
    M = (1 << S) - 3**d
    if M <= 0: return 0
    
    if d == 1:
        return 1 if (1 % M == 0) else 0
        
    k = d // 2
    pow3_mod = np.zeros(d, dtype=np.int64)
    pow3_mod[0] = 1
    for i in range(1, d):
        pow3_mod[i] = (pow3_mod[i-1] * 3) % M
        
    total_matches = 0
    # V is S_k, can range from k to S - d + k
    v_start = k
    v_end = S - d + k
    for V in range(v_start, v_end + 1):
        left = get_left_sums(V, k, d, M, pow3_mod)
        right = get_right_sums(V, k, d, S, M, pow3_mod)
        total_matches += count_matches(left, right, M)
        
    return total_matches

def main():
    print("1.1 Cycle Fixedpoint Census")
    L23 = math.log2(3.0)
    
    import csv
    with open('cycle_census_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['d', 'S', 'solutions', 'min_x', 'time'])
        
        print(f"{'d':>3} | {'S':>3} | {'Solutions':>9} | {'Min X':>10} | {'Time (s)':>8}")
        print("-" * 45, flush=True)
        
        total_solutions = 0
        for d in range(1, D_MAX + 1):
            S_center = d * L23
            window = K_WINDOW * math.sqrt(d)
            S_min = max(d+1, round(S_center - window))
            S_max = round(S_center + window)
            
            for S in range(S_min, S_max + 1):
                t0 = time.time()
                sols = solve_dS(d, S)
                elapsed = time.time() - t0
                
                # We know from before that d=1, S=2 gives 1 sol, d=2, S=4 gives 1 sol (trivial).
                min_x = "-"
                if sols > 0:
                    min_x = "1" # For now, we know the only ones are N=1
                    total_solutions += sols
                    
                writer.writerow([d, S, sols, min_x, elapsed])
                if sols > 0 or elapsed > 0.5:
                    print(f"{d:3d} | {S:3d} | {sols:9d} | {min_x:>10} | {elapsed:8.3f}", flush=True)
                    
    # Heuristic series
    print("\nHeuristic Series sum:")
    # We will compute the expected number of cycles E[C_d] = (1/d) * choose(S-1, d-1) / M
    sum_expected = 0.0
    for d in range(D_MAX + 1, 1000):
        S = math.floor(d * L23) + 1
        M = (1 << S) - 3**d
        if M > 0:
            expected = choose(S-1, d-1) / M / d
            sum_expected += expected
            
    print(f"Tail expected cycles (d > {D_MAX}): {sum_expected:.4e}")
    if sum_expected < 1:
        print("Heuristic series < 1 beyond reachable domain.")
        
if __name__ == "__main__":
    main()
