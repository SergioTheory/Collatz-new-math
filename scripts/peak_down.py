import csv, ast
from crt_solver import number_from_parity, collatz_peak

with open('zone2_shifts.csv', 'r') as f:
    rows = list(csv.DictReader(f))
vec = ast.literal_eval(rows[0]['blocks'])
tail = vec[7:]

def tail_to_parity(t):
    return ''.join('1' + '0' * s for s in t)

print("cut_len\tbits\tpeak\tratio\td")
for cut in range(50, 110, 5):
    short = tail[-cut:]
    parity = tail_to_parity(short)
    n = number_from_parity(parity)
    if n is None or n <= 0:
        print(f"{cut}\t-\t-\t-")
        continue
    bits = n.bit_length()
    peak, steps, conv = collatz_peak(n)
    marker = " <-- BREAKS" if peak < 140 else ""
    print(f"{cut}\t{bits}\t{peak}\t{peak/bits:.4f}\t{cut}{marker}")