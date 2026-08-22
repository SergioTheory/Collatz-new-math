import ast
import csv

with open("zone2_shifts_full.csv", "r") as f:
    r = next(csv.DictReader(f))
    v = ast.literal_eval(r["blocks"])
    
peak_val = 329409787129088108212379710537829645932061

# The peak shift is v[-1] = 3.
x = peak_val >> v[-1]

for k in range(252):
    # the shift applied going forward was v[251 - k]
    a = v[251 - k]
    
    num = (x << a) - 1
    if num % 3 != 0:
        print(f"Error at k={k}, a={a}, num%3 != 0")
        break
    y = num // 3
    
    # check grammar
    phase18 = k % 18
    if k < 90:
        if a >= 3 and phase18 not in (0, 5, 9):
            print(f"Grammar rejected true path at k={k}, a={a}, phase18={phase18}")
            break
            
    x = y
    
print(f"Survives to k={k}")

