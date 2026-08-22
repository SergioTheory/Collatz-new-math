import csv
from collections import defaultdict
import multiprocessing
import sys

def load_centers():
    files = ['confluence_census.csv', 'targeted_31_50.csv', 'targeted_41_50.csv', 'targeted_missing.csv']
    centers = {}
    for f in files:
        try:
            with open(f, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    c = int(row['center'])
                    p = int(row.get('peak', 0))
                    if p > 0:
                        if p not in centers:
                            centers[p] = set()
                        centers[p].add(c)
        except Exception as e:
            pass
    return centers

def collatz_peak_with_path(n):
    pb = n.bit_length()
    cur = n
    path = {n}
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
        else:
            cur = cur // 2
        path.add(cur)
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb, path

def worker(args):
    start, end, centers_dict = args
    results = defaultdict(lambda: {"center": 0, "soliton": 0})
    for n in range(start, end, 2):
        P, path = collatz_peak_with_path(n)
        if P in centers_dict:
            # Check if path hits ANY of the known centers for this peak
            hit = any(c in path for c in centers_dict[P])
            if hit:
                results[P]["center"] += 1
            else:
                results[P]["soliton"] += 1
    return dict(results)

def main():
    centers = load_centers()
    # Ensure peak 14 has both 121 and 719 if they exist
    print("Centers loaded:")
    for p in sorted(centers.keys()):
        if p <= 30:
            print(f"Peak {p}: {centers[p]}")
            
    # Exhaustive search up to 2^20
    MAX_N = 1 << 20
    print(f"\nRunning exhaustive search up to {MAX_N} (2^20)...")
    
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    chunk_size = 50000
    ranges = []
    for i in range(3, MAX_N, chunk_size):
        end = min(i + chunk_size, MAX_N)
        if end % 2 == 0: end -= 1
        ranges.append((i, end, centers))
        
    final_results = defaultdict(lambda: {"center": 0, "soliton": 0})
    
    for chunk_res in pool.imap_unordered(worker, ranges):
        for P, counts in chunk_res.items():
            final_results[P]["center"] += counts["center"]
            final_results[P]["soliton"] += counts["soliton"]
            
    print("\n--- Soliton Census Results ---")
    print(f"{'Peak':>5} | {'Center Hits':>15} | {'Solitons (Misses)':>20} | {'Soliton %':>10}")
    print("-" * 60)
    for p in sorted(final_results.keys()):
        if p <= 30:
            hits = final_results[p]["center"]
            misses = final_results[p]["soliton"]
            total = hits + misses
            pct = (misses / total * 100) if total > 0 else 0
            print(f"{p:5} | {hits:15} | {misses:20} | {pct:9.2f}%")

if __name__ == "__main__":
    main()
