import numpy as np
import time
from multiprocessing import Pool

def build_Ps(n, s):
    mod_n = 3**n
    T = 2 * 3**(n-1)
    
    # State space V: numbers coprime to 3
    V = [x for x in range(mod_n) if x % 3 != 0]
    V_to_idx = {x: i for i, x in enumerate(V)}
    
    ln2 = np.log(2)
    weights = np.zeros(T + 1)
    denom = 1.0 - np.exp(T * (s - ln2))
    
    for a in range(1, T + 1):
        weights[a] = np.exp(a * (s - ln2)) / denom
        
    inv2 = pow(2, -1, mod_n)
    inv2_a = np.zeros(T + 1, dtype=np.int64)
    curr = 1
    for a in range(1, T + 1):
        curr = (curr * inv2) % mod_n
        inv2_a[a] = curr
        
    P_s = np.zeros((T, T), dtype=np.float64)
    
    for i, x in enumerate(V):
        base = (3 * x + 1) % mod_n
        for a in range(1, T + 1):
            y = (base * inv2_a[a]) % mod_n
            j = V_to_idx[y]
            P_s[i, j] += weights[a]
            
    return P_s

def compute_lambda_worker(args):
    n, s = args
    P_s = build_Ps(n, s)
    T = P_s.shape[0]
    
    v = np.ones(T, dtype=np.float64) / np.sqrt(T)
    for _ in range(100):
        v_next = P_s @ v
        norm = np.linalg.norm(v_next)
        if norm == 0:
            return s, np.nan
        v_next /= norm
        v = v_next
        
    rho = np.dot(v, P_s @ v)
    if rho <= 0: 
        return s, np.nan
    return s, np.log(rho)

def solve():
    ns = [5, 6, 7, 8]
    ss = np.linspace(-1.5, 0.68, 30)
    
    lambdas = {n: [] for n in ns}
    
    with Pool(processes=15) as pool: # 15 workers to balance load and avoid memory blowup
        for n in ns:
            t0 = time.time()
            args_list = [(n, s) for s in ss]
            
            # map over workers
            results = pool.map(compute_lambda_worker, args_list)
            
            # sort back into same order
            results.sort(key=lambda x: x[0])
            lambdas[n] = [res[1] for res in results]
            
            print(f'n={n} done in {time.time()-t0:.2f}s', flush=True)
        
    diffs = np.abs(np.array(lambdas[7]) - np.array(lambdas[8]))
    print(f'\nMax diff Lambda_7 vs Lambda_8: {np.nanmax(diffs):.6f}', flush=True)
    
    sigmas = np.linspace(1.0, 1.5, 50)
    L8 = np.array(lambdas[8])
    
    I_sigma = []
    for sigma in sigmas:
        valid_idx = ~np.isnan(L8)
        if not np.any(valid_idx):
            I_sigma.append(np.nan)
            continue
        I = np.max(ss[valid_idx] * sigma - L8[valid_idx])
        I_sigma.append(I)
        
    print('\nResults for I(sigma) at n=8:', flush=True)
    for sigma, I in zip(sigmas, I_sigma):
        if abs(sigma - 1.0) < 1e-4 or abs(sigma - 1.33) < 0.01:
            print(f'sigma = {sigma:.3f} -> I(sigma) = {I:.4f}', flush=True)

if __name__ == '__main__':
    solve()
