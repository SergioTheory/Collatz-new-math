import math
import pandas as pd
import ast
import matplotlib.pyplot as plt
from crt_solver import number_from_parity, collatz_peak

LOG2_3 = math.log2(3)

def compute_gains_from_blocks(blocks):
    gains = []
    cum_s = 0
    for k, s in enumerate(blocks, 1):
        cum_s += s
        gains.append(k * LOG2_3 - cum_s)
    return gains

# 1. Zone 2 – берём сдвиги из zone2_shifts.csv (любое число, например, 87 бит)
df_z2 = pd.read_csv('zone2_shifts.csv')
df_z2['blocks'] = df_z2['blocks'].apply(ast.literal_eval)
# Возьмём первое число (любое)
row_z2 = df_z2.iloc[0]
shifts_z2 = row_z2['blocks']
gains_z2 = compute_gains_from_blocks(shifts_z2)
print(f"Zone 2: d={len(shifts_z2)}, final gain={gains_z2[-1]:.2f} (peak={row_z2['peak_bits']}, bits={row_z2['input_bits']})")

# 2. Family A vicinity – из new_zone3_shifts.csv (или zone3_shifts.csv)
try:
    df_fa = pd.read_csv('new_zone3_shifts.csv')
except FileNotFoundError:
    df_fa = pd.read_csv('zone3_shifts.csv')
df_fa['blocks'] = df_fa['blocks'].apply(ast.literal_eval)
# Выбираем число с peak=239 и bits=150 (или близкое)
mask = (df_fa['original_peak'] == 239) & (df_fa['original_bits'] == 150)
if mask.sum() == 0:
    # Если нет, возьмём любое с high peak
    mask = df_fa['original_peak'] > 237
row_fa = df_fa[mask].iloc[0]
shifts_fa = row_fa['blocks']
gains_fa = compute_gains_from_blocks(shifts_fa)
print(f"Family A vicinity: d={len(shifts_fa)}, final gain={gains_fa[-1]:.2f} (peak={row_fa['original_peak']}, bits={row_fa['original_bits']})")

# График
plt.figure(figsize=(12, 6))
plt.plot(range(1, len(gains_z2)+1), gains_z2, label='Zone 2 (peak 140)')
plt.plot(range(1, len(gains_fa)+1), gains_fa, label='Family A vicinity (peak ~239)')
plt.xlabel('Шаг k')
plt.ylabel('Кумулятивный gain G(k)')
plt.title('Сравнение структуры траекторий')
plt.legend()
plt.grid()
plt.savefig('gain_comparison.png', dpi=150)
plt.show()