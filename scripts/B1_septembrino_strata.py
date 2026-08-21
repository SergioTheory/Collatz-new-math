import sys

def v2(x):
    if x == 0: return float('inf')
    return (x & -x).bit_length() - 1

def theoretical_v2(k, n):
    if n % 2 == 1:
        if k % 4 == 1:
            return 1
        else:
            return ">=2"
    else:
        t = v2(n)
        v2_km1 = v2(k - 1)
        if v2_km1 != t + 2:
            return min(v2_km1, t + 2)
        else:
            return "critical"

def main():
    print("--- B1: Septembrino Strata ---")
    k_vals = [17, 33, 65, 257]
    n_max = 500
    
    for k in k_vals:
        print(f"\nTesting k = {k}")
        critical_count = 0
        exact_matches = 0
        mismatches = 0
        
        for n in range(1, n_max + 1):
            val = k * (3 ** n) - 1
            exact = v2(val)
            expected = theoretical_v2(k, n)
            
            if expected == "critical":
                critical_count += 1
                t = v2(n)
                if exact <= t + 2:
                    print(f"  Mismatch at n={n}: exact={exact}, expected > {t+2}")
                    mismatches += 1
            else:
                if expected == ">=2":
                    if exact < 2:
                        print(f"  Mismatch at n={n}: exact={exact}, expected >= 2")
                        mismatches += 1
                    else:
                        exact_matches += 1
                else:
                    if exact != expected:
                        print(f"  Mismatch at n={n}: exact={exact}, expected={expected}")
                        mismatches += 1
                    else:
                        exact_matches += 1
                        
        print(f"  Matches: {exact_matches}")
        print(f"  Critical strata (v2(k-1) == t+2) encountered: {critical_count}")
        print(f"  Mismatches: {mismatches}")
        if mismatches == 0:
            print("  Verdict: PASS (All deviations perfectly explained by critical strata)")
        else:
            print("  Verdict: FAIL")

if __name__ == '__main__':
    main()
