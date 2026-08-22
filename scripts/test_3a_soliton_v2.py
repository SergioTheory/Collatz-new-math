import multiprocessing
import os

pow2_mod9 = [ (1<<a)%9 for a in range(10) ]
pow2_mod9[0] = 1 

X0 = 705289985300017165728597776119331502225569
X0_even = 3 * X0 + 1

def get_lookahead(y, max_steps=40):
    curr = y
    steps = 0
    for i in range(max_steps):
        c3 = curr % 3
        if c3 == 0:
            break
        a = 2 if c3 == 1 else 1
        curr = (curr * (1 << a) - 1) // 3
        steps += 1
    return steps

def process_chunk(chunk_data):
    chunk, k_step, L0 = chunk_data
    cands = []
    local_deaths = {'corridor': 0, 'S-d': 0, 'mod3_0': 0, 'peak_guard': 0, 'even': 0}
    
    for state in chunk:
        x, k, cum_S, shifts = state
        
        start_a = 2 if x % 3 == 1 else 1
        # Action space: {parity, parity+2, parity+4, parity+6}
        for a in [start_a, start_a + 2, start_a + 4, start_a + 6]:
            y = ((x << a) - 1) // 3
            if y <= 0 or y % 2 == 0:
                local_deaths['even'] += 1
                continue
                
            if y % 3 == 0:
                local_deaths['mod3_0'] += 1
                continue
                
            if y > X0:
                local_deaths['peak_guard'] += 1
                continue
                
            new_k = k + 1
            new_S = cum_S + a
            
            # Target linear corridor
            L_k = L0 - 0.25 * new_k
            bit_diff = abs(y.bit_length() - L_k)
            
            if bit_diff > 15:
                local_deaths['corridor'] += 1
                continue
                
            sd = new_S / new_k
            if new_k > 150 and sd > 1.40:
                local_deaths['S-d'] += 1
                continue
                
            lookahead_val = get_lookahead(y, 40)
            
            # Score: trade-off between corridor adherence and future pure run length
            # We penalize bit_diff and high average a (to enforce sd ~ 1.33)
            # a_penalty = max(0, sd - 1.33) * 50  # roughly 5 points per 0.1 deviation
            score = -bit_diff + 2.0 * lookahead_val
            
            new_shifts = (shifts + [a])[-50:]
            new_state = (y, new_k, new_S, new_shifts)
            sig = y & ((1<<64) - 1)
            
            cands.append((sig, score, new_state))
                
    return cands, local_deaths

def deduplicate_and_sort(cands, limit):
    dedup = {}
    for sig, score, st in cands:
        if sig not in dedup or dedup[sig][1] < score:
            dedup[sig] = (st, score)
            
    unique = list(dedup.values())
    unique.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in unique[:limit]]

def stage3a_soliton():
    n = 161118544943626166412582673973375097
    k = 89
    S = 119
    shifts = [1, 1, 2] * 29 + [1, 1] 
    
    beam = [(n, k, S, shifts)]
    L0 = 140.0
    
    W = 30000
    
    death_stats = {'corridor': 0, 'S-d': 0, 'mod3_0': 0, 'peak_guard': 0, 'even': 0}
    num_workers = min(30, multiprocessing.cpu_count())
    pool = multiprocessing.Pool(processes=num_workers)
    
    for k_step in range(89, 270):
        if not beam:
            print(f"Beam died at step {k_step}")
            print(f"Death stats right before death: {death_stats}")
            break
            
        chunk_size = max(1, len(beam) // num_workers)
        chunks = [beam[i:i + chunk_size] for i in range(0, len(beam), chunk_size)]
        results = pool.map(process_chunk, [(chunk, k_step, L0) for chunk in chunks])
        
        merged_cands = []
        for cands, local_d in results:
            for key, val in local_d.items():
                death_stats[key] += val
            merged_cands.extend(cands)
            
        beam = deduplicate_and_sort(merged_cands, W)
        
        if k_step % 10 == 0:
            print(f"--- Checkpoint k={k_step} ---")
            print(f"Beam size: {len(beam)}")
            print("Death stats:", death_stats)
            if beam:
                bits = sorted([st[0].bit_length() for st in beam])
                print(f"Bits (p10/p50/p90): {bits[int(len(bits)*0.1)]} / {bits[int(len(bits)*0.5)]} / {bits[int(len(bits)*0.9)]}")
                
                # S/d average
                sd_vals = [st[2]/st[1] for st in beam]
                sd_avg = sum(sd_vals) / len(sd_vals)
                print(f"Avg S/d: {sd_avg:.4f}")
                
                # lookahead average
                lookaheads = [get_lookahead(st[0], 40) for st in beam]
                la_avg = sum(lookaheads) / len(lookaheads)
                print(f"Avg Lookahead: {la_avg:.1f} steps")
                
        if k_step == 269:
            print(f"--- Final verification at k={k_step} ---")
            print(f"Beam size: {len(beam)}")
            successes = [st for st in beam if 71 <= st[0].bit_length() <= 80]
            print(f"Found {len(successes)} branches in 71-80 bit window!")
            
            successes.sort(key=lambda st: st[0])
            for st in successes[:10]:
                ratio = X0_even / st[0]
                print(f"Candidate bits: {st[0].bit_length()}, num: {st[0]}, ratio: {ratio:.2f}, S: {st[2]}")
            break
            
if __name__ == "__main__":
    stage3a_soliton()
