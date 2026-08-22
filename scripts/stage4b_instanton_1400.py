import random
import ast
from collections import Counter
import math
import json
import time

def load_grammar(csv_path):
    with open(csv_path, 'r') as f:
        line = f.readlines()[1]
    zone2_shifts = ast.literal_eval(line.strip().split(',"')[1].split('"')[0])
    core_shifts = zone2_shifts[-251:]
    
    bwd_shifts = core_shifts[::-1]
    
    BLOCK_LEN = 6
    blocks = []
    for i in range(len(bwd_shifts) - BLOCK_LEN + 1):
        blocks.append(tuple(bwd_shifts[i:i+BLOCK_LEN]))
    
    block_counts = Counter(blocks)
    
    T = 1.5
    block_weights = {b: count ** (1/T) for b, count in block_counts.items()}
    blocks_list = list(block_weights.keys())
    blocks_prob = [block_weights[b] for b in blocks_list]
    total_prob = sum(blocks_prob)
    blocks_prob = [p/total_prob for p in blocks_prob]
    
    return blocks_list, blocks_prob

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
    cap = 18.0
    c = 0.25
    delta_0 = 8.0
    
    if k > total_k * 0.9:
        base_delta = min(cap, delta_0 + c * math.sqrt(total_k * 0.9))
        progress = (k - total_k * 0.9) / (total_k * 0.1)
        return base_delta - progress * (base_delta - delta_0)
    else:
        return min(cap, delta_0 + c * math.sqrt(k))

def stage4b():
    blocks_list, blocks_prob = load_grammar('zone2_shifts.csv')
    
    TOTAL_K = 2500
    BLOCK_LEN = 6
    
    # Generate initial 1400-bit odd peaks
    beam = []
    for _ in range(64):
        x = random.randint((1 << 1399), (1 << 1400) - 1)
        if x % 2 == 0: x += 1
        beam.append((x, 0, 0, []))
        
    W = 100000 # Large beam width since space is vast
    
    print("Starting Stage 4b (Instanton Constructive Search) from 1400 bits")
    start_time = time.time()
    
    candidates = []
    
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
            valid_proposals = [b for b in blocks_list if apply_block(x, b, max_len) is not None]
            
            if not valid_proposals:
                continue
            
            # Family M sampling
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
                    
                    L_k = 1400 - 0.2788 * new_k # Glide from 1400 to 703
                    delta = get_delta(new_k, TOTAL_K)
                    if abs(y.bit_length() - L_k) > delta:
                        continue
                        
                    next_beam.append((y, new_k, new_S, new_shifts))
                    
                    if new_k >= 2460:
                        candidates.append((y, new_k, new_S, new_shifts))
        
        dedup = {}
        for state in next_beam:
            y, new_k, new_S, new_shifts = state
            sig = y & ((1<<64) - 1)
            
            L_k = 1400 - 0.2788 * new_k
            score = -abs(y.bit_length() - L_k)
            
            sd_ratio = new_S / new_k if new_k > 0 else 1.33
            bin_idx = int(sd_ratio * 100) 
            
            key = (bin_idx, sig)
            if key not in dedup or dedup[key][1] < score:
                dedup[key] = (state, score)
        
        sorted_cands = sorted(dedup.values(), key=lambda item: item[1], reverse=True)
        beam = [c[0] for c in sorted_cands[:W]]
        
        if (k_step + BLOCK_LEN) % 120 == 0:
            print(f"Step {min(TOTAL_K, k_step + BLOCK_LEN)}: Beam size {len(beam)}, Time elapsed: {time.time()-start_time:.1f}s")
        
    if candidates:
        print(f"SUCCESS! Found {len(candidates)} candidates.")
        with open("candidates_1400_instanton.json", "w") as f:
            out = []
            for c in candidates:
                y, k, S, shifts = c
                out.append({"x": str(y), "k": k, "S": S, "shifts": shifts[-50:]})
            json.dump(out, f)
    else:
        print(f"NULL result. No candidates found.")

if __name__ == "__main__":
    stage4b()
