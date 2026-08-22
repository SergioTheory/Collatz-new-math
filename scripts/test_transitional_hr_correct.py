import multiprocessing
from collections import deque

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

def main():
    tasks = [
        (35, 26658983, 15),
        (37, 67625867, 15),
        (41, 37748015, 15)
    ]
    
    print("Peak | Center     | HR(d=7) | HR(d=10) | HR(d=15)")
    print("-" * 55)
    
    pool = multiprocessing.Pool(len(tasks))
    for target_peak, center, results in pool.imap_unordered(reverse_tree_hr_depths, tasks):
        hr7 = results[7][0] / results[7][1] if results[7][1] > 0 else 0
        hr10 = results[10][0] / results[10][1] if results[10][1] > 0 else 0
        hr15 = results[15][0] / results[15][1] if results[15][1] > 0 else 0
        
        print(f"{target_peak:4} | {center:10} | {hr7:7.4f} | {hr10:8.4f} | {hr15:8.4f}")

if __name__ == "__main__":
    main()
