x = 20152090995747160937051
for _ in range(251):
    x = 3 * x + 1
    a = (x & -x).bit_length() - 1
    x >>= a

print(f"Odd peak: {x}")
print(f"Bits: {x.bit_length()}")
