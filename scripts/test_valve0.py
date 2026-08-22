import sys

K = 87
M = 3**K
inv11 = pow(11, -1, M)
X0 = (-29 * inv11) % M
if X0 % 2 == 0:
    X0 += M

print(f"X0: {X0}")
print(f"X0 bits: {X0.bit_length()}")

curr = X0
rev_path = [curr]
shifts = []

# Greedy reverse Collatz
for i in range(300):
    if curr % 3 == 0:
        print(f"Error: curr is divisible by 3 at step {i}")
        break
        
    if curr % 3 == 1:
        a = 2
    else:
        a = 1
        
    curr = (curr * (1 << a) - 1) // 3
    shifts.append(a)
    rev_path.append(curr)
    
    if 71 <= curr.bit_length() <= 80:
        break

n = curr
print(f"Found n: {n}")
print(f"n bits: {n.bit_length()}")
print(f"Steps taken: {len(shifts)}")

# Full forward simulation on n
x_star = 20152090995747160937051
passed_x_star = False
peak = n.bit_length()

fwd_curr = n
fwd_shifts = []

if fwd_curr == x_star:
    passed_x_star = True

while fwd_curr > 1:
    y = 3 * fwd_curr + 1
    a = (y & -y).bit_length() - 1
    fwd_shifts.append(a)
    fwd_curr = y >> a
    
    if fwd_curr.bit_length() > peak:
        peak = fwd_curr.bit_length()
        
    if fwd_curr == x_star:
        passed_x_star = True

print(f"Peak of n: {peak}")
print(f"Passed x_star: {passed_x_star}")

# x_star shifts
x_curr = x_star
x_star_shifts = []
while x_curr > 1:
    y = 3 * x_curr + 1
    a = (y & -y).bit_length() - 1
    x_star_shifts.append(a)
    x_curr = y >> a

match_len = 0
for i in range(1, min(len(fwd_shifts), len(x_star_shifts)) + 1):
    if fwd_shifts[-i] == x_star_shifts[-i]:
        match_len += 1
    else:
        break
        
print(f"Common suffix length: {match_len}")
print(f"Total x_star shifts: {len(x_star_shifts)}")
print(f"Total n shifts: {len(fwd_shifts)}")

# Check peak of X0 itself
X0_peak = X0.bit_length()
X0_curr = X0
X0_shifts = []
while X0_curr > 1:
    y = 3 * X0_curr + 1
    a = (y & -y).bit_length() - 1
    X0_shifts.append(a)
    X0_curr = y >> a
    if X0_curr.bit_length() > X0_peak:
        X0_peak = X0_curr.bit_length()

print(f"Peak of X0: {X0_peak}")
