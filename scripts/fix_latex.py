import re

# 1. Read Collatz_v12_ru_temp.tex which is the clean translation but with structural elements not reordered
# Wait, Collatz_v12_ru_temp.tex is the one we started with. Let's use it as base.
with open('Collatz_v12_ru_temp.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 2. Fix the literal `\n` issue without breaking LaTeX commands
# Any place that has literal \n followed by \noindent or \textbf or \textit
content = re.sub(r'\\n\\noindent', r'\\noindent', content)
content = re.sub(r'\\n\\textbf', r'\\textbf', content)
content = re.sub(r'\\n\\textit', r'\\textit', content)
content = re.sub(r'\\n\\smallskip', r'\\smallskip', content)

# 3. Apply the numerical fixes
content = content.replace(r'K^{1/\gamma} \approx e^{10.3} \approx 3 \times 10^4', r'K^{1/\gamma} \approx 10^{7.7}')
content = content.replace(r'\approx 1 - 2.5 \times 10^{-17}', r'\approx 1 - 2.5 \times 10^{-9}')
content = content.replace(r'P - B \approx 68.4', r'P - B \approx 63.8')
content = content.replace(r'I_1 \circ I_1 \circ I_2', r'I_2 \circ I_1 \circ I_1')
content = content.replace('(композиция, сопряженная прямому паттерну (2,1,1))', '(применяя $I_1$, затем $I_1$, затем $I_2$, что сопряжено прямому паттерну (2,1,1))')
content = content.replace(r'c = 0.416 (проверено вычислительно для n \le 14 на частотах', r'c = 0.416 (строгая консервативная граница, проверенная вычислительно для n \le 14 на частотах')
content = content.replace(r'c \approx 0.55', r'c \approx 0.55 (эмпирический спектральный зазор)')
content = content.replace(r'c \approx 0.61', r'c \approx 0.61 (эмпирическое затухание Фурье)')
content = content.replace('которое сильнее, чем теоретическая граница 3^{-2.26n}', 'которое сильнее, чем теоретическая граница 3^{-2.26n} (поскольку $2n-3 < 2.26n$ при больших $n$, эмпирическая нижняя граница больше и потому сильнее)')

# 4. Structural Order
sections = re.split(r'(?=\\section\{|\\section\*\{|\\subsection\{|\\appendix)', content)

new_parts = {
    'main': [],
    'branching': [],
    'effective': [],
    'conclusion': [],
    'appendix_start': [],
    'app_a': [],
    'app_b': [],
    'bib': []
}

current_group = 'main'
for sec in sections:
    if sec.startswith(r'\subsection{Баланс ветвления: центр как каустика (Модель T1)}'):
        current_group = 'branching'
    elif sec.startswith(r'\section{Эффективные Оценки Почти Всюду для орбит Коллатца}'):
        current_group = 'effective'
    elif sec.startswith(r'\section{Заключение: Кристаллы нельзя вырастить}'):
        current_group = 'conclusion'
    elif sec.startswith(r'\section*{Доступность данных и дополнительные материалы}'):
        current_group = 'conclusion'
    elif sec.startswith(r'\appendix'):
        current_group = 'appendix_start'
    elif sec.startswith(r'\section*{Приложение A. Основные скрипты проекта}'):
        current_group = 'app_a'
    elif sec.startswith(r'\section{Природа Инстантона (Экспедиция B)}'):
        current_group = 'app_b'
    elif sec.startswith(r'\begin{thebibliography}'):
        current_group = 'bib'
    
    new_parts[current_group].append(sec)
    
    if current_group == 'branching':
        current_group = 'main'

final_content = ''.join(new_parts['main']) + \
                ''.join(new_parts['branching']) + \
                ''.join(new_parts['effective']) + \
                ''.join(new_parts['conclusion']) + \
                ''.join(new_parts['appendix_start']) + \
                ''.join(new_parts['app_a']) + \
                ''.join(new_parts['app_b']) + \
                ''.join(new_parts['bib'])

with open('Collatz_v12_ru.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)
