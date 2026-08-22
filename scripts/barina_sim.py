n = 1765856170146672440559
d = 0
S = 0
cur = n
while d < 213:
    if cur % 2 != 0:
        cur = cur * 3 + 1
    else:
        cur //= 2
        S += 1
        if cur % 2 != 0:
            d += 1
print(f"Barina d={d}, S={S}")
