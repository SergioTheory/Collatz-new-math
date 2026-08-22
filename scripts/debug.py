import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from collatz_dynamics import analyze_to_peak
from collatz_peak import analyze_to_peak as analyze_to_peak_orig

x_star = 20152090995747160937051
print("New dynamics:")
print(analyze_to_peak(x_star))
print("Orig dynamics:")
print(analyze_to_peak_orig(x_star))
