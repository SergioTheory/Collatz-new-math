import random
import ast
import csv
from collections import Counter

def load_true_path():
    with open("zone2_shifts_full.csv", "r") as f:
        r = next(csv.DictReader(f))
        v = ast.literal_eval(r["blocks"])
    
    x_star = 20152090995747160937051
    path = [x_star]
    shifts = []
    curr = x_star
    for a in v:
        curr = (curr * 3 + 1) >> a
        path.append(curr)
        shifts.append(a)
        
    rev_path = path[::-1] # rev_path[0] is peak odd (140 bits)
    rev_shifts = shifts[::-1] # rev_shifts[0] is last forward shift (3)
    return rev_path, rev_shifts

pow2_mod9 = [ (1<<a)%9 for a in range(10) ]
pow2_mod9[0] = 1 # though we don't use a=0

def get_valid_a(x, alphabet, is_terminal):
    r = x % 9
    cands = []
    if x % 3 == 0: return cands # just in case, but shouldn't happen with our filter
    start_a = 2 if x % 3 == 1 else 1
    for a in range(start_a, 10, 2):
        if a not in alphabet: continue
        
        # mod 9 check
        if not is_terminal:
            if (r * pow2_mod9[a]) % 9 == 1:
                continue
                
        y = ((x << a) - 1) // 3
        if y > 0 and y % 2 == 1:
            cands.append((y, a))
    return cands

def score_branch(shifts, fam, lam1, lam2, lam3):
    L = len(shifts)
    if L == 0: return 0
    motif = sum(1 for i in range(L - 2) if shifts[i:i+3] == [2, 1, 1])
    f_dip = sum(1 for a in shifts if a >= 3) / L
    
    max_r = 0
    curr = 0
    for a in shifts:
        if a == 1:
            curr += 1
            if curr > max_r: max_r = curr
        else:
            curr = 0
            
    score = lam1 * (motif / L)
    if fam != 'E':
        score -= lam2 * abs(f_dip - 0.26)
        score -= lam3 * max(0, max_r - 12)
    return score

def calibrate():
    rev_path, rev_shifts = load_true_path()
    # rev_path has length 253 (indices 0 to 252)
    # rev_shifts has length 252 (indices 0 to 251)
    # the true branch at step k is rev_path[k]
    
    # We will track rank for family M (or C)
    lam1 = 1.2
    lam2 = 5.0
    lam3 = 0.6
    base_delta = 5.0
    
    W = 10000
    
    # Init
    start_x = rev_path[0]
    beam = [(start_x, 0, 0, [])] # (x, k, cum_S, shifts)
    
    true_ranks = []
    
    for k_step in range(1, 253):
        true_x = rev_path[k_step]
        true_a = rev_shifts[k_step - 1]
        
        is_adapter = (k_step >= 240)
        is_terminal = (k_step == 252)
        alphabet = set(range(1, 10)) if is_adapter else set(range(1, 7)) # Fam M
        
        next_beam = []
        for x, k, cum_S, shifts in beam:
            cands = get_valid_a(x, alphabet, is_terminal)
            
            for y, a in cands:
                new_k = k + 1
                new_S = cum_S + a
                new_shifts = shifts + [a]
                
                if new_k > 20 and not is_adapter:
                    if new_S / new_k < 1.15 or new_S / new_k > 1.55:
                        continue
                        
                L_k = 140 - (140 - 75) / 258.0 * new_k
                bit_diff = abs(y.bit_length() - L_k)
                delta_k = base_delta + 0.1 * new_k
                
                if bit_diff > 3 * delta_k:
                    continue
                    
                next_beam.append((y, new_k, new_S, new_shifts))
                
        # deduplicate and score
        dedup = {}
        true_found = False
        
        for state in next_beam:
            y, new_k, new_S, new_shifts = state
            sig = y & ((1<<64) - 1)
            
            # bit diff penalty
            L_k = 140 - (140 - 75) / 258.0 * new_k
            score = -abs(y.bit_length() - L_k)
            if not is_adapter:
                score += score_branch(new_shifts[-40:], 'M', lam1, lam2, lam3)
                
            if sig not in dedup or dedup[sig][1] < score:
                dedup[sig] = (state, score)
                
            if y == true_x:
                true_found = True
                
        unique_cands = sorted(dedup.values(), key=lambda x: x[1], reverse=True)
        beam = [c[0] for c in unique_cands[:W]]
        
        # calculate rank of true branch
        rank = -1
        for i, (state, score) in enumerate(unique_cands):
            if state[0] == true_x:
                rank = i
                break
                
        true_ranks.append(rank)
        
        if rank == -1:
            print(f"Step {k_step}: True branch LOST!")
            if true_found:
                print(f"True branch was generated but didn't make the top {W}")
            break
        
        if k_step % 20 == 0:
            print(f"Step {k_step}, Beam {len(beam)}, True Rank: {rank}")
            
    print("Calibration finished.")
    print("Max true rank:", max(true_ranks) if true_ranks else -1)
    
if __name__ == "__main__":
    calibrate()
