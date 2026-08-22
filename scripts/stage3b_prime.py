import random
import os
import json
import time
from collections import Counter
import copy
import math

pow2_mod9 = [ (1<<a)%9 for a in range(10) ]
pow2_mod9[0] = 1 

# Precompute glideslope
L_base = [1398.0]
for k in range(1, 3000):
    if k <= 300: r = 0.34
    elif k <= 900: r = 0.34 - 0.07 * (k - 300) / 600.0
    else: r = 0.27
    L_base.append(L_base[-1] - r)

def get_delta(k):
    if k <= 200: return 60.0
    if k <= 600: return 60.0 - 15.0 * (k - 200) / 400.0
    return 45.0 + 0.005 * (k - 600)

def score_branch(shifts, fam, is_barina, lam1, lam2, lam3, dip_target):
    L = len(shifts)
    if L == 0: return 0
    
    if is_barina:
        return 0 
        
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

def stage3b_prime():
    seeds = get_seeds()
    
    lam1 = 1.2
    lam2 = 5.0
    lam3 = 0.6
    
    # Niches: (r_offset, dip_target)
    # Target S/d: 1.33 (dip=0.26), 1.38 (dip=0.20), 1.42 (dip=0.15)
    niches = [ (0.0, 0.26), (-0.02, 0.20), (-0.04, 0.15) ]
    families = ['C', 'M', 'E']
    
    beam = []
    for x, k, S, shifts in seeds:
        for r_off, dip_t in niches:
            for fam in families:
                if fam == 'C':
                    for T in [12, 18, 24]:
                        for phase in [0, 5, 9]:
                            beam.append((x, k, S, r_off, dip_t, fam, T, phase, shifts, False))
                else:
                    beam.append((x, k, S, r_off, dip_t, fam, 0, 0, shifts, False))
                    
                if fam == 'E' and r_off == 0.0:
                    beam.append((x, k, S, r_off, dip_t, fam, 0, 0, shifts, True))
                    
    total_W = 2000
    W_barina = 100
    W_C = 100
    W_E = 600
    W_M = 1200
    
    # Per niche (3 niches)
    W_C_n = W_C // 3
    W_E_n = W_E // 3
    W_M_n = W_M // 3
    
    death_stats = {'corridor': 0, 'S-d': 0, 'mod9': 0, 'odd': 0, 'phase': 0}
    
    for k_step in range(12, 601):
        if not beam:
            print(f"Beam died at step {k_step}")
            break
            
        is_terminal = (k_step >= 2000)
        
        cands_by_bucket = {} # keys: (fam, r_off), is_barina
        barina_cands = []
        
        # We will collect generated candidates directly into buckets to avoid massive lists
        for state in beam:
            x, k, cum_S, r_off, dip_t, fam, T, phase, shifts, is_barina = state
            
            if is_terminal or k_step >= 2460: 
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
                        death_stats['mod9'] += 1
                        continue
                        
                y = ((x << a) - 1) // 3
                if y <= 0 or y % 2 == 0:
                    death_stats['odd'] += 1
                    continue
                    
                if fam == 'C' and not is_terminal:
                    allowed_phases = [(phase + p) % T for p in [0, 5, 9]]
                    if a >= 3 and (k % T) not in allowed_phases:
                        death_stats['phase'] += 1
                        continue
                        
                new_k = k + 1
                new_S = cum_S + a
                
                # Check S/d limits at checkpoints
                if new_k % 250 == 0:
                    sd = new_S / new_k
                    if sd < 1.28 or sd > 1.45:
                        death_stats['S-d'] += 1
                        continue
                        
                if is_barina:
                    sd = new_S / new_k
                    if new_k > 50 and (sd < 1.20 or sd > 1.30):
                        death_stats['S-d'] += 1
                        continue
                
                L_k = L_base[new_k] - r_off * new_k
                bit_diff = abs(y.bit_length() - L_k)
                delta_k = get_delta(new_k)
                
                if bit_diff > 3 * delta_k:
                    death_stats['corridor'] += 1
                    continue
                    
                new_shifts = shifts + [a]
                new_state = (y, new_k, new_S, r_off, dip_t, fam, T, phase, new_shifts, is_barina)
                
                score = -bit_diff
                score += score_branch(new_shifts[-40:], fam, is_barina, lam1, lam2, lam3, dip_t)
                
                sig = y & ((1<<64) - 1)
                
                if is_barina:
                    barina_cands.append((sig, score, new_state))
                else:
                    key = (fam, r_off)
                    if key not in cands_by_bucket:
                        cands_by_bucket[key] = []
                    cands_by_bucket[key].append((sig, score, new_state))

        def deduplicate_and_enforce_mod3(cands, limit):
            dedup = {}
            for sig, score, st in cands:
                if sig not in dedup or dedup[sig][1] < score:
                    dedup[sig] = (st, score)
                    
            unique = list(dedup.values())
            # Mod-3 Quota: 80% to y%3==2, 20% to y%3==1
            mod2 = [x for x in unique if x[0][0] % 3 == 2]
            mod1 = [x for x in unique if x[0][0] % 3 == 1]
            
            mod2.sort(key=lambda x: x[1], reverse=True)
            mod1.sort(key=lambda x: x[1], reverse=True)
            
            q2 = int(limit * 0.8)
            q1 = limit - q2
            
            res = mod2[:q2] + mod1[:q1]
            # Fill if one is short
            if len(mod2) < q2:
                rem = q2 - len(mod2)
                res += mod1[q1:q1+rem]
            if len(mod1) < q1:
                rem = q1 - len(mod1)
                res += mod2[q2:q2+rem]
                
            res.sort(key=lambda x: x[1], reverse=True)
            return [x[0] for x in res[:limit]]

        next_beam = []
        for key, lst in cands_by_bucket.items():
            fam = key[0]
            if fam == 'C': lim = W_C_n
            elif fam == 'E': lim = W_E_n
            else: lim = W_M_n
            next_beam.extend(deduplicate_and_enforce_mod3(lst, lim))
            
        next_beam.extend(deduplicate_and_enforce_mod3(barina_cands, W_barina))
        beam = next_beam
        
        if k_step % 100 == 0:
            print(f"--- Checkpoint k={k_step} ---")
            print(f"Beam size: {len(beam)}")
            print("Death stats:", death_stats)
            # Reset death stats after printing to see per-interval stats, or keep cumulative. Let's keep cumulative.
            
            if beam:
                bits = sorted([st[0].bit_length() for st in beam])
                p10 = bits[int(len(bits)*0.1)]
                p50 = bits[int(len(bits)*0.5)]
                p90 = bits[int(len(bits)*0.9)]
                print(f"Bits (p10/p50/p90): {p10} / {p50} / {p90}")
                
            fam_counts = Counter([st[5] for st in beam])
            print(f"Families: C={fam_counts['C']}, M={fam_counts['M']}, E={fam_counts['E']}")
            print(f"Barina count: {sum(1 for st in beam if st[9])}")
            
            if k_step in [200, 400, 600, 800, 1000]:
                print(f"CHECKPOINT {k_step} FULL REPORT DUMP")

if __name__ == "__main__":
    stage3b_prime()
