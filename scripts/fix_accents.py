with open(r'C:\Users\Admin\Documents\Collatz\docs\Collatz_v11_ru.tex', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("б\\'ольш", "больш")
with open(r'C:\Users\Admin\Documents\Collatz\docs\Collatz_v11_ru.tex', 'w', encoding='utf-8') as f:
    f.write(text)
