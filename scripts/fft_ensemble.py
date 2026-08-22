import csv, ast
import numpy as np

vecs = [ast.literal_eval(r["blocks"])
        for r in csv.DictReader(open("zone2_shifts_full.csv"))]

N = 1024
acc = None
for v in vecs:
    v = np.asarray(v, float); v -= v.mean()
    A = np.abs(np.fft.rfft(v, N))
    acc = A if acc is None else acc + A
freqs = np.fft.rfftfreq(N)
mean = acc / len(vecs)

for f, a in sorted(zip(freqs, mean), key=lambda t: -t[1])[:12]:
    if f > 0: print(f"T={1/f:6.2f}  f={f:.3f}  amp={a:.2f}")
