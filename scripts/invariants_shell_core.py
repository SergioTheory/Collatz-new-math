import csv, ast
from collections import defaultdict

rows = list(csv.DictReader(open("zone2_shifts_full.csv")))
for r in rows:
    r["bits"], r["d"], r["S"] = int(r["bits"]), int(r["d"]), int(r["S"])
    r["blocks"] = ast.literal_eval(r["blocks"])

core = [r for r in rows if r["n"] == "20152090995747160937051"][0]
cb = core["blocks"]
print("CORE: d=", core["d"], " S=", core["S"], " S/d=%.4f" % (core["S"]/core["d"]))

ok_suffix, by_ad = True, defaultdict(int)
for r in rows:
    ad = len(r["blocks"]) - len(cb)
    by_ad[ad] += 1
    ok_suffix &= (r["blocks"][ad:] == cb)   # хвост = ядро для ВСЕХ
print("all suffixes == core:", ok_suffix)
print("adapter depth histogram:", dict(sorted(by_ad.items())))

shell = [r for r in rows if len(r["blocks"]) == len(cb) + 7]
print("shell |S==bits+271:", all(r["S"] == r["bits"] + 271 for r in shell))
print("shell adapter sums S-334 vs bits-71:",
      sorted({(r["bits"], r["S"] - core["S"]) for r in shell})[:6])
