import csv, ast, math
from collections import defaultdict, Counter

CORE_LEN = 251
rows = list(csv.DictReader(open("zone2_shifts_full.csv")))
for r in rows:
    r["bits"] = int(r["bits"]); r["blocks"] = ast.literal_eval(r["blocks"])

# (i) тождественность ядра
core = rows[0]["blocks"][-CORE_LEN:]
assert all(r["blocks"][-CORE_LEN:] == core for r in rows)
print("CORE verified: len=251, S_core =", sum(core))

by_depth = defaultdict(list)
for r in rows:
    ad = r["blocks"][:-CORE_LEN]
    by_depth[len(ad)].append((int(r["n"]), r["bits"], ad))

# (ii)-(iv) послойная статистика адаптеров
for d in sorted(by_depth):
    items = by_depth[d]
    seqs = Counter(tuple(ad) for _, _, ad in items)
    diffs = Counter(sum(ad) - b for _, b, ad in items)
    print(f"depth={d} inputs={len(items)} distinct_adapters={len(seqs)} "
          f"S-bits: {dict(sorted(diffs.items())[:4])}")

# (v) энтропийная скорость: рост входов с битностью на depth=7
cnt = Counter(b for _, b, _ in by_depth[7])
bs = sorted(cnt)
slope = (math.log2(cnt[bs[-1]]) - math.log2(cnt[bs[0]])) / (bs[-1] - bs[0])
print(f"depth7 growth slope = {slope:.3f} bit^-1 (ожидали ~0.486)")

# (vi) детерминизм автомата: адаптер как функция хвоста (младших бит)
def lowbits(n, t): return n & ((1 << t) - 1)
ads = defaultdict(list)
for n, b, ad in by_depth[7]:
    ads[tuple(ad)].append(n)
# различимы ли разные адаптеры по младшим битам?
worst = 0
keys = list(ads)
for i in range(len(keys)):
    for j in range(i + 1, min(i + 40, len(keys))):
        for x in ads[keys[i]][:2]:
            for y in ads[keys[j]][:2]:
                t = 0
                while lowbits(x, t) == lowbits(y, t): t += 1
                worst = max(worst, t)
print("max common low-bit prefix between different adapters =", worst)
