import sys

def collatz_step(n):
    n = 3 * n + 1
    shifts = 0
    while n % 2 == 0:
        n //= 2
        shifts += 1
    return n, shifts

def boolean_metrics(n):
    hw = 0
    blocks = 0
    temp = n
    prev_bit = 0
    while temp > 0:
        bit = temp & 1
        if bit == 1:
            hw += 1
            if prev_bit == 0:
                blocks += 1
        prev_bit = bit
        temp >>= 1
    return hw, blocks

def analyze_trajectory(n_start, name):
    print(f"--- Trajectory: {name} (Start: {n_start}) ---")
    n = n_start
    step = 0
    max_hw = 0
    max_blocks = 0
    hw_monotone = True
    blocks_monotone = True
    
    prev_hw, prev_blocks = boolean_metrics(n)
    
    while n > 1:
        n, _ = collatz_step(n)
        hw, blocks = boolean_metrics(n)
        
        if hw >= prev_hw: hw_monotone = False
        if blocks >= prev_blocks: blocks_monotone = False
            
        if hw > max_hw: max_hw = hw
        if blocks > max_blocks: max_blocks = blocks
        
        prev_hw, prev_blocks = hw, blocks
        step += 1
        if step > 10000: break
            
    print(f"Steps to 1: {step}")
    print(f"Max Hamming Weight: {max_hw}")
    print(f"Max 1-Blocks: {max_blocks}")
    print(f"Hamming Weight strictly monotone decreasing? {hw_monotone}")
    print(f"1-Blocks strictly monotone decreasing? {blocks_monotone}")
    print("")

if __name__ == '__main__':
    analyze_trajectory(27, "Number 27 (Miniature Zone 2)")
    analyze_trajectory(20152090995747160937051, "Zone 2 Record (75-bit peak)")
    analyze_trajectory(1980976057694848447, "Barina's Number")
    
