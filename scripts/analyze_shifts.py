import pandas as pd
import ast

# Загружаем данные
df = pd.read_csv('zone3_shifts.csv')
df['blocks'] = df['blocks'].apply(ast.literal_eval)  # преобразуем строку в список

print("Первые 5 строк:")
print(df.head())
print("\nСписок колонок:", df.columns.tolist())

print("=== ОБЩАЯ ИНФОРМАЦИЯ ===")
print(f"Всего чисел: {len(df)}")
print("\nРаспределение по исходным пикам (original_peak):")
print(df['original_peak'].value_counts().sort_index())
print("\nРаспределение по исходной битности входа (original_bits):")
print(df['original_bits'].value_counts().sort_index())

print("\n=== АНАЛИЗ d И S ПО ГРУППАМ (original_peak, original_bits) ===")
for peak in sorted(df['original_peak'].unique()):
    sub = df[df['original_peak'] == peak]
    for bits in sorted(sub['original_bits'].unique()):
        sub2 = sub[sub['original_bits'] == bits]
        d_vals = sub2['d'].tolist()
        S_vals = sub2['S'].tolist()
        d_unique = set(d_vals)
        if len(d_unique) == 1:
            d_const = d_vals[0]
            S_unique = set(S_vals)
            if len(S_unique) == 1:
                print(f"peak={peak}, bits={bits}: d={d_const}, S={S_vals[0]} (постоянны)")
            else:
                print(f"peak={peak}, bits={bits}: d={d_const} (постоянно), S варьируется: {sorted(S_unique)}")
        else:
            print(f"peak={peak}, bits={bits}: d варьируется: {sorted(d_unique)}")

print("\n=== СРАВНЕНИЕ ВЕКТОРОВ В ГРУППАХ (общий префикс) ===")
def common_prefix(seq1, seq2):
    n = min(len(seq1), len(seq2))
    for i in range(n):
        if seq1[i] != seq2[i]:
            return i
    return n

for peak in sorted(df['original_peak'].unique()):
    sub = df[df['original_peak'] == peak]
    for bits in sorted(sub['original_bits'].unique()):
        group = sub[sub['original_bits'] == bits]
        if len(group) < 2:
            continue
        vectors = group['blocks'].tolist()
        pref = common_prefix(vectors[0], vectors[1])
        total_len = min(len(vectors[0]), len(vectors[1]))
        print(f"peak={peak}, bits={bits}: общий префикс первых двух векторов: {pref} из {total_len} ({pref/total_len:.1%})")
        if len(group) > 2:
            all_pref = min(common_prefix(vectors[0], v) for v in vectors[1:])
            print(f"    минимальный общий префикс для всех {len(group)} векторов: {all_pref}")

print("\n=== СРАВНЕНИЕ ПРЕФИКСОВ РАЗНЫХ ГРУПП ===")
# Выбираем группы с одинаковой битностью, но разными пиками
target_bits = 147  # самая частая битность в данных
print(f"Сравниваем группы с original_bits = {target_bits}:")

# Получаем список всех пиков для этой битности
peaks = sorted(df[df['original_bits'] == target_bits]['original_peak'].unique())
if len(peaks) > 1:
    # Для каждого пика берём первый вектор (или общий префикс группы)
    # Для простоты возьмём первый вектор из группы
    groups = {}
    for p in peaks:
        group = df[(df['original_peak'] == p) & (df['original_bits'] == target_bits)]
        if len(group) > 0:
            # Можно взять общий префикс группы, но для демонстрации возьмём первый вектор
            vec = group['blocks'].iloc[0]
            groups[p] = vec
            print(f"peak={p}: первые 20 элементов: {vec[:20]}")
    # Сравниваем попарно
    for i, (p1, v1) in enumerate(groups.items()):
        for p2, v2 in list(groups.items())[i+1:]:
            pref = common_prefix(v1, v2)
            print(f"Общий префикс между peak={p1} и peak={p2}: {pref}")

# Также сравним для другой битности, например 150
target_bits2 = 150
print(f"\nСравниваем группы с original_bits = {target_bits2}:")
peaks2 = sorted(df[df['original_bits'] == target_bits2]['original_peak'].unique())
if len(peaks2) > 1:
    groups2 = {}
    for p in peaks2:
        group = df[(df['original_peak'] == p) & (df['original_bits'] == target_bits2)]
        if len(group) > 0:
            vec = group['blocks'].iloc[0]
            groups2[p] = vec
            print(f"peak={p}: первые 20 элементов: {vec[:20]}")
    for i, (p1, v1) in enumerate(groups2.items()):
        for p2, v2 in list(groups2.items())[i+1:]:
            pref = common_prefix(v1, v2)
            print(f"Общий префикс между peak={p1} и peak={p2}: {pref}")

print("\n=== ВСЁ ГОТОВО ===")