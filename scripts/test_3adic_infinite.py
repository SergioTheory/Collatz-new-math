import sys
sys.set_int_max_str_digits(100000)

k = 883
M = 3**k
inv11 = pow(11, -1, M)
x = (-29 * inv11) % M

print("Original bit length:", x.bit_length())

curr = x
shifts = []
for i in range(2800):
    if curr % 3 == 1:
        a = 2
    else:
        a = 1
    
    y = (curr * (1 << a) - 1) // 3
    shifts.append(a)
    curr = y

print("Bit length after 2800 steps:", curr.bit_length())
print("Shifts (last 50):", shifts[-50:])
