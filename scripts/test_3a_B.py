import multiprocessing
import random
import os
import json
import time
from collections import Counter

pow2_mod9 = [ (1<<a)%9 for a in range(10) ]
pow2_mod9[0] = 1 

L_base = [140.0]
for k in range(1, 400):
    if k <= 40: r = 0.34
    elif k <= 100: r = 0.34 - 0.07 * (k - 40) / 60.0
    else: r = 0.27
    L_base.append(L_base[-1] - r)

def get_delta(k):
    if k <= 40: return 20.0
    if k <= 100: return 20.0 - 5.0 * (k - 40) / 60.0
    return 15.0 + 0.01 * (k - 100)

def score_branch(shifts, fam, is_barina, lam1, lam2, lam3, dip_target):
    L = len(shifts)
    if L == 0: return 0
    if is_barina: return 0 
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
        dip_err = abs(f_dip - dip_target)
        if dip_err > 0.06:
            score -= lam2 * (dip_err - 0.06)
        score -= lam3 * max(0, max_r - 12)
    return score

def get_seeds():
    seeds = []
    min_x = ((1 << 138) * 2) // 3
    max_x = (1 << 138) - 1
    while len(seeds) < 64:
        x = random.randint(min_x, max_x)
        if x % 4 == 3: seeds.append(x)
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
        sprinted.append((x, curr, s_steps, s_steps, shifts))
    return sprinted

def process_chunk(chunk_data):
    chunk, k_step, is_terminal, local_deaths, rebased_L0 = chunk_data
    cands_by_bucket = {}
    barina_cands = []
    lam1, lam2, lam3 = 1.2, 5.0, 0.6
    
    for state in chunk:
        orig_x, x, k, cum_S, r_off, dip_t, fam, T, phase, shifts, is_barina = state
        
        if is_terminal or k_step >= 240: 
            alphabet = set(range(1, 10))
        else:
            if fam == 'M': alphabet = set(range(1, 7))
            elif fam == 'C': alphabet = set(range(1, 9))
            else: alphabet = set(range(1, 10))
            
        r = x % 9
        start_a = 2 if x % 3 == 1 else 1
        for a in range(start_a, 10, 2):
            if a not in alphabet: continue
            if not is_terminal:
                if (r * pow2_mod9[a]) % 9 == 1:
                    local_deaths['mod9'] += 1
                    continue
                    
            y = ((x << a) - 1) // 3
            if y <= 0 or y % 2 == 0:
                local_deaths['odd'] += 1
                continue
                
            if fam == 'C' and not is_terminal:
                allowed_phases = [(phase + p) % T for p in [0, 5, 9]]
                if a >= 3 and (k % T) not in allowed_phases:
                    local_deaths['phase'] += 1
                    continue
                    
            new_k = k + 1
            new_S = cum_S + a
            
            c3, c9 = y % 3, y % 9
            steer = 0.0
            if c3 == 2:            steer += 0.8
            if c9 in (2, 8):       steer += 0.4
            if c9 == 8:            steer += 0.3
            if c9 == 4:            steer += 0.4
            if c9 in (5, 7):       steer -= 1.2
            
            sd = new_S / new_k
            sd_penalty = 3.0 * max(0, sd - 1.45) + 3.0 * max(0, 1.28 - sd)
            
            if new_k > 600 and (sd < 1.28 or sd > 1.45):
                local_deaths['S-d'] += 1
                continue
                    
            if is_barina:
                if new_k > 50 and (sd < 1.20 or sd > 1.30):
                    local_deaths['S-d'] += 1
                    continue
            
            if k_step <= 100:
                bit_diff = 0
            else:
                L_k = rebased_L0 - 0.255 * (k_step - 100) - r_off * (k_step - 100)
                bit_diff = abs(y.bit_length() - L_k)
                if bit_diff > 15:
                    local_deaths['corridor'] += 1
                    continue
                
            new_shifts = (shifts + [a])[-50:]
            a_bar_50 = sum(new_shifts) / len(new_shifts)
            a_penalty = 3.0 * max(0, abs(a_bar_50 - 1.33) - 0.05)
            new_state = (orig_x, y, new_k, new_S, r_off, dip_t, fam, T, phase, new_shifts, is_barina)
            score = -bit_diff + steer - sd_penalty - a_penalty + score_branch(new_shifts[-40:], fam, is_barina, lam1, lam2, lam3, dip_t)
            sig = y & ((1<<64) - 1)
            
            if is_barina:
                barina_cands.append((sig, score, new_state))
            else:
                key = (fam, r_off)
                if key not in cands_by_bucket:
                    cands_by_bucket[key] = []
                cands_by_bucket[key].append((sig, score, new_state))
                
    return cands_by_bucket, barina_cands, local_deaths

def deduplicate_and_sort(cands, limit):
    dedup = {}
    for sig, score, st in cands:
        if sig not in dedup or dedup[sig][1] < score:
            dedup[sig] = (st, score)
            
    unique = list(dedup.values())
    unique.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in unique[:limit]]

def stage3b_140_steer():
    seeds = get_seeds()
    niches = [ (0.0, 0.26), (-0.02, 0.20), (-0.04, 0.15) ]
    families = ['C', 'M', 'E']
    
    beam = []
    for orig_x, x, k, S, shifts in seeds:
        for r_off, dip_t in niches:
            for fam in families:
                if fam == 'C':
                    for T in [12, 18, 24]:
                        for phase in [0, 5, 9]:
                            beam.append((orig_x, x, k, S, r_off, dip_t, fam, T, phase, shifts, False))
                else:
                    beam.append((orig_x, x, k, S, r_off, dip_t, fam, 0, 0, shifts, False))
                if fam == 'E' and r_off == 0.0:
                    beam.append((orig_x, x, k, S, r_off, dip_t, fam, 0, 0, shifts, True))
                    
    total_W = 10000
    W_barina = int(total_W * 0.05)
    W_C = int(total_W * 0.05)
    W_E = int(total_W * 0.30)
    W_M = int(total_W * 0.60)
    W_C_n = max(1, W_C // 3)
    W_E_n = max(1, W_E // 3)
    W_M_n = max(1, W_M // 3)
    
    death_stats = {'corridor': 0, 'S-d': 0, 'mod9': 0, 'odd': 0, 'phase': 0}
    num_workers = min(30, multiprocessing.cpu_count())
    pool = multiprocessing.Pool(processes=num_workers)
    
    rebased_L0 = 140
    for k_step in range(1, 401):
        if not beam:
            print(f"Beam died at step {k_step}")
            print(f"Death stats right before death: {death_stats}")
            break
            
        if k_step == 100:
            if beam:
                bits = sorted([st[1].bit_length() for st in beam])
                rebased_L0 = bits[len(bits) // 2]
                print(f"Rebasing corridor to L0 = {rebased_L0}")
                
        is_terminal = (k_step == 400)
        chunks = [beam[i:i + 100] for i in range(0, len(beam), 100)]
        results = pool.map(process_chunk, [(chunk, k_step, is_terminal, {k: 0 for k in death_stats}, rebased_L0) for chunk in chunks])
        
        merged_cands = {}
        merged_barina = []
        for cands_b, bar_cands, local_d in results:
            for key, val in local_d.items():
                death_stats[key] += val
            for key, cands in cands_b.items():
                if key not in merged_cands:
                    merged_cands[key] = []
                merged_cands[key].extend(cands)
            merged_barina.extend(bar_cands)
            
        next_beam = []
        for key, lst in merged_cands.items():
            fam = key[0]
            lim = W_C_n if fam == 'C' else W_E_n if fam == 'E' else W_M_n
            next_beam.extend(deduplicate_and_sort(lst, lim))
            
        next_beam.extend(deduplicate_and_sort(merged_barina, W_barina))
        beam = next_beam
        
        if k_step % 20 == 0:
            print(f"--- Checkpoint k={k_step} ---")
            print(f"Beam size: {len(beam)}")
            print("Death stats:", death_stats)
            if beam:
                bits = sorted([st[1].bit_length() for st in beam])
                print(f"Bits (p10/p50/p90): {bits[int(len(bits)*0.1)]} / {bits[int(len(bits)*0.5)]} / {bits[int(len(bits)*0.9)]}")
                
                mod3_counts = Counter([st[1] % 3 for st in beam])
                total = len(beam)
                print(f"Mod-3 distribution: 0: {mod3_counts[0]/total:.1%}, 1: {mod3_counts[1]/total:.1%}, 2: {mod3_counts[2]/total:.1%}")
                
                all_a = []
                for st in beam:
                    all_a.extend(st[9])
                a_counts = Counter(all_a)
                total_a = len(all_a)
                hist_str = ", ".join(f"{k}: {v/total_a:.1%}" for k, v in sorted(a_counts.items()))
                print(f"Hist 'a' (last 50): {hist_str}")
        if k_step == 400:
            print(f"--- Final verification at k={k_step} ---")
            print(f"Beam size: {len(beam)}")
            successes = [st for st in beam if 71 <= st[1].bit_length() <= 87]
            print(f"Found {len(successes)} branches in 71-87 bit window!")
            break
            
if __name__ == "__main__":
    stage3b_140_steer()
