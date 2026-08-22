import pandas as pd
import ast

def common_prefix_all(vectors):
    """Возвращает общий префикс всех векторов."""
    if not vectors:
        return []
    min_len = min(len(v) for v in vectors)
    for i in range(min_len):
        # Проверяем, одинаков ли элемент на позиции i у всех векторов
        first = vectors[0][i]
        for v in vectors[1:]:
            if v[i] != first:
                return vectors[0][:i]
    return vectors[0][:min_len]

# Загружаем новые данные
df = pd.read_csv('new_zone3_shifts.csv')
df['blocks'] = df['blocks'].apply(ast.literal_eval)

# Извлекаем все shift-векторы
vectors = df['blocks'].tolist()

# Находим общий префикс
core = common_prefix_all(vectors)
print(f"Общий префикс (ядро) для всех 50 чисел: длина {len(core)}")
print(f"Первые 20 элементов: {core[:20]}")
print(f"Последние 10 элементов: {core[-10:]}")

# Сохраняем ядро в файл
with open('core_alpha.txt', 'w') as f:
    f.write(','.join(map(str, core)))
print("Ядро сохранено в core_alpha.txt")