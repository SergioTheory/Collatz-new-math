x_star = 20152090995747160937051
x0_2 = (-29 * pow(11, -1, 2**100)) % 2**100
diff = x_star - x0_2
count = 0
while diff % 2 == 0 and diff != 0:
    count += 1
    diff //= 2
print('Matching 2-adic digits:', count)
