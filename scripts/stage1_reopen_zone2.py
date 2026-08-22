import math

def reverse_step_grammar(x, k, phase18):
    cands = []
    for a in (1, 2, 3, 4, 5, 6, 7, 8):
        num = (x << a) - 1
        if num % 3 != 0:
            continue
        y = num // 3
        if y <= 0 or y % 2 == 0 or y % 3 == 0:
            continue
        
        # grammar: a>=3 only in phases {0,5,9} of T=18 clock
        if k < 90:
            if a >= 3 and phase18 not in (0, 5, 9):
                continue
            
        cands.append((y, a))
    return cands

def stage1_beam_search():
    # To get the true end of the core:
    x = 20152090995747160937051
    shifts = []
    for i in range(252): # 252 shifts according to CSV
        y = 3*x + 1
        a = (y & -y).bit_length() - 1
        shifts.append(a)
        x = y >> a
    
    end_of_core_odd = x
    print(f"Start reverse search from: {end_of_core_odd}")
    
    beam = {end_of_core_odd}
    
    for k in range(252):
        next_beam = set()
        phase18 = k % 18
        for val in beam:
            cands = reverse_step_grammar(val, k, phase18)
            for y, a in cands:
                expected_bits = 140 - (k+1) * 0.255 # roughly
                if abs(y.bit_length() - expected_bits) < 15:
                    next_beam.add(y)
                    
        if len(next_beam) > 50000:
            sorted_beam = sorted(list(next_beam), key=lambda y: abs(y.bit_length() - (140 - (k+1)*0.255)))
            next_beam = set(sorted_beam[:50000])
        beam = next_beam
        if k % 50 == 0:
            print(f"Step {k}: beam size {len(beam)}")
            
    success = [y for y in beam if 71 <= y.bit_length() <= 87]
    print(f"Found {len(success)} candidates in 71-87 bits.")
    
    x_star_hits = 0
    x_star = 20152090995747160937051
    for y in success:
        curr = y
        hit = False
        while curr > 1 and curr.bit_length() <= 145:
            if curr == x_star:
                hit = True
                break
            if curr % 2 != 0: curr = 3*curr + 1
            else: curr //= 2
        if hit: x_star_hits += 1
        
    print(f"Candidates hitting x*: {x_star_hits} out of {len(success)}")

if __name__ == "__main__":
    stage1_beam_search()
