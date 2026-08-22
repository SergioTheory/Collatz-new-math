import pandas as pd
import ast

df = pd.read_csv('new_zone3_shifts.csv')
df['blocks'] = df['blocks'].apply(ast.literal_eval)

core_len = 112
for idx, row in df.iterrows():
    vec = row['blocks']
    core = vec[:core_len]
    tail = vec[core_len:]
    peak = row['original_peak']
    bits = row['original_bits']
    print(f"{idx+1:2d}: peak={peak}, bits={bits}, d={len(vec)}, tail_len={len(tail)}, tail_sum={sum(tail)}, tail_mean={sum(tail)/len(tail) if tail else 0:.3f}")
    if tail:
        print(f"   tail first 10: {tail[:10]}")