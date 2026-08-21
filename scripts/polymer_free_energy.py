import numpy as np

class PolymerFreeEnergy:
    def __init__(self, n, s, epsilon=0.05):
        self.n, self.s, self.epsilon = n, s, epsilon
        
    def compute_theta(self, j, l):
        j, l = int(j), int(l)
        power = self.n - 2*j + 2
        if power <= 0: return 0.0
        mod = 3**power
        num = pow(2, self.s - l + 1, mod)
        theta = num / mod
        if theta > 0.5: theta -= 1.0
        return theta
    
    def is_white(self, j, l):
        return abs(self.compute_theta(j, l)) > self.epsilon
    
    def compute_Q_dp(self, max_j=None, max_l_range=100):
        if max_j is None: max_j = self.n // 2
        l_values = np.arange(-max_l_range, max_l_range + 1)
        l_to_idx = {l: idx for idx, l in enumerate(l_values)}
        Q = np.ones((max_j + 1, len(l_values)))
        eta = self.epsilon ** 3
        
        for j in range(max_j, -1, -1):
            for l_idx, l in enumerate(l_values):
                white_factor = np.exp(-eta) if self.is_white(j, l) else 1.0
                expected_Q = 0.0
                max_k = 20
                for k in range(1, max_k + 1):
                    prob = (0.75 ** (k - 1)) * 0.25
                    new_j, new_l = j + k, l + 3
                    if new_j > max_j or new_l not in l_to_idx:
                        Q_next = 1.0
                    else:
                        Q_next = Q[new_j, l_to_idx[new_l]]
                    expected_Q += prob * Q_next
                expected_Q += (0.75 ** max_k) * 1.0
                Q[j, l_idx] = white_factor * expected_Q
        return Q, l_values
    
    def compute_free_energy(self, Q, l_values):
        l_idx = list(l_values).index(0) if 0 in l_values else np.argmin(np.abs(l_values))
        Q_00 = Q[0, l_idx]
        return -np.log(Q_00) / self.n if Q_00 > 0 else None, Q_00

if __name__ == "__main__":
    results = []
    for n in [50, 100, 150]:
        for s in [79, 158, 238]:
            for eps in [0.02, 0.05, 0.10]:
                pfe = PolymerFreeEnergy(n, s, eps)
                Q, l_values = pfe.compute_Q_dp(max_l_range=50)
                F, Q_00 = pfe.compute_free_energy(Q, l_values)
                if F is not None:
                    print(f"n={n}, s={s}, eps={eps}: F(nats)={F:.6f}, F(bits)={F/np.log(2):.6f}")
