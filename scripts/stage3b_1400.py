import random
import os
import json
import time
from collections import Counter
import copy

pow2_mod9 = [ (1<<a)%9 for a in range(10) ]
pow2_mod9[0] = 1 

def get_valid_a(x, alphabet, is_terminal):
    r = x % 9
    cands = []
    if x % 3 == 0: return cands
    start_a = 2 if x % 3 == 1 else 1
    for a in range(start_a, 10, 2):
        if a not in alphabet: continue
        if not is_terminal:
            if (r * pow2_mod9[a]) % 9 == 1:
                continue
                
        y = ((x << a) - 1) // 3
        if y > 0 and y % 2 == 1:
            cands.append((y, a))
    return cands

def score_branch(shifts, fam, is_barina, lam1, lam2, lam3):
    L = len(shifts)
    if L == 0: return 0
    
    if is_barina:
        return 0 # no motif bonus, no dip penalty
        
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
        dip_err = abs(f_dip - 0.26)
        if dip_err > 0.06:
            score -= lam2 * (dip_err - 0.06)
        score -= lam3 * max(0, max_r - 12)
    return score

def get_seeds():
    seeds = []
    # 1398 bits upper third -> range [ (2/3)*2^1398, 2^1398 - 1 ]
    min_x = ((1 << 1398) * 2) // 3
    max_x = (1 << 1398) - 1
    while len(seeds) < 64:
        x = random.randint(min_x, max_x)
        if x % 4 == 3:
            seeds.append(x)
            
    sprinted = []
    for x in seeds:
        curr = x
        s_steps = 0
        shifts = []
        while curr % 3 == 2 and s_steps < 12:
            y = (curr * 2 - 1) // 3
            if y % 2 == 1:
                curr = y
                s_steps += 1
                shifts.append(1)
            else:
                break
        sprinted.append((curr, s_steps, s_steps, shifts))
    return sprinted

def stage3b():
    seeds = get_seeds()
    
    lam1 = 1.2
    lam2 = 5.0
    lam3 = 0.6
    
    r_niches = [0.25, 0.265, 0.28]
    families = ['C', 'M', 'E']
    
    beam = []
    for x, k, S, shifts in seeds:
        for r_val in r_niches:
            for fam in families:
                # state: (x, k, cum_S, r_val, fam, T, phase, shifts)
                if fam == 'C':
                    for T in [12, 18, 24]:
                        for phase in [0, 5, 9]:
                            beam.append((x, k, S, r_val, fam, T, phase, shifts, False)) # False for is_barina
                else:
                    beam.append((x, k, S, r_val, fam, 0, 0, shifts, False))
                    
                # Barina canal (only for E family to simplify, or maybe M)
                if fam == 'E':
                    beam.append((x, k, S, r_val, fam, 0, 0, shifts, True)) # is_barina = True
                    
    total_W = 5000
    W_barina = int(total_W * 0.05)
    W_normal = total_W - W_barina
    W_per_niche = W_normal // 9
    
    base_delta_add = 0
    low_survivor_streak = 0
    
    candidates = []
    
    for k_step in range(12, 501):
        if not beam:
            print(f"Beam died at step {k_step}")
            break
            
        next_beam = []
        is_terminal = (k_step >= 2000)
        
        for state in beam:
            x, k, cum_S, r_val, fam, T, phase, shifts, is_barina = state
            
            # Alphabet
            if is_terminal or k_step >= 2460: 
                alphabet = set(range(1, 10))
            else:
                if fam == 'M': alphabet = set(range(1, 7))
                elif fam == 'C': alphabet = set(range(1, 9))
                else: alphabet = set(range(1, 10))
                
            cands = get_valid_a(x, alphabet, is_terminal=False) # we don't know exact terminal step, just allow mod 9 filter always until final 
            
            for y, a in cands:
                if fam == 'C' and not is_terminal:
                    allowed_phases = [(phase + p) % T for p in [0, 5, 9]]
                    if a >= 3 and (k % T) not in allowed_phases:
                        continue
                        
                new_k = k + 1
                new_S = cum_S + a
                new_shifts = shifts + [a]
                
                L_k = 1398 - r_val * new_k
                bit_diff = abs(y.bit_length() - L_k)
                delta_k = (60 if new_k <= 200 else 40 + 0.01 * new_k) + base_delta_add
                
                if bit_diff > 3 * delta_k:
                    continue
                    
                if new_k % 250 == 0:
                    sd = new_S / new_k
                    if sd < 1.28 or sd > 1.40:
                        continue
                        
                if is_barina:
                    sd = new_S / new_k
                    if new_k > 50 and (sd < 1.20 or sd > 1.30):
                        continue
                        
                next_beam.append((y, new_k, new_S, r_val, fam, T, phase, new_shifts, is_barina))
                
                if new_k >= 2000:
                    b = y.bit_length()
                    if 690 <= b <= 730:
                        candidates.append((y, new_k, new_S, r_val, fam, new_shifts, is_barina))
                        
        if k_step >= 2000 and len(candidates) > 0:
            pass # Keep searching but we have candidates!
            
        dedup_normal = {}
        dedup_barina = {}
        
        for state in next_beam:
            y, new_k, new_S, r_val, fam, T, phase, new_shifts, is_barina = state
            sig = y & ((1<<64) - 1)
            
            L_k = 1398 - r_val * new_k
            score = -abs(y.bit_length() - L_k)
            score += score_branch(new_shifts[-40:], fam, is_barina, lam1, lam2, lam3)
            
            key = (fam, r_val)
            
            if is_barina:
                if sig not in dedup_barina or dedup_barina[sig][1] < score:
                    dedup_barina[sig] = (state, score)
            else:
                if key not in dedup_normal:
                    dedup_normal[key] = {}
                if sig not in dedup_normal[key] or dedup_normal[key][sig][1] < score:
                    dedup_normal[key][sig] = (state, score)
                    
        beam = []
        for key, bucket in dedup_normal.items():
            sorted_cands = sorted(bucket.values(), key=lambda x: x[1], reverse=True)
            beam.extend([c[0] for c in sorted_cands[:W_per_niche]])
            
        sorted_barina = sorted(dedup_barina.values(), key=lambda x: x[1], reverse=True)
        beam.extend([c[0] for c in sorted_barina[:W_barina]])
        
        if len(beam) < 0.1 * total_W:
            low_survivor_streak += 1
            if low_survivor_streak >= 2:
                base_delta_add += 10
                lam2 *= 0.8
                lam3 *= 0.8
                low_survivor_streak = 0
                print(f"Auto-expanded at step {k_step}: delta_add={base_delta_add}, lam2={lam2:.2f}")
        else:
            low_survivor_streak = 0
            
        if k_step % 100 == 0:
            print(f"--- Checkpoint k={k_step} ---")
            print(f"Beam size: {len(beam)}")
            fam_counts = Counter([st[4] for st in beam])
            print(f"Families: C={fam_counts['C']}, M={fam_counts['M']}, E={fam_counts['E']}")
            # Estimate beta_eff
            # We had ~5000 parents, we have ~5000 survivors, but actual multiplier before deduplication:
            # Let's just calculate beta_eff = log2( len(next_beam) / total_parents )
            # Wait, beta_eff is the effective branching factor. 
            # We can approximate it by the average number of valid children generated per parent:
            print(f"Avg children per parent: {len(next_beam) / (len(beam)+1):.2f}")
            if candidates:
                print(f"Found {len(candidates)} candidates in target zone!")
                
    if candidates:
        print(f"SUCCESS! Found {len(candidates)} total candidates.")
        with open("candidates_1400.json", "w") as f:
            out = []
            for c in candidates:
                y, k, S, r_val, fam, shifts, is_b = c
                out.append({"x": str(y), "k": k, "S": S, "fam": fam, "r": r_val, "is_barina": is_b, "shifts": shifts[-50:]})
            json.dump(out, f)
    else:
        print("NULL result. No candidates found in target zone.")
        
if __name__ == "__main__":
    stage3b()
