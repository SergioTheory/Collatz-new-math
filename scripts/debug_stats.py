import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from collatz_dynamics import analyze_to_peak

def main():
    data_path = os.path.join("data", "expand_913.json")
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    d_set = set()
    s_diff = set()
    for item in data:
        n = int(item['n'])
        stats = analyze_to_peak(n)
        d_set.add(stats['d'])
        s_diff.add(stats['S'] - n.bit_length())
        
    print("Unique d values:", d_set)
    print("Unique (S - bits) values:", s_diff)

if __name__ == '__main__':
    main()
