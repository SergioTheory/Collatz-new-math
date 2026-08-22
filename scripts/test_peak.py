K = 88
M = 3**K
X0 = (-29 * pow(11, -1, M)) % M
if X0 % 2 == 0: X0 += M

curr = X0
max_val = X0
for i in range(88):
    if curr % 3 == 1: a = 2
    else: a = 1
    curr = (curr * (1 << a) - 1) // 3
    if curr > max_val: max_val = curr

print("X0:", X0)
print("max_val:", max_val)
print("max_val / X0:", max_val / X0)
