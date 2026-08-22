import csv
import ast
import sys

# Если crt_solver.py доступен, импортируем; иначе используем встроенную функцию
try:
    from crt_solver import number_from_parity
except ImportError:
    # Если нет, попробуем из zone_search
    try:
        sys.path.insert(0, r'C:\Users\Admin\Desktop\Zone_search')
        from zone_search import number_from_parity as num_from_parity
        number_from_parity = num_from_parity
    except ImportError:
        # Если и так нет, используем простую заглушку (но лучше установить)
        print("Не найден crt_solver или zone_search, не могу восстановить число.")
        sys.exit(1)

# Загружаем zone2_shifts.csv
vectors = []
with open('zone2_shifts.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        blocks = ast.literal_eval(row['blocks'])
        vectors.append(blocks)

print(f"Загружено {len(vectors)} векторов.")

# Определяем общий суффикс (хвост)
# Ищем минимальную длину среди всех векторов
min_len = min(len(v) for v in vectors)
# Найдём позицию, начиная с которой все векторы совпадают
# Будем идти с конца, чтобы найти общий хвост, или с начала? Нам нужен хвост, который одинаков.
# Мы знаем из данных, что последние 20 элементов идентичны. Найдём, где начинается совпадение.

# Сравниваем все векторы попарно, начиная с конца
common_start = min_len  # по умолчанию весь вектор
for i in range(min_len):
    # Сравним элементы на позиции i (с конца) у всех векторов
    pos = min_len - 1 - i
    val = vectors[0][pos] if pos < len(vectors[0]) else None
    ok = True
    for v in vectors:
        if pos >= len(v) or v[pos] != val:
            ok = False
            break
    if not ok:
        common_start = pos + 1
        break

print(f"Общий хвост начинается с позиции {common_start} (с 0)")

# Выделим хвост
tail = vectors[0][common_start:]

print(f"Длина хвоста: {len(tail)}")
print(f"Первые 20 элементов хвоста: {tail[:20]}")
print(f"Последние 20 элементов хвоста: {tail[-20:]}")

# Построим parity-строку
parity = ''
for s in tail:
    parity += '1' + '0' * s
print(f"Parity-строка (первые 100 символов): {parity[:100]}...")

# Восстанавливаем число
n = number_from_parity(parity)
if n is None:
    print("Не удалось восстановить число.")
else:
    bits = n.bit_length()
    print(f"Восстановленное число: {n}")
    print(f"Битность: {bits}")
    # Можно также вычислить пик, но для этого нужна симуляция
    try:
        from crt_solver import collatz_peak
        peak, steps, conv = collatz_peak(n)
        print(f"Пик (бит): {peak}")
        print(f"Ratio: {peak / bits:.5f}")
        print(f"Шаги: {steps}")
    except:
        print("Не удалось вычислить пик (нет collatz_peak)")

# Сохраним для анализа
with open('tail_parity.txt', 'w') as f:
    f.write(parity)
print("Parity-строка сохранена в tail_parity.txt")