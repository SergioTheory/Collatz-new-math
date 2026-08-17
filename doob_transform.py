import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import math
import time

def build_operator_and_sim_data(n, s, A_max=600):
    N = 3**n
    valid_states = [x for x in range(N) if x % 3 != 0]
    state_to_idx = {x: i for i, x in enumerate(valid_states)}
    M = len(valid_states)
    
    row = []
    col = []
    data = []
    
    # We also want to store the transitions for simulation
    # transitions[i] = list of (a, next_idx, unnormalized_P_h_weight)
    # We will fill this later after finding h.
    # For now, just store (i, next_idx, a, weight)
    trans_list = []
    
    p2_mod = [pow(2, a, N*3) for a in range(A_max + 10)]
    
    for i, x in enumerate(valid_states):
        a0 = 2 if x % 3 == 1 else 1
            
        for k in range(A_max // 2):
            a = a0 + 2 * k
            y = (x * p2_mod[a] - 1) // 3 % N
            if y % 3 == 0:
                continue
            weight = 2.0 ** ((s - 1.0) * a)
            
            j = state_to_idx[y]
            row.append(i)
            col.append(j)
            data.append(weight)
            trans_list.append((i, j, a, weight))
            
    P_matrix = sp.csr_matrix((data, (row, col)), shape=(M, M))
    return P_matrix, valid_states, trans_list

def analyze_doob():
    n_list = [8, 9, 10]
    s_values = [0.0, 0.5, 0.8]
    
    for s in s_values:
        print(f"\n{'='*50}\nAnalyzing s = {s}\n{'='*50}")
        
        sim_data = None
        
        for n in n_list:
            t0 = time.time()
            P_mat, valid_states, trans_list = build_operator_and_sim_data(n, s, A_max=600)
            
            # Eigenvalues
            vals, vecs = spla.eigs(P_mat, k=2, which='LR', tol=1e-10)
            
            idx = np.argsort(np.real(vals))[::-1]
            vals = vals[idx]
            vecs = vecs[:, idx]
            
            rho = np.real(vals[0])
            h = np.real(vecs[:, 0])
            
            if np.mean(h) < 0:
                h = -h
                
            h = h / np.mean(h)
            
            max_h = np.max(h)
            min_h = np.min(h)
            ratio = max_h / min_h
            
            # Lipschitz on cylinder of size 3^{n-1}
            mod_base = 3**(n-1)
            groups = {}
            for i, x in enumerate(valid_states):
                rem = x % mod_base
                if rem not in groups:
                    groups[rem] = []
                groups[rem].append(h[i])
                
            max_diff = 0
            for rem, vals_in_group in groups.items():
                if len(vals_in_group) > 1:
                    max_diff = max(max_diff, max(vals_in_group) - min(vals_in_group))
                    
            lambda_2_P = vals[1]
            gap = 1.0 - np.abs(lambda_2_P) / rho
            
            print(f"n={n:2d} | rho={rho:.4f} | max/min(h)={ratio:.4f} | max_diff(3^{n-1})={max_diff:.4e} | gap={gap:.4e} | time={time.time()-t0:.2f}s")
            
            # Save n=10 data for simulation
            if n == 10:
                sim_data = (valid_states, trans_list, h, rho)
                
        # Run simulation for n=10
        if sim_data:
            print(f"\n  [Simulation for s={s}, n=10]")
            valid_states, trans_list, h, rho = sim_data
            M = len(valid_states)
            
            # Build fast transition choice arrays
            probs = [[] for _ in range(M)]
            shifts = [[] for _ in range(M)]
            next_states = [[] for _ in range(M)]
            
            for (i, j, a, weight) in trans_list:
                p_h = weight * h[j] / (rho * h[i])
                probs[i].append(p_h)
                shifts[i].append(a)
                next_states[i].append(j)
                
            for i in range(M):
                S = sum(probs[i])
                probs[i] = [p / S for p in probs[i]] # normalize to exactly 1
                
            # Simulate paths
            num_paths = 5000
            d_values = [10, 20, 40, 80]
            max_d = max(d_values)
            
            # Start from random states
            current_states = np.random.randint(0, M, size=num_paths)
            total_shifts = np.zeros(num_paths)
            
            print(f"  {'d':<5} | {'Mean Shift':<12} | {'Var(S/d)':<12} | {'Var * d (const?)':<15}")
            
            for step in range(1, max_d + 1):
                new_states = np.zeros(num_paths, dtype=np.int32)
                new_shifts = np.zeros(num_paths)
                for p_idx in range(num_paths):
                    u = current_states[p_idx]
                    choice = np.random.choice(len(next_states[u]), p=probs[u])
                    new_states[p_idx] = next_states[u][choice]
                    new_shifts[p_idx] = shifts[u][choice]
                    
                current_states = new_states
                total_shifts += new_shifts
                
                if step in d_values:
                    mean_shift = np.mean(total_shifts / step)
                    var_shift = np.var(total_shifts / step)
                    print(f"  {step:<5} | {mean_shift:<12.5f} | {var_shift:<12.6f} | {var_shift * step:<15.6f}")

if __name__ == '__main__':
    analyze_doob()
