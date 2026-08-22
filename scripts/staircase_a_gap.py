import numpy as np
import scipy.linalg as la

def construct_reverse_matrix(n, s):
    dim = 3**n
    T = 2 * 3**(n-1) if n > 0 else 1
    q = np.exp(s - np.log(2))
    pow2 = [1]
    for _ in range(T):
        pow2.append((pow2[-1] * 2) % dim)
        
    valid_states = [x for x in range(dim) if x % 3 != 0]
    k_dim = len(valid_states)
    state_to_idx = {x: i for i, x in enumerate(valid_states)}
    idx_to_state = {i: x for i, x in enumerate(valid_states)}
    
    M = np.zeros((k_dim, k_dim))
    for i in range(k_dim):
        x = idx_to_state[i]
        for a in range(1, T+1):
            if (x * pow2[a]) % 3 == 1:
                num = (x * pow2[a] - 1) % (3 * dim)
                if num % 3 == 0:
                    y = (num // 3) % dim
                    if y % 3 != 0:
                        j = state_to_idx[y]
                        M[i, j] += (q**a) / (1 - q**T)
    return M

def analyze(n, s):
    M = construct_reverse_matrix(n, s)
    # Right eigenvector
    eigenvalues, eigenvectors_R = la.eig(M, left=False, right=True)
    idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors_R = eigenvectors_R[:, idx]
    
    rho = np.abs(eigenvalues[0])
    lambda2 = np.abs(eigenvalues[1])
    gap_ratio = lambda2 / rho
    gap = 1.0 - gap_ratio
    
    h_R = np.real(eigenvectors_R[:, 0])
    if np.sum(h_R) < 0: h_R = -h_R
    
    h_R_valid = h_R[h_R > 1e-12]
    if len(h_R_valid) > 0:
        max_min = np.max(h_R_valid) / np.min(h_R_valid)
    else:
        max_min = float('inf')
        
    print(f"n={n}, s={s:.1f}: rho={rho:.4f}, lambda2={lambda2:.4f}, gap={gap:.4f}, max/min={max_min:.1f}")

if __name__ == "__main__":
    for n in [5, 6, 7]:
        for s in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
            analyze(n, s)
