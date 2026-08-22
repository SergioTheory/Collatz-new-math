import sys
import os
import json
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from crt_solver import collatz_peak
from collatz_peak import analyze_to_peak

X_STAR = 20152090995747160937051
MAX_BITS = 90
A_MAX = 15
MAX_DEPTH = 7

def find_predecessors(m: int) -> list[int]:
    preds = []
    power2 = 1
    for a in range(1, A_MAX + 1):
        power2 <<= 1
        val = m * power2 - 1
        if val % 3 != 0:
            continue
        n = val // 3
        if n <= 0 or n % 2 == 0:
            continue
        if n.bit_length() > MAX_BITS:
            continue
        preds.append(n)
    return preds

def main():
    print(f"Building reverse tree from {X_STAR} to depth {MAX_DEPTH}...")
    tree = {0: {X_STAR}}
    all_nodes = {X_STAR}

    for depth in range(MAX_DEPTH):
        current = tree[depth]
        nxt = set()
        for m in current:
            for n in find_predecessors(m):
                if n not in all_nodes:
                    all_nodes.add(n)
                    nxt.add(n)
        tree[depth + 1] = nxt
        print(f"Depth {depth}->{depth+1}: {len(current)} -> {len(nxt)} nodes")

    print("Filtering 71-87 bits and peak=140...")
    zone2_nodes = []
    for depth in range(MAX_DEPTH + 1):
        for n in tree[depth]:
            bits = n.bit_length()
            if 71 <= bits <= 87:
                peak, _, _ = collatz_peak(n, max_steps=500_000)
                if peak == 140:
                    zone2_nodes.append(n)

    print(f"Found {len(zone2_nodes)} classic Zone 2 numbers.")
    
    # Save to expand_913.json
    json_data = [{"n": str(x)} for x in zone2_nodes]
    json_path = os.path.join(os.path.dirname(__file__), 'expand_913.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"Saved to {json_path}")

    # Directly build zone2_verified.csv
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'zone2_verified.csv')
    
    # Sort by bit length
    zone2_nodes.sort(key=lambda x: x.bit_length())
    
    results = []
    print("Analyzing each number for CSV export...")
    for i, n in enumerate(zone2_nodes):
        stats = analyze_to_peak(n)
        results.append({
            "Number": str(n),
            "Input_Bits": n.bit_length(),
            "Peak_Bits": stats["peak_bits"],
            "d": stats["d"],
            "S": stats["S"],
            "S_over_d": f"{stats['S_over_d']:.4f}"
        })
        if (i+1) % 100 == 0:
            print(f"  processed {i+1}/{len(zone2_nodes)}...")

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Number", "Input_Bits", "Peak_Bits", "d", "S", "S_over_d"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Successfully exported 913 elements to {csv_path}")

if __name__ == '__main__':
    main()
