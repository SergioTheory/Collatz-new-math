with open(r'C:\Users\Admin\Documents\Collatz\docs\Collatz_v11_ru.tex', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace(r'\_a > 15$.', r'$max\_a > 15$.')
with open(r'C:\Users\Admin\Documents\Collatz\docs\Collatz_v11_ru.tex', 'w', encoding='utf-8') as f:
    f.write(text)
