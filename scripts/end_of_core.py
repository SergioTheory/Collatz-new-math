def get_end_of_core():
    x = 20152090995747160937051
    shifts = []
    for i in range(252):
        y = 3*x + 1
        a = (y & -y).bit_length() - 1
        shifts.append(a)
        x = y >> a
    return x, shifts

end_x, shifts = get_end_of_core()
print(f"End x: {end_x}")
print(f"Length of shifts: {len(shifts)}")

dips = []
for i, a in enumerate(shifts):
    if a >= 3:
        # Distance from the end of the 252-step vector
        dist = 251 - i
        dips.append(dist % 18)

from collections import Counter
print("Phase of dips mod 18:", Counter(dips))
