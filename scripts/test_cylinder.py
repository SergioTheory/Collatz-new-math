import numpy as np

def test_cylinder():
    M = 10
    d = 5
    S = 9
    w = (1, 1, 1, 1, 5) # Sum = 9
    
    K = 1 << M
    r_w = None
    for z in range(K):
        N = 2 * z + 1
        curr = N
        S_val = 0
        word = []
        for step in range(1, d + 1):
            curr = 3 * curr + 1
            a = 0
            while curr % 2 == 0:
                a += 1
                curr //= 2
            word.append(a)
            S_val += a
        if tuple(word) == w:
            r_w = z % (1 << S)
            break
            
    print(f"r_w = {r_w} for word {w}")
    
    # Now sum the phases for this cylinder for h=1
    h = 1
    sum_phase = 0j
    count = 0
    for q in range(1 << (M - S)):
        z = r_w + q * (1 << S)
        
        phase = -2 * np.pi * h * z / K
        sum_phase += np.exp(1j * phase)
        count += 1
        
    print(f"Total z in cylinder: {count}")
    print(f"Sum of phases for h=1: {sum_phase}")
    
    # What about h=2?
    h = 2
    sum_phase_2 = 0j
    for q in range(1 << (M - S)):
        z = r_w + q * (1 << S)
        phase = -2 * np.pi * h * z / K
        sum_phase_2 += np.exp(1j * phase)
    print(f"Sum of phases for h=2: {sum_phase_2}")

test_cylinder()
