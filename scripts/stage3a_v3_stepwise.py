import random
from collections import Counter

def reverse_step(x):
    cands = []
    if x % 3 == 0: return cands
    start_a = 2 if x % 3 == 1 else 1
    for a in range(start_a, 10, 2):
        y = ((x << a) - 1) // 3
        if y > 0 and y % 2 == 1:
            cands.append((y, a))
    return cands

def score_branch(shifts, fam):
    L = len(shifts)
    if L == 0: return 0
    motif = 0
    for i in range(L - 2):
        if shifts[i] == 2 and shifts[i+1] == 1 and shifts[i+2] == 1:
            motif += 1
            
    f_dip = sum(1 for a in shifts if a >= 3) / L
    max_r = 0
    curr = 0
    for a in shifts:
        if a == 1:
            curr += 1
            if curr > max_r: max_r = curr
        else:
            curr = 0
            
    score = 1.2 * (motif / L)
    if fam != 'E':
        score -= 5.0 * abs(f_dip - 0.26)
        score -= 0.6 * max(0, max_r - 12)
    return score

def get_seeds():
    seeds = []
    while len(seeds) < 64:
        min_x = ( (1<<139) - 1 ) // 3
        max_x = (1<<138) - 1
        x = random.randint(min_x, max_x)
        if x % 4 == 3:
            seeds.append(x)
            
    sprinted = []
    for x in seeds:
        curr = x
        s_steps = 0
        shifts = []
        while curr % 3 == 2 and s_steps < 8:
            y = (curr * 2 - 1) // 3
            if y % 2 == 1:
                curr = y
                s_steps += 1
                shifts.append(1)
            else:
                break
        sprinted.append((curr, s_steps, s_steps, shifts))
    return sprinted

def stage3a_stepwise():
    seeds = get_seeds()
    b_stars = [71, 75, 79, 83, 87]
    
    beam = []
    for x, k, S, shifts in seeds:
        for b_star in b_stars:
            for fam in ['C', 'M', 'E']:
                if fam == 'C':
                    for T in [12, 18, 24]:
                        for phase in [0, 5, 9]:
                            beam.append((x, k, S, b_star, fam, T, phase, shifts))
                else:
                    beam.append((x, k, S, b_star, fam, 0, 0, shifts))
                    
    W_per_fam = 10000
    
    for k_step in range(8, 260):
        if not beam:
            print(f"Beam died at step {k_step}")
            break
            
        next_beam = []
        for state in beam:
            x, k, cum_S, b_star, fam, T, phase, shifts = state
            cands = reverse_step(x)
            r = (140 - b_star) / 258.0
            
            for y, a in cands:
                is_adapter = (k > 220)
                if not is_adapter:
                    if fam == 'C':
                        allowed_phases = [(phase + p) % T for p in [0, 5, 9]]
                        if a >= 3 and (k % T) not in allowed_phases:
                            continue
                        if a > 4: continue
                    elif fam == 'M':
                        if a > 4: continue
                        
                new_k = k + 1
                new_S = cum_S + a
                new_shifts = shifts + [a]
                
                L_k = 140 - r * new_k
                bit_diff = abs(y.bit_length() - L_k)
                delta_k = 5 + 0.05 * new_k  # Tight bound!
                
                if bit_diff > delta_k:
                    continue
                    
                next_beam.append((y, new_k, new_S, b_star, fam, T, phase, new_shifts))
                
        # NICHING BY FAMILY
        fam_buckets = {'C': {}, 'M': {}, 'E': {}}
        for state in next_beam:
            y = state[0]
            fam = state[4]
            sig = y & ((1<<64) - 1)
            score = -abs(y.bit_length() - (140 - ((140-state[3])/258.0)*state[1]))
            if not (state[1] > 220):
                score += score_branch(state[7][-40:], fam)
                
            if sig not in fam_buckets[fam] or fam_buckets[fam][sig][1] < score:
                fam_buckets[fam][sig] = (state, score)
                
        beam = []
        for fam in ['C', 'M', 'E']:
            cands = sorted(fam_buckets[fam].values(), key=lambda x: x[1], reverse=True)
            beam.extend([c[0] for c in cands[:W_per_fam]])
        
        if k_step % 25 == 0 and beam:
            fam_counts = Counter([st[4] for st in beam])
            print(f"Step {k_step}, beam {len(beam)}. C={fam_counts['C']}, M={fam_counts['M']}, E={fam_counts['E']}")
            for f in ['C', 'M', 'E']:
                f_beam = [st for st in beam if st[4] == f]
                if f_beam:
                    avg_bits = sum(st[0].bit_length() for st in f_beam) / len(f_beam)
                    avg_sd = sum(st[2]/st[1] for st in f_beam) / len(f_beam)
                    print(f"  {f}: avg bits {avg_bits:.1f}, S/d {avg_sd:.3f}")
            
    if beam:
        print(f"Reached depth {beam[0][1]} with {len(beam)} candidates.")
        success = [st for st in beam if 71 <= st[0].bit_length() <= 87]
        print(f"Valid targets in 71-87 bits: {len(success)}")
        
        import json
        import os
        if os.path.exists("expand_913.json"):
            with open("expand_913.json", "r") as f:
                zone2_inputs = json.load(f)
            zone2_set = set(zone2_inputs)
            matches = [st for st in success if str(st[0]) in zone2_set]
            print(f"Matches with known Zone 2 inputs: {len(matches)}")
            
        x_star = 20152090995747160937051
        x_star_cands = [st for st in success if st[0] == x_star]
        print(f"x* found exactly: {len(x_star_cands)}")

if __name__ == "__main__":
    stage3a_stepwise()
