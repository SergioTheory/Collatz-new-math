import numpy as np
import math
import os

def build_joint_dist(max_k=30, max_S=250):
    p_X = {}
    for b in range(2, max_S + 1):
        if b == 3: continue
        p_X[b] = (4 * (b - 1)) / (3 * (2**b))
    
    dist_S = {1: {3: 1.0}}
    for k in range(2, max_k + 1):
        dist_S[k] = {}
        for s_prev, p_prev in dist_S[k-1].items():
            for x, p_x in p_X.items():
                s_new = s_prev + x
                if s_new <= max_S:
                    dist_S[k][s_new] = dist_S[k].get(s_new, 0.0) + p_prev * p_x
                    
    joint_dist = {}
    for k in range(1, max_k + 1):
        p_k = (0.75**(k-1)) * 0.25
        for S, p_S in dist_S[k].items():
            joint_dist[(k, S)] = p_k * p_S
            
    return joint_dist

def is_white(j, l, s, n, eps):
    j, l, s, n = int(j), int(l), int(s), int(n)
    power = n - 2*j + 2
    if power <= 0: return True 
    mod = 3**power
    num = pow(2, s - l + 1, mod)
    theta = num / mod
    if theta > 0.5: theta -= 1.0
    return abs(theta) > eps

def mc_polymer_validation(n, s, eps, joint_dist, num_trials=50000):
    max_j = n // 2
    steps = list(joint_dist.keys())
    probs = list(joint_dist.values())
    sum_p = sum(probs)
    probs = [p/sum_p for p in probs]
    
    eta = eps ** 3
    total_weight = 0.0
    
    for _ in range(num_trials):
        j, l = 0, 0
        weight = 1.0
        while j <= max_j:
            if is_white(j, l, s, n, eps):
                weight *= math.exp(-eta)
                
            idx = np.random.choice(len(steps), p=probs)
            k, S = steps[idx]
            j += k
            l += S
            
        total_weight += weight
        
    Q_00_mc = total_weight / num_trials
    F_mc = -math.log(Q_00_mc) / n if Q_00_mc > 0 else None
    return F_mc, Q_00_mc

if __name__ == "__main__":
    print("Building joint distribution for MC...")
    joint_dist = build_joint_dist(max_k=30, max_S=250)
    
    n = 100
    eps = 0.05
    
    if os.path.exists('worst_s.txt'):
        with open('worst_s.txt', 'r') as f:
            s_worst = int(f.read().strip())
    else:
        s_worst = 158
        
    print(f"\n=== Stage 3: Monte Carlo Validation (n={n}, s={s_worst}, eps={eps}) ===")
    print(f"Running 100,000 random walks with true 2D drift (mean slope = 4)...")
    
    F_mc, Q_00_mc = mc_polymer_validation(n, s_worst, eps, joint_dist, num_trials=10000)
    print(f"MC Result: Q(0,0) = {Q_00_mc:.4e}, F(nats) = {F_mc:.6f}")
