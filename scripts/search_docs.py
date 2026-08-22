import sys

def search_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"--- {filepath} ---")
            for i, line in enumerate(lines):
                if '7.3' in line or 'budget' in line.lower() or 'experimental' in line.lower():
                    print(f"{i+1}: {line.strip()}")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

search_file('Collatz_v11_ru.tex')
search_file('Collatz_v11_en.tex')
