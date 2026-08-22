import pandas as pd
import ast

def common_prefix_len(a, b):
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))

# Загружаем старые данные (zone3_shifts.csv)
df_old = pd.read_csv('zone3_shifts.csv')
df_old['blocks'] = df_old['blocks'].apply(ast.literal_eval)

# Загружаем новые данные
df_new = pd.read_csv('new_zone3_shifts.csv')
df_new['blocks'] = df_new['blocks'].apply(ast.literal_eval)

# Выбираем эталонные векторы из старых кластеров
# Канал α: peak=233, bits=147
alpha_row = df_old[(df_old['original_peak'] == 233) & (df_old['original_bits'] == 147)].iloc[0]
alpha_vector = alpha_row['blocks']
print(f"Эталон канала α: peak={alpha_row['original_peak']}, bits={alpha_row['original_bits']}, d={alpha_row['d']}, длина вектора={len(alpha_vector)}")

# Канал β: peak=234, bits=147 (или 236)
beta_row = df_old[(df_old['original_peak'] == 234) & (df_old['original_bits'] == 147)].iloc[0]
beta_vector = beta_row['blocks']
print(f"Эталон канала β: peak={beta_row['original_peak']}, bits={beta_row['original_bits']}, d={beta_row['d']}, длина вектора={len(beta_vector)}")

print("\n=== Анализ новых чисел ===")
for idx, row in df_new.iterrows():
    vec = row['blocks']
    peak = row['original_peak']
    bits = row['original_bits']
    d = row['d']
    len_vec = len(vec)
    prefix_alpha = common_prefix_len(alpha_vector, vec)
    prefix_beta = common_prefix_len(beta_vector, vec)
    print(f"{idx+1:2d}: peak={peak}, bits={bits}, d={d}, len={len_vec}, pref_α={prefix_alpha}, pref_β={prefix_beta}")