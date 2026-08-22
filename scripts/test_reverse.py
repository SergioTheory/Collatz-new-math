import ast
import stage4a_instanton_validate as s4

x = 20152090995747160937051
fwd_shifts = []
for _ in range(251):
    x = 3 * x + 1
    a = (x & -x).bit_length() - 1
    x >>= a
    fwd_shifts.append(a)

peak = x

bwd_shifts = fwd_shifts[::-1]
y = peak
for a in bwd_shifts:
    y = ((y << a) - 1) // 3

print("Original x*:", 20152090995747160937051)
print("Recovered y:", y)
print("Match:", y == 20152090995747160937051)

# Now check if the reversed chunks are in the reversed grammar
blocks, _, _ = s4.load_grammar('zone2_shifts.csv')
reversed_core = fwd_shifts[::-1]
test_blocks = []
for i in range(len(reversed_core) - 6 + 1):
    test_blocks.append(tuple(reversed_core[i:i+6]))

print("Number of test blocks from reversed core:", len(set(test_blocks)))
print("Number of them in our forward blocks list:", len([b for b in set(test_blocks) if b in blocks]))
