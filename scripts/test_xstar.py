x_star = 20152090995747160937051
curr = x_star
peak = curr.bit_length()
shifts = []
while curr > 1:
    if curr % 2 == 0:
        curr //= 2
        continue
    y = 3 * curr + 1
    a = (y & -y).bit_length() - 1
    shifts.append(a)
    curr = y >> a
    if curr.bit_length() > peak:
        peak = curr.bit_length()

print("Peak:", peak)
print("Max shift:", max(shifts))
print("Shifts:", shifts[:30])
