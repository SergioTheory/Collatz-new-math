import ast
import csv

def load_true_path():
    with open("zone2_shifts_full.csv", "r") as f:
        r = next(csv.DictReader(f))
        v = ast.literal_eval(r["blocks"])
    
    # 252 shifts in total
    peak_val = 329409787129088108212379710537829645932061
    # The actual odd number right before the peak is peak_val >> v[-1]
    # Wait, peak_val in my previous run was the max ODD number.
    # The true x* is 20152090995747160937051
    # Let's just generate the true path forwards from x*
    x_star = 20152090995747160937051
    path = [x_star]
    shifts = []
    curr = x_star
    for a in v:
        curr = (curr * 3 + 1) >> a
        path.append(curr)
        shifts.append(a)
    
    # path has 253 elements: path[0] = x_star, ..., path[252] = max odd number
    # shifts has 252 elements: shifts[0] = a_1, ..., shifts[251] = a_{252}
    
    # Reverse path:
    rev_path = path[::-1] # rev_path[0] = peak odd, ..., rev_path[252] = x_star
    rev_shifts = shifts[::-1] # rev_shifts[0] = last forward shift, ..., rev_shifts[251] = first forward shift
    
    return rev_path, rev_shifts

rev_path, rev_shifts = load_true_path()
for i in range(10):
    print(f"k={i}, x={rev_path[i]}, a={rev_shifts[i]}")
