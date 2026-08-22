import math
import multiprocessing
import sys
from collections import deque

def collatz_peak(n):
    pb = n.bit_length()
    cur = n
    d = 0
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
        else:
            cur = cur // 2
        d += 1
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb, d

def get_S_d(n):
    cur = n
    pb = cur.bit_length()
    peak_val = cur
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
        else:
            cur = cur // 2
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
            peak_val = cur
            
    cur = n
    S = 0
    d = 0
    while cur != peak_val:
        if cur % 2 != 0:
            cur = cur * 3 + 1
            d += 1
        else:
            cur = cur // 2
            S += 1
    return S, d

def reverse_tree_hr(center, depth=7):
    queue = deque([(center, 0)])
    leaves = []
    
    while queue:
        node, d = queue.popleft()
        if d == depth:
            leaves.append(node)
            continue
            
        queue.append((node * 2, d + 1))
        if (node - 1) % 3 == 0:
            odd_child = (node - 1) // 3
            if odd_child % 2 != 0 and odd_child > 1:
                queue.append((odd_child, d + 1))
                
    target_peak, _ = collatz_peak(center)
    hits = 0
    for leaf in leaves:
        p, _ = collatz_peak(leaf)
        if p == target_peak:
            hits += 1
            
    hr = hits / len(leaves) if leaves else 0
    return hr, len(leaves)

def worker(args):
    P, start_val, end_val = args
    candidates = []
    for c in range(start_val, end_val + 1):
        if c % 2 == 0: continue
        if c % 3 != 2: continue
        if ((3*c + 1) % 4) != 2: continue
        
        p, _ = collatz_peak(c)
        if p == P:
            hr, _ = reverse_tree_hr(c, depth=7)
            if hr > 0.05:
                S, d = get_S_d(c)
                candidates.append((c, hr, d, S))
    return candidates

def search_centers():
    missing_peaks = [15, 17, 20, 28, 29]
    results = {}
    
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    
    for P in missing_peaks:
        print(f"--- Searching for Peak {P} ---")
        sys.stdout.flush()
        target_bits_center = 0.498 * P + 6.29
        min_bits = max(1, math.floor(target_bits_center - 3))
        max_bits = math.ceil(target_bits_center + 3)
        
        start_val = 1 << (min_bits - 1)
        end_val = (1 << max_bits) - 1
        
        chunk_size = 100000
        ranges = []
        for i in range(start_val, end_val + 1, chunk_size):
            ranges.append((P, i, min(i + chunk_size - 1, end_val)))
            
        candidates = []
        for chunk_candidates in pool.imap_unordered(worker, ranges):
            candidates.extend(chunk_candidates)
            
        candidates.sort(key=lambda x: x[1], reverse=True)
        if candidates:
            best_c, best_hr, best_d, best_S = candidates[0]
            S_d_ratio = best_S / best_d if best_d > 0 else 0
            print(f"Found Center for Peak {P}: {best_c} (Bits: {best_c.bit_length()})")
            print(f"HR(depth=7): {best_hr:.4f}, d_peak: {best_d}, S/d: {S_d_ratio:.4f}")
            results[P] = (best_c, best_c.bit_length(), best_hr, best_d, best_S)
        else:
            print(f"No center found for Peak {P} in bit range [{min_bits}, {max_bits}]")
        sys.stdout.flush()

if __name__ == "__main__":
    search_centers()
