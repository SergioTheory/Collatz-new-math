import numpy as np
import matplotlib.pyplot as plt

def compute_theta(j, l, s, n):
    j, l, s, n = int(j), int(l), int(s), int(n)
    power = n - 2*j + 2
    if power <= 0: return 0.0
    mod = 3**power
    num = pow(2, s - l + 1, mod)
    theta = num / mod
    if theta > 0.5: theta -= 1.0
    return theta

def is_white_point(j, l, s, n, epsilon=0.05):
    return abs(compute_theta(j, l, s, n)) > epsilon

def visualize_white_black_regions(n, s, epsilon=0.05, max_j=50, max_l=100):
    j_vals = np.arange(1, max_j + 1)
    l_vals = np.arange(-max_l, max_l + 1)
    J, L = np.meshgrid(j_vals, l_vals)
    is_white = np.zeros_like(J, dtype=bool)
    for i in range(len(l_vals)):
        for j_idx in range(len(j_vals)):
            is_white[i, j_idx] = is_white_point(j_vals[j_idx], l_vals[i], s, n, epsilon)
    plt.figure(figsize=(12, 8))
    plt.imshow(is_white, aspect='auto', origin='lower', extent=[1, max_j, -max_l, max_l], cmap='RdBu')
    plt.colorbar(label='White (True) / Black (False)')
    plt.xlabel('j')
    plt.ylabel('l')
    plt.title(f'White/Black regions for s={s}, n={n}, eps={epsilon}')
    plt.savefig(f'white_black_n{n}_s{s}_eps{epsilon}.png', dpi=150, bbox_inches='tight')
    plt.close()

def analyze_triangle_structure(n, s, epsilon=0.05):
    black_points = []
    for j in range(1, 30):
        for l in range(-50, 50):
            if not is_white_point(j, l, s, n, epsilon):
                black_points.append((j, l))
    print(f"Found {len(black_points)} black points")
    if len(black_points) < 2: return
    from scipy.spatial.distance import pdist, squareform
    dist_matrix = squareform(pdist(black_points))
    clusters = []
    visited = set()
    for i, point in enumerate(black_points):
        if i in visited: continue
        cluster = [point]
        visited.add(i)
        queue = [i]
        while queue:
            current = queue.pop(0)
            for j, other_point in enumerate(black_points):
                if j not in visited and dist_matrix[current, j] < 2:
                    cluster.append(other_point)
                    visited.add(j)
                    queue.append(j)
        clusters.append(cluster)
    print(f"Found {len(clusters)} clusters (triangles)")
    if clusters:
        sizes = [len(c) for c in clusters]
        print(f"Triangle sizes: min={min(sizes)}, max={max(sizes)}, mean={np.mean(sizes):.1f}")

if __name__ == "__main__":
    for n in [50, 100]:
        for s in [79, 158]:
            print(f"n={n}, s={s}")
            visualize_white_black_regions(n, s, 0.05, 40, 80)
            analyze_triangle_structure(n, s, 0.05)
