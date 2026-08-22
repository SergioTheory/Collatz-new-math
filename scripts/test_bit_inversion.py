import pandas as pd
import ast

# ============================================================
# Функция извлечения shift-вектора (скопирована из extract_shifts.py)
# ============================================================

def extract_blocks_from_number(n: int, include_partial: bool = False):
    """
    Возвращает список сдвигов [s1,...,sd] до пика.
    Также возвращает d, S, peak, gain и т.д.
    include_partial: если True, включает незавершённый odd-step, если пик достигнут на even-хвосте.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    traj = [n]
    x = n
    peak = n
    peak_step = 0
    step = 0

    # Сначала полная траектория до 1, чтобы узнать пик
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

    # Теперь идём по траектории до peak_step и собираем блоки
    blocks = []
    i = 0
    L = peak_step + 1  # включаем сам пик

    while i < L:
        if traj[i] % 2 == 1:  # odd
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
# Тест инверсии битов
# ============================================================

def invert_bit(n, pos):
    """
    Инвертирует бит числа n на позиции pos (0 = младший бит).
    Возвращает новое число.
    """
    return n ^ (1 << pos)

def common_prefix_len(a, b):
    """Возвращает длину общего префикса двух списков."""
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))

# Загружаем данные из zone3_shifts.csv
df = pd.read_csv('zone3_shifts.csv')
df['blocks'] = df['blocks'].apply(ast.literal_eval)  # превращаем строку в список

# Находим первое число с original_peak=233 и original_bits=147
mask = (df['original_peak'] == 233) & (df['original_bits'] == 147)
if mask.sum() == 0:
    print("Нет числа с peak=233, bits=147. Берём первое число с original_peak=233.")
    mask = (df['original_peak'] == 233)
row = df[mask].iloc[0]
n_original = int(row['n'])
original_vector = row['blocks']  # уже список
print(f"Исходное число n = {n_original}")
print(f"Длина shift-вектора: {len(original_vector)}")
print(f"Первые 20 элементов вектора: {original_vector[:20]}")

# Позиции битов для инверсии (от младшего бита)
positions = [50, 60, 70, 80, 90]

print("\n=== Результаты инверсии битов ===")
for pos in positions:
    n_mut = invert_bit(n_original, pos)
    # Вычисляем shift-вектор для мутанта
    info = extract_blocks_from_number(n_mut)
    mutant_vector = info['blocks']
    common = common_prefix_len(original_vector, mutant_vector)
    print(f"Бит {pos:3d}: длина общего префикса = {common} из {len(original_vector)} (ориг) / {len(mutant_vector)} (мут)")
    # Для контроля покажем, что изменилось
    if common < len(original_vector):
        print(f"   Первое различие на позиции {common}: оригинал = {original_vector[common] if common < len(original_vector) else 'END'}, мутант = {mutant_vector[common] if common < len(mutant_vector) else 'END'}")