import numpy as np
import json

d = json.load(open("e6_results.json"))
res = d["results"]
ns = np.array([r["n"] for r in res])
cc = np.array([r["c_cert"] for r in res])
ss = np.array([r["s*"] for r in res])
bb = ss / ns

print("=== table ===")
for r in res:
    n = r["n"]
    if n in (50, 60, 70, 80, 90, 100, 120, 150, 180, 200, 220, 250, 280, 300):
        print(f"n={n:>4} c_cert={r['c_cert']:.6f} s*={r['s*']:>4} s*/n={r['s*/n']:.4f}")

print("\n=== fit c(n)=c_inf + a/n, windows ===")
for w1, w2 in [(100, 300), (150, 300), (200, 300), (250, 300)]:
    m = (ns >= w1) & (ns <= w2)
    X = np.vstack([1 / ns[m], np.ones(ns[m].size)]).T
    coef = np.linalg.lstsq(X, cc[m], rcond=None)[0]
    pred = X @ coef
    rm = np.sqrt(np.mean((cc[m] - pred) ** 2))
    print(f"n in [{w1},{w2}]: c_inf={coef[1]:.5f} a={coef[0]:.3f} rmse={rm:.2e}")

print("\n=== fit c(n)=c_inf + a/n^alpha ===")
def fitc(alpha, w1, w2):
    m = (ns >= w1) & (ns <= w2)
    X = np.vstack([ns[m] ** (-alpha), np.ones(ns[m].size)]).T
    coef = np.linalg.lstsq(X, cc[m], rcond=None)[0]
    pred = X @ coef
    return coef[1], coef[0], np.sqrt(np.mean((cc[m] - pred) ** 2))

for w1, w2 in [(100, 300), (150, 300), (200, 300)]:
    print(f"n in [{w1},{w2}]:")
    for alpha in (0.5, 0.8, 0.9, 1.0, 1.2, 1.5):
        ci, a, rm = fitc(alpha, w1, w2)
        print(f"  alpha={alpha}: c_inf={ci:.5f} a={a:.3f} rmse={rm:.2e}")

print("\n=== fit beta(n)=beta_inf + b/n ===")
for w1, w2 in [(100, 300), (150, 300), (200, 300), (250, 300)]:
    m = (ns >= w1) & (ns <= w2)
    X = np.vstack([1 / ns[m], np.ones(ns[m].size)]).T
    coef = np.linalg.lstsq(X, bb[m], rcond=None)[0]
    print(f"n in [{w1},{w2}]: beta_inf={coef[1]:.5f} b={coef[0]:.3f}")

print(f"\nlog2(3)={np.log2(3):.6f}  4/3={4/3:.6f}")

lp = d["landscape"]
print("\n=== landscape minima ===")
for k in sorted(lp, key=int):
    n = int(k)
    if n < 100:
        continue
    dd = {float(ak): av for ak, av in lp[k].items()}
    bm = min(dd, key=dd.get)
    fm = dd[bm]
    ks = sorted(dd)
    i = ks.index(bm)
    if 0 < i < len(ks) - 1:
        curv = (dd[ks[i+1]] - 2*dd[ks[i]] + dd[ks[i-1]]) / ((ks[i+1]-ks[i])**2)
        print(f"n={n:>4}: beta*={bm:.3f} min_f={fm:.5f} curv={curv:.2f}")

# error budget: band truncation n*2^{-(s+R)} at s*, R=90
print("\n=== band truncation error at s* (R=90) ===")
for n in (100, 200, 300):
    s = ss[ns == n][0]
    print(f"n={n}: s*={s}, err<= {n}*2^-({s}+90) ~ {n*2**(-(s+90)):.2e}")
