import numpy as np
from multiprocessing.dummy import Pool as ThreadPool
from numba import njit
import time
import math

XIS = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17, 31, 32, 64, 128]
XIS = np.array([xi for xi in XIS if xi % 3 != 0], dtype=np.uint64)

@njit(nogil=True)
def mul_mod(a, b, m):
    a = np.uint64(a)
    b = np.uint64(b)
    m = np.uint64(m)
    
    a_hi = a >> np.uint64(32)
    a_lo = a & np.uint64(0xFFFFFFFF)
    
    res_hi = (a_hi * b) % m
    for _ in range(32):
        res_hi = (res_hi * np.uint64(2)) % m
        
    res_lo = (a_lo * b) % m
    return (res_hi + res_lo) % m

@njit(nogil=True)
def worker_mc(n, s, num_samples, xis, inv2_table, mod3n, seed):
    np.random.seed(seed)
    num_xis = len(xis)
    sum_cos = np.zeros(num_xis, dtype=np.float64)
    sum_sin = np.zeros(num_xis, dtype=np.float64)
    
    out = np.empty(n, dtype=np.int32)
    arr = np.empty(n - 1, dtype=np.int32)
    
    mod3n_u = np.uint64(mod3n)
    use_fast_mul = mod3n_u <= np.uint64(4294967295)
    
    for _ in range(num_samples):
        # sample composition
        count = 0
        while count < n - 1:
            val = np.random.randint(1, s)
            found = False
            for i in range(count):
                if arr[i] == val:
                    found = True
                    break
            if not found:
                arr[count] = val
                count += 1
        arr.sort()
        last = 0
        for i in range(n - 1):
            out[i] = arr[i] - last
            last = arr[i]
        out[n-1] = s - last
        
        # calculate trajectory
        y = np.uint64(0)
        for i in range(n):
            a = out[i]
            y = (np.uint64(3) * y + np.uint64(1)) % mod3n_u
            if use_fast_mul:
                y = (y * inv2_table[a]) % mod3n_u
            else:
                y = mul_mod(y, inv2_table[a], mod3n_u)
            
        # calc fourier
        for i in range(num_xis):
            angle = -2.0 * math.pi * float(xis[i]) * float(y) / float(mod3n)
            sum_cos[i] += math.cos(angle)
            sum_sin[i] += math.sin(angle)
            
    return sum_cos, sum_sin

def run_simulation(n, s, total_samples=10**8, num_workers=30):
    mod3n = 3**n
    inv2 = pow(2, -1, mod3n)
    inv2_table = np.array([pow(inv2, a, mod3n) for a in range(s + 1)], dtype=np.uint64)
    
    samples_per_worker = total_samples // num_workers
    args = []
    import random
    for i in range(num_workers):
        seed = random.randint(0, 2**31 - 1)
        args.append((n, s, samples_per_worker, XIS, inv2_table, mod3n, seed))
        
    with ThreadPool(num_workers) as pool:
        results = pool.starmap(worker_mc, args)
        
    total_cos = np.zeros(len(XIS), dtype=np.float64)
    total_sin = np.zeros(len(XIS), dtype=np.float64)
    for sum_cos, sum_sin in results:
        total_cos += sum_cos
        total_sin += sum_sin
        
    total_cos /= total_samples
    total_sin /= total_samples
    magnitudes = np.sqrt(total_cos**2 + total_sin**2)
    max_mag = np.max(magnitudes)
    max_xi = XIS[np.argmax(magnitudes)]
    
    return max_mag, max_xi

if __name__ == "__main__":
    test_cases = [
        (8, 16),
        (12, 24),
        (16, 32),
        (20, 40)
    ]
    
    print("Testing Sum-Conditioned Fourier Decay (Allikvere Theorem B)")
    print("Sampling 10^8 compositions per layer using Numba JIT")
    print("-" * 50)
    print(f"{'n':<4} | {'s':<4} | {'Max Mag M(n,s)':<14} | {'At xi':<6}")
    print("-" * 50)
    for n, s in test_cases:
        t0 = time.time()
        max_mag, max_xi = run_simulation(n, s, total_samples=10**8, num_workers=20)
        t1 = time.time()
        print(f"{n:<4} | {s:<4} | {max_mag:.6f}       | {max_xi:<6} (took {t1-t0:.1f}s)")
