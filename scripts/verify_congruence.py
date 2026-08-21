import os
import json

def shift_vector(n, steps):
    v = []
    for _ in range(steps):
        if n == 1: break
        x = 3 * n + 1
        a = 0
        while x % 2 == 0:
            x //= 2
            a += 1
        v.append(a)
        n = x
    return v

def compute_c(shift_vec):
    """
    Computes the offset c_vec and sum of shifts S.
    c_{j+1} = 3*c_j + 2^{S_j}
    """
    c = 0
    S = 0
    for a in shift_vec:
        c = 3 * c + (1 << S)
        S += a
    return c, S

def check_lemma(k, m):
    val = k * (3**m) - 1
    t = 0
    while val > 0 and val % 2 == 0:
        val //= 2
        t += 1
    N = val
    
    vec_k = shift_vector(k, 2*m)
    if len(vec_k) < 2*m:
        return False, "Short k", {}
    beta = vec_k[:2*m]
    
    vec_N = shift_vector(N, m)
    if len(vec_N) < m:
        return False, "Short N", {}
    alpha = vec_N[:m]
    
    c_beta, S_beta = compute_c(beta)
    c_alpha, S_alpha = compute_c(alpha)
    
    cond1 = ((c_beta + 3**m) % (1 << t)) == 0
    
    if cond1:
        cond2 = (c_alpha == (c_beta + 3**m) // (1 << t))
    else:
        cond2 = False
        
    cond3 = (S_alpha == S_beta - t)
    
    # Actual match verification
    full_N = shift_vector(N, m + 15)
    full_k = shift_vector(k, 2*m + 15)
    actual_match = False
    if len(full_N) >= m + 15 and len(full_k) >= 2*m + 15:
        actual_match = full_N[m:m+15] == full_k[2*m:2*m+15]
    
    all_conds = cond1 and cond2 and cond3
    
    details = {
        'cond1': cond1,
        'cond2': cond2,
        'cond3': cond3,
        'c_beta': c_beta,
        'c_alpha': c_alpha,
        't': t,
        'S_beta': S_beta,
        'S_alpha': S_alpha
    }
    
    return all_conds, actual_match, details

if __name__ == '__main__':
    # We test the "good" seeds we found and some known "bad" seeds
    good_seeds = [6803, 586115]
    bad_seeds = [121, 27611, 41471, 67625867]
    
    print("=== Checking Congruence Lemma ===")
    
    for k in good_seeds + bad_seeds:
        status = "GOOD" if k in good_seeds else "BAD "
        print(f"\nSeed {k} ({status}):")
        for m in (1, 2, 3):
            theory_match, actual_match, det = check_lemma(k, m)
            
            # Print if theory perfectly predicts actual match
            if theory_match == actual_match:
                result_str = "Predicted correctly"
            else:
                result_str = "PREDICTION FAILED!"
                
            print(f"  m={m}: Theory={theory_match:<5} | Actual={actual_match:<5} | {result_str}")
            if not theory_match and det:
                fail_reasons = []
                if not det['cond1']: fail_reasons.append(f"c_beta+3^m not div by 2^{det['t']}")
                if not det['cond2']: fail_reasons.append(f"c_alpha mismatch")
                if not det['cond3']: fail_reasons.append(f"S_alpha({det['S_alpha']}) != S_beta({det['S_beta']}) - t({det['t']})")
                print(f"         Fails: {', '.join(fail_reasons)}")
