import json
import math
from crt_solver import collatz_peak, analyze_to_peak

with open('zone_search_results.json', 'r') as f:
    results = json.load(f)

print(f"{'bits':>5} {'peak':>5} {'ratio':>7} | {'d_designed':>5} {'S_designed':>5} | "
      f"{'d_actual':>5} {'S_actual':>5} {'S/d_act':>6} | match")
print("-" * 80)

for r in results[:20]:
    n = int(r['n'])
    bits = n.bit_length()
    
    # Реальный анализ до пика
    info = analyze_to_peak(n)
    d_actual = info['total_o']
    S_actual = info['total_e']
    sd_actual = S_actual / d_actual if d_actual > 0 else 0
    
    # Совпадает ли реальное d с запланированным?
    d_designed = r['d']
    S_designed = r['S']
    match = "YES" if abs(d_actual - d_designed) <= 2 else f"NO ({d_actual})"
    
    print(f"{bits:>5} {info['peak']:>5} {info['peak']/bits:>7.4f} | "
          f"{d_designed:>5} {S_designed:>5} | "
          f"{d_actual:>5} {S_actual:>5} {sd_actual:>6.3f} | {match}")