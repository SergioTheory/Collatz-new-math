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

def test():
    x = ( (1<<139) - 1 ) // 3 + 1
    if x % 4 != 3: x += (3 - x % 4)
    # sprint
    curr = x
    s_steps = 0
    while curr % 3 == 2 and s_steps < 8:
        y = (curr * 2 - 1) // 3
        if y % 2 == 1:
            curr = y
            s_steps += 1
        else:
            break
            
    beam = [(curr, s_steps, s_steps)]
    
    for step in range(30):
        next_beam = []
        for x, k, S in beam:
            cands = reverse_step(x)
            for y, a in cands:
                next_beam.append((y, k+1, S+a))
        
        # print stats
        if not next_beam:
            print(f"Died at step {step}")
            break
            
        dedup = {}
        for st in next_beam:
            sig = st[0] & ((1<<64)-1)
            dedup[sig] = st
        beam = list(dedup.values())[:1000]
        
        # stats
        k_val = beam[0][1]
        s_vals = [st[2]/k_val for st in beam]
        bit_lens = [st[0].bit_length() for st in beam]
        print(f"Step {step}, k={k_val}, S/d avg={sum(s_vals)/len(s_vals):.2f}, bits avg={sum(bit_lens)/len(bit_lens):.1f}")
        
test()
