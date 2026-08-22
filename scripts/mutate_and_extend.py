import sys
# Путь к папке, где лежит crt_solver.py (если не в текущей)
sys.path.insert(0, r'C:\Users\Admin\Desktop\CrystalHunter2\dist')
# Если crt_solver.py не там, скопируйте или укажите правильный путь

import json
from crt_solver import number_from_parity, collatz_peak

# Загрузите хвост из предыдущего эксперимента (вставьте ваш список)
# Например, из вывода recover_from_tail.py: первые 20: [1,2,1,1,2,1,2,1,1,2,1,2,1,1,2,1,1,2,2,1]...
# Полный список у вас должен быть сохранён. Если нет, можно взять из zone2_shifts.csv.
# Для удобства я приведу пример из вывода: первые 20 элементов, но нужно полный список.
# Вы можете извлечь его из zone2_shifts.csv: для любого вектора (например, 87 бит) взять срез [7:].

# Для демонстрации я создам заглушку; вы замените на реальный список.
# Предположим, вы сохранили tail как список целых чисел.
# Например:
# tail = [1,2,1,1,2,1,2,1,1,2,1,2,1,1,2,1,1,2,2,1, ...]  # 251 элемент
# Если нет, можно загрузить из zone2_shifts.csv:
import csv
import ast

with open('zone2_shifts.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
# Возьмём вектор для 87 бит (или любой), общий хвост начинается с позиции 7
vec = ast.literal_eval(rows[0]['blocks'])  # первый вектор
tail = vec[7:]   # начиная с позиции 7
print(f"Длина хвоста: {len(tail)}")

def tail_to_parity(t):
    return ''.join('1' + '0' * s for s in t)

def test(label, blocks):
    parity = tail_to_parity(blocks)
    n = number_from_parity(parity)
    if n is None or n <= 0:
        print(f"{label}: не удалось восстановить")
        return
    bits = n.bit_length()
    peak, steps, conv = collatz_peak(n)
    print(f"{label}: bits={bits}, peak={peak}, gain={peak-bits}, ratio={peak/bits:.4f}, S={sum(blocks)}")

print("=== ОРИГИНАЛ ===")
test("original", tail)

# Тип 1: двойка → единица (gain +1)
print("\n=== ТИП 1: двойка → единица (gain +1) ===")
pos_2 = [i for i, s in enumerate(tail) if s == 2]
for pos in pos_2[:10]:  # первые 10
    t = tail.copy()
    t[pos] = 1
    test(f"2→1 pos={pos}", t)

# Тип 2: единица → двойка (gain -1)
print("\n=== ТИП 2: единица → двойка (gain -1) ===")
pos_1 = [i for i, s in enumerate(tail) if s == 1]
step = max(1, len(pos_1)//10)
for idx in range(0, len(pos_1), step)[:10]:
    pos = pos_1[idx]
    t = tail.copy()
    t[pos] = 2
    test(f"1→2 pos={pos}", t)

# Тип 3: перестановка соседних [1,2] → [2,1]
print("\n=== ТИП 3: перестановка (S сохраняется) ===")
swap_count = 0
for i in range(len(tail)-1):
    if tail[i] == 1 and tail[i+1] == 2:
        t = tail.copy()
        t[i], t[i+1] = t[i+1], t[i]
        test(f"swap {i}<->{i+1}", t)
        swap_count += 1
        if swap_count >= 10:
            break

# Удлинение: добавление единиц в начало
print("\n=== УДЛИНЕНИЕ: единичный префикс + хвост ===")
for extra in [10, 20, 30, 50, 80, 100]:
    extended = [1] * extra + tail
    test(f"prefix={extra}", extended)