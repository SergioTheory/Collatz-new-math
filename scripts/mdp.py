import numpy as np

transitions = {
    1: {'C1': 2, 'C2': 4},
    4: {'C1': 4, 'C2': 2},
    7: {'C1': 4, 'C2': 6},
    2: {'C1': 1, 'C2': 3},
    5: {'C1': 3, 'C2': 5},
    8: {'C1': 3, 'C2': 1}
}

states = [1, 4, 7, 2, 5, 8]
best_a = 100
best_pol = None

for i in range(64):
    pol = {}
    for j, s in enumerate(states):
        pol[s] = 'C1' if (i & (1 << j)) else 'C2'
        
    P = np.zeros((6, 6))
    for s in states:
        dest_class = pol[s]
        dests = [1,4,7] if dest_class == 'C1' else [2,5,8]
        s_idx = states.index(s)
        for d in dests:
            d_idx = states.index(d)
            P[s_idx, d_idx] = 1.0 / 3.0
            
    try:
        evals, evecs = np.linalg.eig(P.T)
        stat = evecs[:, np.isclose(evals, 1.0)]
        if stat.shape[1] == 0: continue
        stat = stat[:, 0].real
        if np.sum(stat) == 0: continue
        stat = stat / np.sum(stat)
        
        avg_a = 0
        for s in states:
            s_idx = states.index(s)
            avg_a += stat[s_idx] * transitions[s][pol[s]]
            
        if avg_a < best_a and avg_a > 0.1:
            best_a = avg_a
            best_pol = pol
    except Exception as e:
        continue

print(f"Minimum average a: {best_a}")
print("Best Policy:", best_pol)
