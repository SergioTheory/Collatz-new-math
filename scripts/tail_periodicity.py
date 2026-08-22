import csv
import ast
from collections import Counter
import numpy as np

def tail_periodicity_analysis(src="zone2_shifts_full.csv", tail_len=90):
    rows = list(csv.DictReader(open(src)))
    vecs = [ast.literal_eval(r["blocks"]) for r in rows]
    
    # 1. Autocorrelation over the tails
    # Auto-correlation of length 90 tails to find period 3 and 6
    tails = [v[-tail_len:] for v in vecs if len(v) >= tail_len]
    
    avg_acf = np.zeros(tail_len)
    for tail in tails:
        t = np.array(tail, dtype=float)
        t -= t.mean()
        var = t.var()
        if var > 0:
            # np.correlate mode='full' gives length 2N-1
            acf = np.correlate(t, t, mode='full')[tail_len-1:] / (var * tail_len)
            avg_acf += acf
            
    avg_acf /= len(tails)
    
    print("--- Autocorrelation of the last 90 steps ---")
    for lag in range(1, 13):
        print(f"Lag {lag:2d}: {avg_acf[lag]:.4f}")
        
    # 2. Pattern matching [2, 1, 1] and [2, 1, 2, 1, 1, 1]
    pat_3 = [2, 1, 1]
    pat_6 = [2, 1, 2, 1, 1, 1]
    
    def count_pattern(seq, pat):
        c = 0
        p_len = len(pat)
        for i in range(len(seq) - p_len + 1):
            if seq[i:i+p_len] == pat:
                c += 1
        return c
        
    total_3 = sum(count_pattern(t, pat_3) for t in tails)
    total_6 = sum(count_pattern(t, pat_6) for t in tails)
    
    # Control: random shuffles of the same tails
    ctrl_3, ctrl_6 = 0, 0
    np.random.seed(42)
    for tail in tails:
        t_shuffled = np.random.permutation(tail).tolist()
        ctrl_3 += count_pattern(t_shuffled, pat_3)
        ctrl_6 += count_pattern(t_shuffled, pat_6)
        
    print("\n--- Pattern frequencies in tail (observed vs shuffled) ---")
    print(f"[2,1,1]       : {total_3} vs {ctrl_3}")
    print(f"[2,1,2,1,1,1] : {total_6} vs {ctrl_6}")
    
    # 3. Phase binding of deep dips (a >= 3) to the T=18 clock
    # Phase = index % 18
    # Let's align all tails to end at the same index
    dip_phases = []
    for tail in tails:
        for i, val in enumerate(tail):
            if val >= 3:
                # Phase from the END of the vector
                # The end is index tail_len - 1
                dist_from_end = (tail_len - 1) - i
                dip_phases.append(dist_from_end % 18)
                
    counts = Counter(dip_phases)
    print("\n--- Phase of deep dips (a>=3) modulo 18 from end ---")
    for phase in range(18):
        print(f"Phase {phase:2d}: {counts.get(phase, 0)}")

if __name__ == "__main__":
    tail_periodicity_analysis()
