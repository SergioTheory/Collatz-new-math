import random
import math
from collections import defaultdict, Counter

def make_block(shifts):
    S = 0
    c = 0
    for a in shifts:
        c = 3 * c + (1 << S)
        S += a
    return (S, len(shifts), c)

def reverse_block(x, blk):
    y = (x << blk[0]) - blk[2]
    for _ in range(blk[1]):
        if y % 3 != 0: return None
        y //= 3
    return y if (y & 1) else None

def generate_blocks_C(num_blocks):
    blocks = []
    shifts_list = []
    while len(blocks) < num_blocks:
        d = random.randint(18, 36)
        T = random.choice([12, 18, 24])
        phase = random.randint(0, T-1)
        shifts = []
        for i in range(d):
            if i % T == phase:
                shifts.append(random.choice([3, 4, 5]))
            else:
                shifts.append(random.choice([1, 2]))
        blk = make_block(shifts)
        S, d_, c = blk
        if 1.15 <= S/d_ <= 1.55:
            blocks.append(blk)
            shifts_list.append(shifts)
    return blocks, shifts_list

def generate_blocks_M(num_blocks):
    blocks = []
    shifts_list = []
    while len(blocks) < num_blocks:
        d = random.randint(18, 36)
        shifts = []
        i = 0
        while i < d:
            if random.random() < 0.4 and i <= d - 3:
                shifts.extend([2, 1, 1])
                i += 3
            else:
                shifts.append(random.choice([1, 2, 3]))
                i += 1
        shifts = shifts[:d]
        blk = make_block(shifts)
        S, d_, c = blk
        if 1.15 <= S/d_ <= 1.55:
            blocks.append(blk)
            shifts_list.append(shifts)
    return blocks, shifts_list

def generate_blocks_E(num_blocks):
    blocks = []
    shifts_list = []
    while len(blocks) < num_blocks:
        d = random.randint(18, 36)
        shifts = [random.choices(range(1, 10), weights=[10, 8, 5, 3, 2, 1, 1, 1, 1])[0] for _ in range(d)]
        blk = make_block(shifts)
        S, d_, c = blk
        if 0.9 <= S/d_ <= 2.2:
            blocks.append(blk)
            shifts_list.append(shifts)
    return blocks, shifts_list

def count_pat(seq, pat):
    c = 0
    p_len = len(pat)
    for i in range(len(seq) - p_len + 1):
        if seq[i:i+p_len] == pat: c += 1
    return c

def max_run(seq, val):
    max_r = 0
    curr = 0
    for x in seq:
        if x == val:
            curr += 1
            max_r = max(max_r, curr)
        else:
            curr = 0
    return max_r

def score_block(shifts):
    L = len(shifts)
    motif_count = count_pat(shifts, [2,1,1])
    f_dip = sum(1 for a in shifts if a >= 3) / L
    run1 = max_run(shifts, 1)
    
    score = 1.2 * (motif_count / L)
    score -= 10.0 * abs(f_dip - 0.26)
    score -= 0.6 * max(0, run1 - 12)
    return score

def get_seeds():
    seeds = []
    while len(seeds) < 64:
        min_x = ( (1<<139) - 1 ) // 3
        max_x = (1<<138) - 1
        if min_x > max_x: min_x = max_x # Edge case handling just in case
        x = random.randint(min_x, max_x)
        if x % 4 == 3:
            seeds.append(x)
            
    sprinted_seeds = []
    for x in seeds:
        curr = x
        s_steps = 0
        while curr % 3 == 2 and s_steps < 8:
            y = (curr * 2 - 1) // 3
            if y % 2 == 1:
                curr = y
                s_steps += 1
            else:
                break
        sprinted_seeds.append((curr, s_steps, s_steps))
    return sprinted_seeds

def stage3a():
    dict_size = 500
    blocks_C, shifts_C = generate_blocks_C(dict_size)
    blocks_M, shifts_M = generate_blocks_M(dict_size)
    blocks_E, shifts_E = generate_blocks_E(dict_size)
    
    scores_C = [score_block(s) for s in shifts_C]
    scores_M = [score_block(s) for s in shifts_M]
    scores_E = [score_block(s) for s in shifts_E]
    
    seeds = get_seeds()
    
    b_stars = [71, 75, 79, 83, 87]
    beam = []
    for x, k, S in seeds:
        for b_star in b_stars:
            for fam in ['C', 'M', 'E']:
                beam.append((x, k, S, b_star, fam, 0.0))
                
    W = 100000
    
    for macro_step in range(15):
        if not beam:
            print(f"Beam died at macro-step {macro_step}")
            break
            
        print(f"Macro-step {macro_step}, beam size {len(beam)}")
        next_beam = []
        
        for state in beam:
            x, k, cum_S, b_star, fam, cum_score = state
            
            is_final = (k >= 220)
            
            fam_blocks = []
            fam_scores = []
            if is_final or fam == 'E':
                fam_blocks = blocks_E
                fam_scores = scores_E
            elif fam == 'C':
                fam_blocks = blocks_C
                fam_scores = scores_C
            elif fam == 'M':
                fam_blocks = blocks_M
                fam_scores = scores_M
                
            sample_idx = random.sample(range(dict_size), 50)
            
            r = (140 - b_star) / 258.0
            
            for i in sample_idx:
                blk = fam_blocks[i]
                y = reverse_block(x, blk)
                if y is None: continue
                
                new_k = k + blk[1]
                new_S = cum_S + blk[0]
                
                if new_S / new_k < 1.22 or new_S / new_k > 1.45:
                    continue
                    
                L_k = 140 - r * new_k
                bit_diff = abs(y.bit_length() - L_k)
                delta_k = 5 + 0.01 * new_k
                if bit_diff > delta_k:
                    continue
                    
                new_score = cum_score - bit_diff + fam_scores[i]
                next_beam.append((y, new_k, new_S, b_star, fam, new_score))
                
        dedup = {}
        for state in next_beam:
            y = state[0]
            sig = y & ((1<<64) - 1)
            if sig not in dedup or dedup[sig][-1] < state[-1]:
                dedup[sig] = state
        
        unique_cands = list(dedup.values())
        unique_cands.sort(key=lambda st: st[-1], reverse=True)
        beam = unique_cands[:W]
        
        fam_counts = Counter([st[4] for st in beam])
        print(f"  Families surviving: C={fam_counts['C']}, M={fam_counts['M']}, E={fam_counts['E']}")
        
        done = [st for st in beam if st[1] >= 250]
        if done:
            print(f"  Reached depth 250+ with {len(done)} candidates.")
            
            import json
            import os
            # target bit range check
            success = [st for st in done if 71 <= st[0].bit_length() <= 87]
            print(f"  Valid targets in 71-87 bits: {len(success)}")
            
            if os.path.exists("expand_913.json"):
                with open("expand_913.json", "r") as f:
                    zone2_inputs = json.load(f)
                zone2_set = set(zone2_inputs)
                matches = [st for st in success if str(st[0]) in zone2_set]
                print(f"  Matches with known Zone 2 inputs: {len(matches)}")
                
            x_star = 20152090995747160937051
            x_star_cands = [st for st in done if st[0] == x_star]
            print(f"  x* found exactly: {len(x_star_cands)}")
            
            return

if __name__ == "__main__":
    stage3a()
