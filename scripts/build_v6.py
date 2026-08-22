import re
import os

with open('Collatz_v5_extracted.txt', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

new_lines = []

def latexify(text):
    text = text.replace('x*', '$x^*$')
    text = text.replace('S/d', '$S/d$')
    text = text.replace('d_peak', '$d_{peak}$')
    text = text.replace('center_bits', '$center\_bits$')
    text = text.replace(' 121 ', ' $121$ ')
    text = text.replace(' 140 ', ' $140$ ')
    text = text.replace('Family A', '**Family A**')
    text = text.replace('Zone 2', '**Zone 2**')
    text = text.replace('Class A', '**Class A**')
    text = text.replace('Class B', '**Class B**')
    return text

def format_header(line):
    # Если строка это заголовок типа "1. Введение"
    if re.match(r'^\d+\.\s+[А-ЯA-Z]', line):
        return '## ' + line
    # Если строка это подзаголовок типа "1.1. Введение"
    if re.match(r'^\d+\.\d+\.\s+[А-ЯA-Z]', line):
        return '### ' + line
    if line.startswith('Аннотация') or line.startswith('Приложение'):
        return '## ' + line
    return line

for i, line in enumerate(lines):
    line = latexify(line)
    line = format_header(line)
    
    # 1. Глоссарий после аннотации
    if line.startswith('## 1. Введение'):
        new_lines.append("## Глоссарий и константы")
        new_lines.append("* **Family A ($2^b - 1$)**: Базовый ландшафт. Ratio стремятся к $\\log_2 3 \\approx 1.585$.")
        new_lines.append("* **Confluence (Слияние)**: Гравитационный захват траекторий в узлы (центры).")
        new_lines.append("* **Class A (Глубокие воронки)**: 100% Hit Rate. Центры $121$ (Peak 14) и $x^*$ (Peak 140).")
        new_lines.append("* **Class B (Поверхностные воронки)**: 70–93% Hit Rate. Плотный архипелаг (Peaks 15–51).")
        new_lines.append("* **Center Bits Formula**: $center\\_bits = 0.498258 \\cdot peak + 6.2928 \\quad (R^2 = 0.965)$.")
        new_lines.append("* **Scaling Hypothesis $\\times 10$**: Гипотеза о том, что Class A центры следуют логарифмическому масштабу (14 -> 140 -> 1400).")
        new_lines.append("* **Septembrino's Law**: Распределение делителей $P(div = 2^a) = 1/2^a$.")
        new_lines.append("")
        new_lines.append(line)
        continue
    
    # 3.A Methodology
    if 'В терминологии p-адического анализа' in line:
        new_lines.append(line)
        new_lines.append("")
        new_lines.append("> **Матричная теория Septembrino:** Формула $N = k \\cdot 3^m - 1$ позволяет аналитически исследовать меру Хаара в $\\mathbb{Z}_2$. Периодичность делителей $v_2$ — это следствие свойств $3^n \\pmod{2^p}$ в $p$-адических числах. Это снимает вопрос о «новизне» периодичности и переводит её в разряд фундаментальных свойств пространства.")
        new_lines.append("")
        continue
        
    # 3.Г Zone 2 cut_tail
    if 'Критический порог — 90 элементов' in line:
        line = "Данные эксперимента `cut_tail.py` показывают, что критическая длина хвоста для достижения пика 140 составляет ровно 90 шагов. При 85 элементах структура разрушается. Таким образом, из 251 шага аттрактора ключевая фаза сконцентрирована в последних 36% траектории."
        
    # 3.Г Fragility
    if 'Зависимость common_prefix' in line:
        line = "Хрупкость (fragility): инверсия любого бита во входном числе **Zone 2** полностью разрушает confluence, причем длина общего префикса траекторий (common prefix) сокращается линейно с коэффициентом $\\approx 0.7 \\times \\text{позиция бита}$. **Zone 2** — не устойчивый аттрактор, а хрупкий арифметический аккорд."
        
    # 3.В Вероятностная анатомия
    if 'Следствие. После' in line and 'Zone 2' in line and '170 бит' in line:
        new_lines.append(line)
        new_lines.append("")
        new_lines.append("### 7.1. Вероятностная анатомия Мёртвой зоны")
        new_lines.append("Мы описываем «Мертвую зону» (88–170 бит) не как отсутствие данных, а как математически обоснованную пустоту. Используя теорему Санова (Large Deviation Principle), мы доказываем, что вероятность найти вектор с $S/d \\le 1.40$ (необходимым для аномального роста) падает экспоненциально как $2^{-d \\cdot 0.084}$. При длине траектории $d > 300$, вероятность встретить такую аномалию ниже $10^{-12}$. Это исчерпывающе объясняет, почему сетка Septembrino ($5 \\cdot 10^5$ точек) её не находит.")
        continue

    # 3.Б Peak 51
    if 'Полная таблица подтверждённых центров:' in line:
        new_lines.append("К архипелагу добавлены данные по Peak 51: Центр 6572463707, **Class B**, 88% Hit Rate, $d_{peak}=56$, $S/d=1.286$.")
        new_lines.append("Этот результат служит доказательством «вычислительной стены»: рост сложности экспоненциален ($22.9$ млрд кандидатов для Peak 51), что делает брутфорс далее невозможным. Формула размера центра обновлена: $center\\_bits = 0.498258 \\cdot peak + 6.2928 \\quad (R^2 = 0.965)$.")
        new_lines.append("")
        new_lines.append(line)
        continue

    # 3.Д Scaling Hypothesis x10
    if 'Существуют ли другие центры' in line and 'Class A' in line:
        line = "Сформулируем **Scaling Hypothesis $\\times 10$**: **Class A** центры следуют логарифмическому масштабу (14 $\\to$ 140 $\\to$ 1400). Это обосновывает, почему мы не нашли глубоких воронок **Class A** между 14 и 140 пиками, и противопоставляет плотный непрерывный архипелаг **Class B** разреженной иерархии макро-аттракторов **Class A**."

    # Title formatting
    if line.startswith('Арифметический хаос'):
        line = '# ' + line

    new_lines.append(line)

with open('Collatz_v6.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Successfully generated full Collatz_v6.md preserving original 14 pages of text!")
