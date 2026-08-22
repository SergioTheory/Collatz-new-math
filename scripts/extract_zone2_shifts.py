import csv

# ============================================================
# Функция извлечения shift-вектора (скопирована из предыдущего)
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
# Числа Zone 2 (взять из records_data.py или из ваших данных)
# ============================================================

# Примеры из records_data.py (проверьте и при необходимости скорректируйте)
# 71 бит (Барина) – бинарная строка "10111111011101000101101010111101101011101101000001010000111010011101111"
n71 = 2358909599867980429759
# 72 бит – ваше рекордное
n72 = 4717819199735960859518
# 76 бит – бинарная строка "1111111111000000111001001100111000010101000110111001111001110011011111101000"
n76 = 75485107195775373752305
# 82 бит – бинарная строка "11111111110000001110010011001110000101010001101110011110011100110111111110110011"
n82 = 4831046860529623920148297
# 87 бит – бинарная строка "111111111100000011100100110011100001010100011011100111100111001101111111100011"
n87 = 154593499536947965444748439

# Список чисел, которые вы хотите проанализировать
zone2_numbers = [n71, n72, n76, n82, n87]

# Можно добавить и другие, например 79 бит, если есть.

results = []
for n in zone2_numbers:
    if n == 0:
        continue
    info = extract_blocks_from_number(n)
    info['original_bits'] = n.bit_length()
    info['n'] = str(n)
    results.append(info)

# Сохраняем в CSV
with open('zone2_shifts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['n', 'input_bits', 'peak_bits', 'd', 'S', 'S_d', 'gain', 'blocks', 'original_bits'])
    writer.writeheader()
    for r in results:
        r['blocks'] = str(r['blocks'])
        writer.writerow(r)

print(f"Сохранено {len(results)} чисел в zone2_shifts.csv")