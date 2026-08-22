import math
import ast
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

LOG2_3 = math.log2(3)

# Загружаем данные
df = pd.read_csv('zone2_shifts.csv')
df['blocks'] = df['blocks'].apply(ast.literal_eval)

# Создаём словарь векторов
vectors_z2 = {}
for idx, row in df.iterrows():
    bits = row['input_bits']
    label = f"{bits}bit"
    vectors_z2[label] = row['blocks']

# Строим графики
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for label, blocks in vectors_z2.items():
    d = len(blocks)
    S = sum(blocks)
    
    # 1. Кумулятивный gain
    gains = []
    cum_s = 0
    for k, s in enumerate(blocks, 1):
        cum_s += s
        gains.append(k * LOG2_3 - cum_s)
    
    axes[0][0].plot(range(1, d+1), gains, label=f'{label} (d={d}, S={S})')
    
    # 2. Распределение сдвигов
    cnt = Counter(blocks)
    axes[0][1].bar([x + 0.1*list(vectors_z2).index(label) for x in cnt.keys()],
                   cnt.values(), width=0.1, label=label)
    
    # 3. Локальный наклон (скользящее среднее за 10 шагов)
    window = 10
    if len(gains) > window:
        slopes = [(gains[i+window] - gains[i]) / window for i in range(len(gains) - window)]
        axes[1][0].plot(range(1, len(slopes)+1), slopes, label=label)
    
    # 4. Позиции сдвигов >= 2
    positions_2plus = [i+1 for i, s in enumerate(blocks) if s >= 2]
    axes[1][1].eventplot([positions_2plus], lineoffsets=[list(vectors_z2).index(label)],
                         linelengths=0.5, label=label)
    
    # Текстовый вывод
    is_mono = all(gains[i] <= gains[i+1] for i in range(len(gains)-1))
    dips = sum(1 for i in range(len(gains)-1) if gains[i] > gains[i+1])
    print(f"\n=== {label} ===")
    print(f"  d={d}, S={S}, S/d={S/d:.3f}")
    print(f"  Final gain: {gains[-1]:.2f}")
    print(f"  Монотонный: {is_mono} (провалов: {dips})")
    print(f"  Сдвиги >= 2: {len(positions_2plus)} шт ({100*len(positions_2plus)/d:.1f}%)")
    print(f"  Макс сдвиг: {max(blocks)} на позиции {blocks.index(max(blocks))+1}")
    print(f"  Первые 30: {blocks[:30]}")
    print(f"  Последние 20: {blocks[-20:]}")

axes[0][0].set_title('Кумулятивный gain G(k)')
axes[0][0].set_xlabel('Шаг k'); axes[0][0].set_ylabel('G(k)')
axes[0][0].legend(); axes[0][0].grid(True)

axes[0][1].set_title('Распределение сдвигов')
axes[0][1].set_xlabel('Значение сдвига'); axes[0][1].set_ylabel('Количество')
axes[0][1].legend()

axes[1][0].set_title('Локальный наклон (скользящее среднее)')
axes[1][0].axhline(y=0, color='r', linestyle='--')
axes[1][0].set_xlabel('Шаг'); axes[1][0].set_ylabel('dG/dk')
axes[1][0].legend(); axes[1][0].grid(True)

axes[1][1].set_title('Позиции сдвигов >= 2')
axes[1][1].set_xlabel('Шаг')
axes[1][1].legend()

plt.tight_layout()
plt.savefig('zone2_analysis.png', dpi=150)
plt.show()