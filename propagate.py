import math

# --- Верифицированные входы конвейера ---
I_133  = 0.2532           # структурная (обратная) ставка I_rev(1.33) в битах (Phase 2)
log2_3 = math.log2(3)     # 1.58496
sigma  = 1.33
gain   = log2_3 - sigma   # прямой прирост бита/шаг для аккорда силы sigma = 0.25496

# --- Структурный показатель ---
gamma = I_133 / gain
print(f"gamma = I_rev(1.33)/(log2 3 - 1.33) = {gamma:.4f}")

# --- Порог N0* = K^{1/gamma} и остаток на фронте 2^68 ---
B = 68
for K in (1e3, 1.4e5):
    N0star = K ** (1/gamma)
    resid  = K * (2**B) ** (-gamma)
    margin = B - math.log2(N0star)
    print(f"K={K:.1e}: N0*={N0star:.2e} (log2={math.log2(N0star):.1f}), "
          f"residual@2^68={resid:.2e}, margin={margin:.1f} bit (~10^{margin*math.log10(2):.0f})")
