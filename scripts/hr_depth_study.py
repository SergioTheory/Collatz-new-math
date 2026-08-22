import sys

def get_path_max(start_node, target_node):
    x = start_node
    max_val = x
    while x != target_node and x > 1:
        if x % 2 == 1: x = 3 * x + 1
        else: x //= 2
        if x > max_val: max_val = x
    return max_val

def reverse_tree_bfs(target, depth, target_peak_bits):
    current_level = {target}
    for _ in range(depth):
        next_level = set()
        for x in current_level:
            a = 1
            while True:
                num = (1 << a) * x - 1
                if num % 3 == 0:
                    y = num // 3
                    if y > 1 and y % 2 != 0 and y % 3 != 0: 
                        # Only add y if it's within a reasonable bit length
                        if y.bit_length() <= target_peak_bits + 5:
                            next_level.add(y)
                a += 1
                if a > 40: break
        current_level = next_level
    return current_level

def calculate_hr(center, target_peak_bits, depths):
    results = {}
    for d in depths:
        nodes = reverse_tree_bfs(center, d, target_peak_bits)
        
        # Method A: bits(y) < P
        nodes_A = [y for y in nodes if y.bit_length() < target_peak_bits]
        
        # Method B: Window [P/2, P)
        lower_bound = max(1, target_peak_bits // 2)
        nodes_B = [y for y in nodes if lower_bound <= y.bit_length() < target_peak_bits]
        
        hits_A = sum(1 for y in nodes_A if get_path_max(y, center).bit_length() <= target_peak_bits)
        hits_B = sum(1 for y in nodes_B if get_path_max(y, center).bit_length() <= target_peak_bits)
                
        results[d] = {
            "A_total": len(nodes_A), "A_hits": hits_A, "A_hr": hits_A / len(nodes_A) if nodes_A else 0.0,
            "B_total": len(nodes_B), "B_hits": hits_B, "B_hr": hits_B / len(nodes_B) if nodes_B else 0.0
        }
    return results

print("Center 121 (Peak 14 bits):")
res_121 = calculate_hr(121, 14, range(3, 9))
for d in sorted(res_121.keys()):
    r = res_121[d]
    print(f"Depth {d}: Method A HR={r['A_hr']:.3f} ({r['A_hits']}/{r['A_total']}) | Method B HR={r['B_hr']:.3f} ({r['B_hits']}/{r['B_total']})")

print("\nCenter x* (Peak 140 bits):")
x_star = 20152090995747160937051
res_xstar = calculate_hr(x_star, 140, range(3, 9))
for d in sorted(res_xstar.keys()):
    r = res_xstar[d]
    print(f"Depth {d}: Method A HR={r['A_hr']:.3f} ({r['A_hits']}/{r['A_total']}) | Method B HR={r['B_hr']:.3f} ({r['B_hits']}/{r['B_total']})")
