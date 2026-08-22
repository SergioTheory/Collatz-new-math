import csv
import numpy as np
import matplotlib.pyplot as plt
import ast
import os

data_path = '../data/zone2_shifts_full.csv'
if not os.path.exists(data_path):
    print(f"Data not found at {data_path}")
    exit(1)

plt.figure(figsize=(10, 6))

count = 0
with open(data_path, 'r', encoding='utf8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if count >= 10: break
        b0 = float(row['bits'])
        blocks = ast.literal_eval(row['blocks'])
        
        bits = [b0]
        current_b = b0
        for a in blocks:
            current_b += np.log2(3) - a
            bits.append(current_b)
            
        plt.plot(range(len(bits)), bits, alpha=0.5, label=f'Zone 2: {int(b0)} bits' if count < 3 else "")
        count += 1

# Plot Barina's number
barina_blocks = [1, 1, 1, 3, 2, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 3, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 3, 1, 1, 1, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 3, 1, 1, 1, 1, 1, 1, 3, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 3, 2, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 3]

b0 = 71
bits = [b0]
current_b = b0
for a in barina_blocks:
    current_b += np.log2(3) - a
    bits.append(current_b)
plt.plot(range(len(bits)), bits, 'r--', linewidth=2, label='Barina: 71 bits')

plt.title('Collatz Trajectories: Zone 2 Confluence and Barina', fontsize=14)
plt.xlabel('Odd Steps (d)', fontsize=12)
plt.ylabel(r'Bit Size $\approx \log_2(x_k)$', fontsize=12)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig('../data/trajectory_plot.png', dpi=300)
print("Plot saved to ../data/trajectory_plot.png")
