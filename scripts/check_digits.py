peak = 329409787129088108212379710537829645932061
x0 = (-29 * pow(11, -1, 3**100)) % 3**100
diff = (peak - x0)
count = 0
while diff % 3 == 0 and diff != 0:
    count += 1
    diff //= 3
print('Matching digits:', count)
