import json
with open("expand_913.json", "r") as f:
    data = json.load(f)

def get_peak_odd(n, target_peak):
    x = int(n)
    best = 0
    best_x = x
    for i in range(5000):
        if x % 2 == 0:
            x //= 2
            continue
        y = 3 * x + 1
        a = (y & -y).bit_length() - 1
        if y > best:
            best = y
            best_x = x
        x = y >> a
        if best.bit_length() - x.bit_length() > 40:
            break
        if best.bit_length() == target_peak and x.bit_length() < best.bit_length() - 10:
            break
    return best_x

n = int(data[0]['n'])
peak_odd = get_peak_odd(n, 140)
print(f"Seed n: {n}")
print(f"Peak odd: {peak_odd}")
print(f"Peak odd bits: {peak_odd.bit_length()}")
