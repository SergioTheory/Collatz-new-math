import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from collatz_peak import analyze_to_peak

stats = analyze_to_peak(27)
print(f"Number 27: d={stats['d']}, S={stats['S']}, S/d={stats['S']/stats['d'] if stats['d']>0 else 0}")
