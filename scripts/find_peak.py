x = 20152090995747160937051
orig_x = x
p = x
while True:
    if x % 2 == 0:
        x //= 2
    else:
        x = 3 * x + 1
    if x > p:
        p = x
    if x < orig_x:
        break

print(f"Peak: {p}")
print(f"Peak bits: {p.bit_length()}")
