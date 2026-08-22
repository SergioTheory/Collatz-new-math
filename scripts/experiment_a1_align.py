import ast

# 1. Load Zone 2 core shifts
with open(r'C:\Users\Admin\Documents\Collatz\data\zone2_shifts.csv', 'r') as f:
    lines = f.readlines()
line = lines[1]
parts = line.strip().split(',\"')
shifts_str = parts[1].split('\"')[0]
zone2_shifts = ast.literal_eval(shifts_str)
core_shifts = zone2_shifts[-251:]

# 2. Compare against shifted infinite pattern (1,1,2)
pattern = [1, 1, 2]
best_offset = 0
min_mismatches = len(core_shifts)

for offset in range(3):
    mismatches = 0
    diffs = []
    for i in range(251):
        expected = pattern[(i + offset) % 3]
        if core_shifts[i] != expected:
            mismatches += 1
            diffs.append((i, core_shifts[i], expected))
    if mismatches < min_mismatches:
        min_mismatches = mismatches
        best_offset = offset
        best_diffs = diffs

print(f"Total shifts compared: 251")
print(f"Best offset (0=starts with 1,1,2; 1=starts with 1,2,1; 2=starts with 2,1,1): {best_offset}")
print(f"Mismatches: {min_mismatches}")
print(f"Mismatch percentage: {min_mismatches / 251 * 100:.2f}%")
print("First 10 differences (index, actual core, expected pattern):")
for d in best_diffs[:10]:
    print(d)
