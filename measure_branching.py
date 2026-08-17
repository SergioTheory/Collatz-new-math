import sys
import os

# Add src to path to import crt_solver
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
import crt_solver

def reverse_tree_level_sizes(root, max_depth, bit_cap):
    # Returns a list of sizes: [N(0), N(1), N(2), ...]
    current_level = {root}
    sizes = [len(current_level)]
    
    for _ in range(max_depth):
        next_level = set()
        for node in current_level:
            # child 1: even step (previous number was 2 * node)
            c1 = node * 2
            if c1.bit_length() <= bit_cap:
                next_level.add(c1)
                
            # child 2: odd step (previous number was (node - 1) / 3)
            # must be an integer, must be odd, must be > 1
            if (node - 1) % 3 == 0:
                c2 = (node - 1) // 3
                if c2 % 2 != 0 and c2 > 1:
                    if c2.bit_length() <= bit_cap:
                        next_level.add(c2)
        
        sizes.append(len(next_level))
        current_level = next_level
        if not next_level:
            break
            
    return sizes

def get_x_star():
    # Construct x* using Z2_CORE pattern
    # It has length 72 bits
    return crt_solver.number_from_parity(crt_solver.Z2_CORE)

def analyze_center(name, center_val, max_depth=10, cap_offset=15):
    center_bits = center_val.bit_length()
    cap = center_bits + cap_offset
    print(f"\n--- Analyzing {name} (Bits: {center_bits}) ---")
    print(f"Using Cap = {cap} bits (+{cap_offset})")
    
    sizes = reverse_tree_level_sizes(center_val, max_depth, cap)
    print("Depth | Nodes | b(k) (N_k / N_{k-1})")
    print("-" * 35)
    
    for k in range(len(sizes)):
        if k == 0:
            print(f"{k:5} | {sizes[k]:5} | {'-':>15}")
        else:
            b_k = sizes[k] / sizes[k-1] if sizes[k-1] > 0 else 0
            print(f"{k:5} | {sizes[k]:5} | {b_k:15.4f}")

if __name__ == "__main__":
    centers = [
        ("Peak 14 (121)", 121),
        ("Peak 50 (1396693151)", 1396693151),
        ("Peak 140 (x*)", get_x_star())
    ]
    
    for name, val in centers:
        analyze_center(name, val, max_depth=15, cap_offset=15)
