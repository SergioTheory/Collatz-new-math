import random
import ast
from collections import Counter
import math
import copy

def load_grammar(csv_path):
    with open(csv_path, 'r') as f:
        line = f.readlines()[1]
    zone2_shifts = ast.literal_eval(line.strip().split(',"')[1].split('"')[0])
    core_shifts = zone2_shifts[-251:]
    
    # We are generating a reverse trajectory. So the sequence of shifts applied
    # backwards is the forward sequence reversed!
    bwd_shifts = core_shifts[::-1]
    
    BLOCK_LEN = 6
    blocks = []
    for i in range(len(bwd_shifts) - BLOCK_LEN + 1):
        blocks.append(tuple(bwd_shifts[i:i+BLOCK_LEN]))
    
    block_counts = Counter(blocks)
    
    # Smoothed frequencies for Family M (T=1.5)
    T = 1.5
    block_weights = {b: count ** (1/T) for b, count in block_counts.items()}
    blocks_list = list(block_weights.keys())
    blocks_prob = [block_weights[b] for b in blocks_list]
    total_prob = sum(blocks_prob)
    blocks_prob = [p/total_prob for p in blocks_prob]
    
    return blocks_list, blocks_prob, bwd_shifts

def apply_block(x, blk, max_len):
    y = x
    for a in blk[:max_len]:
        if y % 3 == 0: return None
        req_parity = 0 if y % 3 == 1 else 1
        if a % 2 != req_parity:
            return None
        y = ((y << a) - 1) // 3
        if y <= 0 or y % 2 == 0:
            return None
    return y

def get_delta(k, total_k):
    # Expanding tunnel with end taper
    cap = 18.0
    c = 0.25
    delta_0 = 8.0
    
    if k > total_k * 0.9:
        base_delta = min(cap, delta_0 + c * math.sqrt(total_k * 0.9))
        progress = (k - total_k * 0.9) / (total_k * 0.1)
        return base_delta - progress * (base_delta - delta_0)
    else:
        return min(cap, delta_0 + c * math.sqrt(k))

def stage4a():
    blocks_list, blocks_prob, bwd_shifts = load_grammar('zone2_shifts.csv')
    
    target_peak = 329409787129088108212379710537829645932061
    TOTAL_K = 251
    BLOCK_LEN = 6
    
    # Shadow forward is (2,1,1). Reversed is (1,1,2).
    v_pattern = [1, 1, 2] * 20
    v_blocks = [
        tuple(v_pattern[0:6]),
        tuple(v_pattern[1:7]),
        tuple(v_pattern[2:8])
    ]
    
    families = ['V', 'M', 'E']
    
    for fam in families:
        print(f"\n--- Testing Family {fam} ---")
        beam = [(target_peak, 0, 0, [])] # x, k, S, shifts
        W = 100000 # Beam width
        
        for k_step in range(0, TOTAL_K, BLOCK_LEN):
            if not beam:
                print(f"Beam died at step {k_step}")
                break
                
            next_beam = []
            for state in beam:
                x, k, cum_S, shifts = state
                if k >= TOTAL_K:
                    next_beam.append(state)
                    continue
                
                max_len = min(BLOCK_LEN, TOTAL_K - k)
                
                if fam == 'V':
                    valid_proposals = [b for b in v_blocks if apply_block(x, b, max_len) is not None]
                else:
                    valid_proposals = [b for b in blocks_list if apply_block(x, b, max_len) is not None]
                
                if not valid_proposals:
                    continue
                
                if fam == 'V':
                    proposals = valid_proposals
                elif fam == 'E':
                    proposals = valid_proposals 
                else: # 'M'
                    if len(valid_proposals) <= 8:
                        proposals = valid_proposals
                    else:
                        subset_weights = [blocks_prob[blocks_list.index(b)] for b in valid_proposals]
                        proposals = random.choices(valid_proposals, weights=subset_weights, k=8)
                    
                for blk in set(proposals):
                    y = apply_block(x, blk, max_len)
                    if y is not None:
                        new_k = k + max_len
                        new_S = cum_S + sum(blk[:max_len])
                        new_shifts = shifts + list(blk[:max_len])
                        
                        L_k = 138 - 0.2669 * new_k
                        delta = get_delta(new_k, TOTAL_K)
                        if abs(y.bit_length() - L_k) > delta:
                            continue
                            
                        next_beam.append((y, new_k, new_S, new_shifts))
            
            dedup = {}
            for state in next_beam:
                y, new_k, new_S, new_shifts = state
                sig = y & ((1<<64) - 1)
                
                L_k = 138 - 0.2669 * new_k
                score = -abs(y.bit_length() - L_k)
                
                sd_ratio = new_S / new_k if new_k > 0 else 1.33
                bin_idx = int(sd_ratio * 100) 
                
                key = (bin_idx, sig)
                if key not in dedup or dedup[key][1] < score:
                    dedup[key] = (state, score)
            
            sorted_cands = sorted(dedup.values(), key=lambda item: item[1], reverse=True)
            beam = [c[0] for c in sorted_cands[:W]]
            
            if (k_step + BLOCK_LEN) % 30 == 0 or (k_step + BLOCK_LEN) >= TOTAL_K:
                print(f"Step {min(TOTAL_K, k_step + BLOCK_LEN)}: Beam size {len(beam)}")
            
        if beam:
            print(f"Success! {len(beam)} survivors at depth {TOTAL_K}.")
            x_star = 20152090995747160937051
            
            found_xstar = False
            for state in beam:
                if state[0] == x_star:
                    found_xstar = True
                    break
                    
            print(f"Recovered x*: {found_xstar}")
            if found_xstar:
                print("Core grammar validated structurally!")
        else:
            print(f"Failed to reach depth {TOTAL_K}.")

if __name__ == "__main__":
    stage4a()
