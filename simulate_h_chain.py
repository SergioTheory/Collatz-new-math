import numpy as np
import scipy.linalg as la
from scipy.optimize import root_scalar

def construct_reverse_matrix_and_shifts(n, s):
    dim = 3**n
    T = 2 * 3**(n-1) if n > 0 else 1
    M = np.zeros((dim, dim))
    Shift_sum = np.zeros((dim, dim))
    q = np.exp(s - np.log(2))
    
    pow2 = [1]
    for _ in range(T):
        pow2.append((pow2[-1] * 2) % dim)
        
    valid_states = [x for x in range(dim) if x % 3 != 0]
    k_dim = len(valid_states)
    state_to_idx = {x: i for i, x in enumerate(valid_states)}
    idx_to_state = {i: x for i, x in enumerate(valid_states)}
    
    for i in range(k_dim):
        x = idx_to_state[i]
        for a in range(1, T+1):
            if (x * pow2[a]) % 3 == 1:
                num = (x * pow2[a] - 1) % (3 * dim)
                if num % 3 == 0:
                    y = (num // 3) % dim
                    if y % 3 != 0:
                        j = state_to_idx[y]
                        weight = (q**a) / (1 - q**T)
                        M[i, j] += weight
                        Shift_sum[i, j] += a * weight
    return M, Shift_sum, valid_states

def get_mean_shift(n, s):
    M, Shift_sum, valid = construct_reverse_matrix_and_shifts(n, s)
    eigenvalues, eigenvectors_R = la.eig(M, left=False, right=True)
    eigenvalues_L, eigenvectors_L = la.eig(M, left=True, right=False)
    
    idx = np.argsort(np.abs(eigenvalues))[::-1]
    rho = np.real(eigenvalues[idx[0]])
    h_R = np.real(eigenvectors_R[:, idx[0]])
    if np.sum(h_R) < 0: h_R = -h_R
    
    idx_L = np.argsort(np.abs(eigenvalues_L))[::-1]
    h_L = np.real(eigenvectors_L[:, idx_L[0]])
    if np.sum(h_L) < 0: h_L = -h_L
    
    k_dim = len(valid)
    P_h = np.zeros((k_dim, k_dim))
    Expected_a = np.zeros((k_dim, k_dim))
    
    for i in range(k_dim):
        for j in range(k_dim):
            if M[i,j] > 0:
                P_h[i, j] = M[i, j] * h_R[j] / (rho * h_R[i])
                Expected_a[i, j] = Shift_sum[i, j] / M[i, j]
                
    row_sums = P_h.sum(axis=1)
    P_h = P_h / row_sums[:, np.newaxis]
                
    pi_h = h_L * h_R
    pi_h /= np.sum(pi_h)
    
    mean_a = 0.0
    for i in range(k_dim):
        for j in range(k_dim):
            mean_a += pi_h[i] * P_h[i, j] * Expected_a[i, j]
            
    return mean_a

def find_root(n, target):
    def obj(s):
        return get_mean_shift(n, s) - target
    # Unconditioned (s=0) is mean ~2. Negative tilts lower the mean.
    res = root_scalar(obj, bracket=[-5.0, 0.0], method='brentq')
    return res.root

if __name__ == "__main__":
    for s in [0.0, -1.0, -2.0, -3.0]:
        print(f"s = {s:.1f}: mean = {get_mean_shift(6, s):.4f}")
    s_star = find_root(6, 1.3333333)
    print(f"\nFor n=6, the tilt s required for a mean shift of 1.33 is s = {s_star:.5f}")
