import ast
from collections import Counter

def ctz(y):
    return (y & -y).bit_length() - 1

def get_shift_vector(n, target_peak):
    # To get shifts UP TO the target peak.
    x = int(n); best = 0; best_i = -1; shifts = []
    for i in range(5000):
        if x % 2 == 0:
            x //= 2
            continue
        y = 3 * x + 1
        a = ctz(y)
        shifts.append(a)
        if y > best:
            best, best_i = y, i
        x = y >> a
        if best.bit_length() - x.bit_length() > 40:
            break
        # stop exactly at peak
        if best.bit_length() == target_peak and x.bit_length() < best.bit_length() - 10:
            break
    
    return shifts[:best_i + 1]

def analyze_grammar(name, shifts):
    tail = shifts[-90:] if len(shifts) >= 90 else shifts
    if not tail: return
    phases = [ (len(tail) - 1 - i) % 18 for i, a in enumerate(tail) if a >= 3 ]
    phase_counts = Counter(phases)
    
    pat_3 = [2, 1, 1]
    pat_6 = [2, 1, 2, 1, 1, 1]
    
    def count_pat(seq, pat):
        c = 0
        p_len = len(pat)
        for i in range(len(seq) - p_len + 1):
            if seq[i:i+p_len] == pat: c += 1
        return c
        
    print(f"--- {name} (shifts length {len(shifts)}) ---")
    print("Dips phase distribution (mod 18 from end):", dict(phase_counts))
    print("[2,1,1] count:", count_pat(tail, pat_3))
    print("[2,1,2,1,1,1] count:", count_pat(tail, pat_6))

analyze_grammar("Number 27 (Peak 14)", get_shift_vector(27, 14))
analyze_grammar("Center 26658983 (Peak 35)", get_shift_vector(26658983, 35))
analyze_grammar("Center 67625867 (Peak 37)", get_shift_vector(67625867, 37))
analyze_grammar("Center 37748015 (Peak 41)", get_shift_vector(37748015, 41))
analyze_grammar("Center 2303929595 (Peak 48)", get_shift_vector(2303929595, 48))
