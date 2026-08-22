import multiprocessing
from collections import deque
import math

def collatz_peak(n):
    pb = n.bit_length()
    cur = n
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
        else:
            cur = cur // 2
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb

def reverse_tree_hr_depths(args):
    target_peak, center, max_depth = args
    queue = deque([(center, 0)])
    
    # Store nodes at each depth
    nodes_by_depth = {d: [] for d in range(1, max_depth + 1)}
    
    while queue:
        node, d = queue.popleft()
        if d == max_depth:
            continue
            
        c1 = node * 2
        queue.append((c1, d + 1))
        nodes_by_depth[d + 1].append(c1)
        
        if (node - 1) % 3 == 0:
            c2 = (node - 1) // 3
            if c2 % 2 != 0 and c2 > 1:
                queue.append((c2, d + 1))
                nodes_by_depth[d + 1].append(c2)
                
    results = {}
    for d in [7, 10, 15]:
        if d <= max_depth:
            leaves = nodes_by_depth[d]
            if not leaves:
                results[d] = (0, 0)
                continue
            hits = 0
            for leaf in leaves:
                if collatz_peak(leaf) == target_peak:
                    hits += 1
            results[d] = (hits, len(leaves))
            
    return target_peak, center, results

def worker(P):
    target_bits_center = 0.6201 * P + 2.285
    min_bits = max(1, math.floor(target_bits_center - 3))
    max_bits = math.ceil(target_bits_center + 3)
    
    start_val = 1 << (min_bits - 1)
    end_val = (1 << max_bits) - 1
    
    best_c = None
    best_hr = -1
    
    for c in range(start_val, end_val + 1):
        if c % 2 == 0: continue
        if c % 3 != 2: continue
        if ((3*c + 1) % 4) != 2: continue
        
        if collatz_peak(c) == P:
            hr, total = reverse_tree_hr_depths((P, c, 7))[2][7]
            hr_val = hr / total if total > 0 else 0
            if hr_val > best_hr:
                best_hr = hr_val
                best_c = c
                
    return P, best_c

def main():
    peaks_to_test = [35, 37, 41, 48, 49]
    pool = multiprocessing.Pool(len(peaks_to_test))
    
    tasks = []
    print("Finding centers for requested peaks...")
    for P, best_c in pool.map(worker, peaks_to_test):
        if best_c is not None:
            tasks.append((P, best_c, 15))
            print(f"Found Center for Peak {P}: {best_c}")
        else:
            print(f"No center found for Peak {P}")

    print("\nPeak | Center | HR(d=7) | HR(d=10) | HR(d=15)")
    print("-" * 55)
    
    for target_peak, center, results in pool.imap_unordered(reverse_tree_hr_depths, tasks):
        hr7 = results[7][0] / results[7][1] if results[7][1] > 0 else 0
        hr10 = results[10][0] / results[10][1] if results[10][1] > 0 else 0
        hr15 = results[15][0] / results[15][1] if results[15][1] > 0 else 0
        
        print(f"{target_peak:4} | {center:10} | {hr7:7.4f} | {hr10:8.4f} | {hr15:8.4f}")

if __name__ == "__main__":
    main()
