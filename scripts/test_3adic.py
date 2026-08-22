import sys
sys.set_int_max_str_digits(10000)
# Compute x = -29 / 11 mod 3^1000
k = 1000
M = 3**k
# Modular inverse of 11 mod 3^1000
inv11 = pow(11, -1, M)
x = (-29 * inv11) % M

# Now let's trace the reverse Collatz from x
curr = x
shifts = []
for i in range(30):
    if curr % 3 == 1:
        a = 2
    else:
        a = 1
    
    y = (curr * (1 << a) - 1) // 3
    shifts.append(a)
    curr = y % (3**(k - i - 1)) # The valid 3-adic precision drops by 1 per step

print("Shifts:", shifts)
print("x in decimal (first 50 digits):", str(x)[:50])
print("x bit length:", x.bit_length())
