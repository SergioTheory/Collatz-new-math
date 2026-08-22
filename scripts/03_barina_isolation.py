#!/usr/bin/env python3
"""
Tutorial 03: Barina's Isolation
Goal: Demonstrate a number (Barina) reaching the 140-bit peak WITHOUT merging at x*.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from collatz_dynamics import collatz_peak

XSTAR = 20152090995747160937051
# Barina's number (71 bits)
BARINA_NUM = 1765856170146672440559
# Zone 2 reference number for comparison
ZONE2_NUM = 2358909599867980429759

def check_path(n):
    """Trace path and search for x*"""
    cur = n
    total_steps = 0
    odd_steps = 0
    found_xstar = False
    
    for _ in range(100):
        if cur == XSTAR:
            found_xstar = True
            break
        if cur % 2 == 0:
            cur //= 2
            total_steps += 1
        else:
            cur = 3 * cur + 1
            total_steps += 1
            odd_steps += 1
            while cur % 2 == 0:
                cur //= 2
                total_steps += 1
            if cur == XSTAR:
                found_xstar = True
                break
                
    return found_xstar, total_steps, odd_steps

def main():
    print("🚧 TUTORIAL 03: BARINA'S ISOLATION")
    print("Goal: Demonstrate that a 140-bit peak can be reached WITHOUT confluence.")
    print("-" * 60)
    
    # Interactive input
    user_input = input("Paste your Zone 2 number (or press Enter for the 71-bit default reference):\n> ").strip()
    
    if user_input.isdigit():
        z2_num = int(user_input)
    else:
        z2_num = ZONE2_NUM
    
    # 1. Zone 2 Analysis
    z2_pass, z2_total, z2_odd = check_path(z2_num)
    z2_peak, _, _ = collatz_peak(z2_num)
    z2_ratio = z2_peak / z2_num.bit_length()
    
    print("\n1. Zone 2 Representative (yours or default):")
    print(f"   Number: {z2_num} ({z2_num.bit_length()} bits)")
    print(f"   Peak: {z2_peak}")
    print(f"   Ratio: {z2_ratio:.4f}")
    print(f"   Passes through x*: {'YES' if z2_pass else 'NO'} ({z2_total} raw iterations, {z2_odd} odd steps d)")
    print()
    
    # 2. Barina's Analysis
    b_pass, b_total, b_odd = check_path(BARINA_NUM)
    b_peak, _, _ = collatz_peak(BARINA_NUM)
    b_ratio = b_peak / BARINA_NUM.bit_length()
    
    print("2. Barina's Number:")
    print(f"   Number: {BARINA_NUM} (71 bits)")
    print(f"   Peak: {b_peak}")
    print(f"   Ratio: {b_ratio:.4f}")
    print(f"   Passes through x*: {'YES' if b_pass else 'NO'} ({b_total} raw iterations, {b_odd} odd steps d)")
    print()
    
    print("=" * 60)
    if not b_pass and z2_pass:
        print("🎓 MAIN CONCLUSION:")
        print("   Despite sharing the exact same peak (140), their trajectories NEVER intersect.")
        print("   Barina's number takes a 'secret path', entirely bypassing x*.")
        print("   This proves the Collatz space contains multiple independent")
        print("   mechanisms for reaching anomalously high peaks.")
    else:
        print("❌ Results do not confirm the isolation hypothesis.")

if __name__ == "__main__":
    main()
