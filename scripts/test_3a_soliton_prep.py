K = 88
M = 3**K
inv11 = pow(11, -1, M)
X0 = (-29 * inv11) % M
if X0 % 2 == 0:
    X0 += M

curr = X0
S = 0
for i in range(300):
    if curr % 3 == 0:
        break
    if curr % 3 == 1:
        a = 2
    else:
        a = 1
    curr = (curr * (1 << a) - 1) // 3
    S += a
print("n:", curr)
print("S:", S)
print("k:", i)
