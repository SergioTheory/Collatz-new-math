import csv
import ast
from crt_solver import number_from_parity, collatz_peak

# Загружаем хвост из zone2_shifts.csv (как в recover_from_tail.py)
with open('zone2_shifts.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
vec = ast.literal_eval(rows[0]['blocks'])
tail = vec[7:]  # хвост начинается с позиции 7
print(f"Длина хвоста: {len(tail)}")

def tail_to_parity(t):
    return ''.join('1' + '0' * s for s in t)

print("cut_len\tbits\tpeak\tratio")
for cut in [200, 150, 100, 50, 30, 20, 10]:
    short = tail[-cut:] if cut <= len(tail) else tail
    parity = tail_to_parity(short)
    n = number_from_parity(parity)
    if n is None:
        print(f"{cut}\t-\t-\t-")
        continue
    bits = n.bit_length()
    peak, steps, conv = collatz_peak(n)
    print(f"{cut}\t{bits}\t{peak}\t{peak/bits:.4f}")