"""
neuro_lyapunov.py
Neuroevolution search for a non-linear Lyapunov function for Collatz.
Uses a Genetic Algorithm to evolve weights of a Neural Network.
The NN defines V(n) = n * exp(NN(features(n))).
Target: V(Syr^d(n)) / V(n) < 1 for ALL n in a dataset of extremely hard numbers.
"""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import numpy as np
from numba import njit
import multiprocessing
import time

# --- Numba Kernels ---

@njit
def syr_step(n):
    val = 3 * n + 1
    while val % 2 == 0:
        val //= 2
    return val

@njit
def syr_d_steps(n, d):
    cur = n
    for _ in range(d):
        cur = syr_step(cur)
    return cur

@njit
def v2(x):
    c = 0
    while x > 0 and x % 2 == 0:
        c += 1
        x //= 2
    return c

@njit
def popcount(x):
    c = 0
    while x > 0:
        c += x & 1
        x >>= 1
    return c

@njit
def bitlen(x):
    c = 0
    while x > 0:
        c += 1
        x >>= 1
    return c

@njit
def extract_features(arr):
    N = len(arr)
    feats = np.empty((N, 6), dtype=np.float32)
    for i in range(N):
        n = arr[i]
        feats[i, 0] = v2(n + 1) / 10.0
        feats[i, 1] = v2(3 * n + 1) / 10.0
        feats[i, 2] = popcount(n) / bitlen(n)
        feats[i, 3] = (n % 16) / 16.0
        feats[i, 4] = (n % 256) / 256.0
        feats[i, 5] = 1.0
    return feats

def evaluate_nn(W, features):
    W1 = W[:96].reshape((6, 16))
    W2 = W[96:]
    # Pure NumPy vectorized dot products (uses AVX2 inside worker)
    h = np.tanh(np.dot(features, W1))
    out = np.dot(h, W2)
    return out

def fitness_kernel(W, feats_start, feats_end, log_ratios):
    nn_start = evaluate_nn(W, feats_start)
    nn_end = evaluate_nn(W, feats_end)
    
    val = log_ratios + nn_end - nn_start
    return np.max(val)

# --- Python Worker & GA ---

# Globals for workers to avoid IPC overhead
g_feats_start = None
g_feats_end = None
g_log_ratios = None

def init_worker(fs, fe, lr):
    global g_feats_start, g_feats_end, g_log_ratios
    g_feats_start = fs
    g_feats_end = fe
    g_log_ratios = lr

def evaluate_genome(W):
    return fitness_kernel(W, g_feats_start, g_feats_end, g_log_ratios)

def generate_hard_dataset(N_samples, d_steps):
    print(f"Generating dataset of {N_samples} hardest numbers...")
    np.random.seed(42)
    starts = []
    # 1. Shadow class (trailing ones) - the hardest proven cases!
    for a in range(2, 40):
        for m in range(1, 1000):
            starts.append(m * (1 << a) - 1)
    
    # 2. Random large odd numbers
    while len(starts) < N_samples:
        n = np.random.randint(10**6, 10**9)
        if n % 2 == 0: n += 1
        starts.append(n)
        
    starts = np.array(starts[:N_samples], dtype=np.int64)
    
    ends = np.zeros_like(starts)
    for i in range(N_samples):
        ends[i] = syr_d_steps(starts[i], d_steps)
        
    feats_start = extract_features(starts)
    feats_end = extract_features(ends)
    log_ratios = np.log(ends / starts)
    
    print(f"Max natural growth without V(n): {np.exp(log_ratios.max()):.2f}x")
    return feats_start, feats_end, log_ratios

def main():
    print("="*60)
    print(" NEURO-LYAPUNOV GENETIC SEARCH ")
    print(" 30-Core Parallel Evolution")
    print("="*60)
    
    D_STEPS = 5
    POPULATION_SIZE = 600
    GENERATIONS = 1000
    GENOME_SIZE = 16*6 + 16 # 112 weights
    
    fs, fe, lr = generate_hard_dataset(100_000, D_STEPS)
    
    # Initialize population (Gaussian random weights)
    population = np.random.randn(POPULATION_SIZE, GENOME_SIZE) * 0.5
    
    pool = multiprocessing.Pool(30, initializer=init_worker, initargs=(fs, fe, lr))
    
    print("\nStarting evolution... (Target: Best c* < 1.0)")
    print(f"{'Gen':>4} | {'Best c*':>10} | {'Mean c*':>10} | {'Time (s)':>8}")
    print("-" * 50)
    
    t_start = time.time()
    
    for gen in range(GENERATIONS):
        t0 = time.time()
        
        # Evaluate fitness in parallel
        fitnesses = pool.map(evaluate_genome, population)
        fitnesses = np.array(fitnesses)
        
        # We want to MINIMIZE max_log_ratio (fitness)
        # Convert log ratio to absolute ratio c*
        c_stars = np.exp(fitnesses)
        
        best_idx = np.argmin(c_stars)
        best_c = c_stars[best_idx]
        mean_c = np.mean(c_stars)
        
        dt = time.time() - t0
        
        if gen % 10 == 0 or best_c < 1.0:
            print(f"{gen:>4} | {best_c:>10.6f} | {mean_c:>10.6f} | {dt:>8.2f}")
            
        if best_c < 1.0:
            print("\n🔥🔥🔥 BREAKTHROUGH: NON-LINEAR LYAPUNOV FUNCTION FOUND! 🔥🔥🔥")
            print(f"c* = {best_c:.6f} < 1.0")
            np.save("data/best_lyapunov_weights.npy", population[best_idx])
            break
            
        # Selection & Reproduction
        # Keep top 10%
        n_elite = POPULATION_SIZE // 10
        elite_indices = np.argsort(c_stars)[:n_elite]
        elites = population[elite_indices]
        
        new_population = np.zeros_like(population)
        new_population[:n_elite] = elites
        
        # Breed the rest
        for i in range(n_elite, POPULATION_SIZE):
            p1, p2 = np.random.choice(n_elite, 2, replace=False)
            # Crossover
            mask = np.random.rand(GENOME_SIZE) > 0.5
            child = np.where(mask, elites[p1], elites[p2])
            # Mutation (dynamic rate)
            if np.random.rand() > 0.2:
                child += np.random.randn(GENOME_SIZE) * 0.1
            new_population[i] = child
            
        population = new_population

    print(f"\nEvolution finished in {(time.time() - t_start)/60:.1f} minutes.")

if __name__ == "__main__":
    main()
