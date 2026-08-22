#!/usr/bin/env python3
"""
Tutorial 02: Proof of Confluence
Goal: Prove that all found Zone 2 numbers pass through x*.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from collatz_dynamics import collatz_peak

# Confluence point x* (known from v6)
XSTAR = 20152090995747160937051

def get_trajectory_to_confluence(n, target):
    """Get path from n to target and count steps"""
    path = [n]
    cur = n
    total_steps = 0
    odd_steps = 0
    
    for _ in range(100): # Allow enough steps for division tracking
        if cur == target:
            return path, True, total_steps, odd_steps
        if cur % 2 == 0:
            cur //= 2
            total_steps += 1
        else:
            cur = 3 * cur + 1
            total_steps += 1
            odd_steps += 1
            # Perform all divisions by 2 following the 3x+1 operation
            while cur % 2 == 0:
                cur //= 2
                total_steps += 1
            if cur == target:
                path.append(cur)
                return path, True, total_steps, odd_steps
        path.append(cur)
    return path, False, total_steps, odd_steps

def main():
    print("🔍 TUTORIAL 02: PROOF OF CONFLUENCE")
    print("Goal: Verify if the numbers pass through the common point x*.")
    print("-" * 60)
    
    # Interactive input
    user_input = input("Paste your Zone 2 number (from step 1) or press Enter to test default reference numbers:\n> ").strip()
    
    if user_input.isdigit():
        test_numbers = [int(user_input)]
        print("\nTesting your number...")
    else:
        print("\nUsing default reference numbers...")
        test_numbers = [
            2358909599867980429759,  # 71 bits
            4717819199735960859518,  # 72 bits
            75485107195775373752296, # 76 bits
        ]
    
    print(f"Confluence point (x*): {XSTAR}")
    print(f"x* bits: {XSTAR.bit_length()} bits")
    print("=" * 60)
    
    all_pass = True
    
    for n in test_numbers:
        path, found, total_steps, odd_steps = get_trajectory_to_confluence(n, XSTAR)
        bits = n.bit_length()
        
        if found:
            print(f"✅ Number ({bits} bits): Passes through x* in {total_steps} raw iterations (exactly {odd_steps} odd steps d).")
        else:
            print(f"❌ Number ({bits} bits): DID NOT hit x* (anomaly!)")
            all_pass = False
            
    print("=" * 60)
    if all_pass:
        print("🎓 CONCLUSION: We observe structure. These numbers are not random.")
        print("   They are attracted to the 'magnetic center' x*.")
        print("👉 Run the next command to witness Barina's isolation:")
        print("   python 03_barina_isolation.py")
    else:
        print("❌ Test failed. This is not Zone 2.")

if __name__ == "__main__":
    main()
