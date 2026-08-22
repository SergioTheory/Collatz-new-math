import json
import csv

# ============================================================
# Функция извлечения shift-вектора (копия из предыдущего скрипта)
# ============================================================

def extract_blocks_from_number(n: int, include_partial: bool = False):
    """Возвращает словарь с shift-вектором и метриками."""
    if n <= 0:
        raise ValueError("n must be positive")

    traj = [n]
    x = n
    peak = n
    peak_step = 0
    step = 0

    while x != 1:
        if x & 1:
            x = 3 * x + 1
        else:
            x //= 2
        traj.append(x)
        step += 1
        if x > peak:
            peak = x
            peak_step = step

    blocks = []
    i = 0
    L = peak_step + 1

    while i < L:
        if traj[i] % 2 == 1:
            if i + 1 >= L:
                break
            count = 0
            j = i + 1
            while j < L and traj[j] % 2 == 0:
                count += 1
                j += 1
            if j == L:
                if include_partial:
                    blocks.append(count)
                break
            else:
                blocks.append(count)
                i = j
        else:
            i += 1

    d = len(blocks)
    S = sum(blocks)
    input_bits = n.bit_length()
    peak_bits = peak.bit_length()
    gain = peak_bits - input_bits

    return {
        'n': str(n),
        'blocks': blocks,
        'd': d,
        'S': S,
        'input_bits': input_bits,
        'peak_bits': peak_bits,
        'gain': gain,
        'S_d': S / d if d else 0,
    }

# ============================================================
# Основная часть
# ============================================================

with open('extra_seeds.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    seeds = data['seeds']

results = []
for seed in seeds:
    # Получаем число n
    if 'n' in seed:
        n = int(seed['n'])
    elif 'binary' in seed:
        n = int(seed['binary'], 2)
    else:
        print("Пропуск: нет n или binary")
        continue

    bits = seed.get('bits', n.bit_length())
    peak = seed.get('peak_bits')

    try:
        info = extract_blocks_from_number(n)
        info['original_peak'] = peak
        info['original_bits'] = bits
        info['n'] = str(n)
        results.append(info)
    except Exception as e:
        print(f"Ошибка для числа {n}: {e}")

# Сохраняем в CSV
with open('new_zone3_shifts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['n', 'input_bits', 'peak_bits', 'd', 'S', 'S_d', 'gain', 'blocks', 'original_peak', 'original_bits'])
    writer.writeheader()
    for r in results:
        r['blocks'] = str(r['blocks'])  # преобразуем список в строку
        writer.writerow(r)

print(f"Обработано {len(results)} чисел. Результаты в new_zone3_shifts.csv")