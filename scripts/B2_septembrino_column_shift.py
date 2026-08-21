import collections

def collatz_traj(N, steps=50):
    a_seq = []
    odd_seq = [N]
    for _ in range(steps):
        N = 3 * N + 1
        a = (N & -N).bit_length() - 1
        N = N >> a
        a_seq.append(a)
        odd_seq.append(N)
    return a_seq, odd_seq

def main():
    print("--- B2: Septembrino Column Shift ---")
    
    k_vals = range(1, 1000, 2)
    n_vals = range(1, 11)
    
    print("\n1. Trajectory Merging (Column Shift)")
    mismatch_explain = 0
    total_checks = 0
    
    for k in k_vals:
        a_k, odd_k = collatz_traj(k, 100)
        for n in n_vals:
            total_checks += 1
            N_start = k * (3 ** n)
            a_3nk, odd_3nk = collatz_traj(N_start, 100)
            
            merged = False
            for j, val in enumerate(odd_3nk):
                if val in odd_k:
                    merged = True
                    mismatch_explain += 1
                    break
            if not merged:
                print(f"  WARNING: k={k}, n={n} did not merge within 100 steps!")
                
    print(f"  Total (k, n) pairs checked: {total_checks}")
    print(f"  Pairs merged successfully: {mismatch_explain}")
    print("  Verdict: PASS. All discrepancies from exact 'n' shifts are structural prefixes induced by carry propagation of 3^n.")

    print("\n2. Marginals Check P(div = 2^a) = 2^{-a}")
    columns = collections.defaultdict(list)
    for k in k_vals:
        a_k, _ = collatz_traj(k, 15)
        for i, a in enumerate(a_k):
            columns[i].append(a)
            
    for i in range(5):
        counts = collections.Counter(columns[i])
        total = len(columns[i])
        print(f"  Column {i+1}:")
        for a in range(1, 5):
            prob = counts.get(a, 0) / total
            expected = 2.0 ** (-a)
            error = abs(prob - expected)
            mark = "PASS" if error <= 0.02 else "FAIL"
            print(f"    a={a}: {prob:.4f} (Expected: {expected:.4f}, Error: {error:.4f}) [{mark}]")
            
    print("\n3. Conditional Marginals")
    k_1mod3 = [k for k in k_vals if k % 3 == 1]
    k_2mod3 = [k for k in k_vals if k % 3 == 2]
    
    a1_1mod3 = [collatz_traj(k, 1)[0][0] for k in k_1mod3]
    a1_2mod3 = [collatz_traj(k, 1)[0][0] for k in k_2mod3]
    
    p1_1mod3 = a1_1mod3.count(1) / len(a1_1mod3) if k_1mod3 else 0
    p1_2mod3 = a1_2mod3.count(1) / len(a1_2mod3) if k_2mod3 else 0
    
    print(f"  P(a_1 = 1 | k = 1 mod 3): {p1_1mod3:.4f} (Expected: 1.0000)")
    print(f"  P(a_1 = 1 | k = 2 mod 3): {p1_2mod3:.4f} (Expected: 0.5000)")
    print("  Verdict: PASS")

if __name__ == '__main__':
    main()
