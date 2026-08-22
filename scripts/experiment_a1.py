import ast

# 1. Load Zone 2 core shifts
with open(r'C:\Users\Admin\Documents\Collatz\data\zone2_shifts.csv', 'r') as f:
    lines = f.readlines()
# Parse the first data line
line = lines[1]
parts = line.strip().split(',\"')
shifts_str = parts[1].split('\"')[0]
zone2_shifts = ast.literal_eval(shifts_str)
# The core is the last 251 shifts
core_shifts = zone2_shifts[-251:]

# 2. Generate 2-adic shadow shifts for -29/11
N = 4000
inv11 = pow(11, -1, 1 << N)
x = (-29 * inv11) % (1 << N)
shadow_shifts = []
for _ in range(251):
    x = 3*x + 1
    a = (x & -x).bit_length() - 1
    x >>= a
    shadow_shifts.append(a)

# 3. Compare
mismatches = 0
diffs = []
for i in range(251):
    if core_shifts[i] != shadow_shifts[i]:
        mismatches += 1
        diffs.append((i, core_shifts[i], shadow_shifts[i]))

print(f"Total shifts compared: 251")
print(f"Mismatches: {mismatches}")
print(f"Mismatch percentage: {mismatches / 251 * 100:.2f}%")
print("Differences (index, core, shadow):")
for d in diffs:
    print(d)
