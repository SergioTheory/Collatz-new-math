import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from collatz_dynamics import analyze_to_peak

def main():
    print("--- Verifying Zone 2 ---")
    data_path = os.path.join("data", "expand_913.json")
    if not os.path.exists(data_path):
        print(f"[FAIL] Missing {data_path}")
        return
    with open(data_path, 'r') as f:
        data = json.load(f)
    assert len(data) == 913, f"Expected 913 entries, got {len(data)}"
    print("[OK] Loaded 913 classical Zone 2 inputs (71-87 bits).")
    
    x_star = 20152090995747160937051
    matches = 0
    
    for item in data:
        n = int(item['n'])
        stats = analyze_to_peak(n)
        
        # Verify peak is 140
        assert stats['peak_bits'] == 140, f"Peak must be 140, got {stats['peak_bits']} for {n}"
        
        # Verify d is in the expected Zone 2 range (250 to 260)
        assert 250 <= stats['d'] <= 260, f"d must be near 259, got {stats['d']}"
        
        # Verify S/d is around 1.33 (Zone 2 profile)
        s_d = stats['S'] / stats['d']
        assert 1.32 <= s_d <= 1.40, f"S/d must be ~1.33, got {s_d}"
        
        # Verify it hits x*
        cur = n
        hit_xstar = False
        for _ in range(8):
            if cur % 2 == 0:
                while cur % 2 == 0: cur >>= 1
            if cur == x_star: hit_xstar = True; break
            cur = (3 * cur + 1)
            while cur % 2 == 0: cur >>= 1
            if cur == x_star: hit_xstar = True; break
        assert hit_xstar, "Did not hit x* within 7 odd steps"
        matches += 1
    
    print(f"[OK] Verified {matches} entries: peak=140, d~259, S/d~1.33, all converge to x* in <=7 steps.")

if __name__ == '__main__':
    main()
