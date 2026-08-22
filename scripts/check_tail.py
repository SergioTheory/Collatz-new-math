import ast
import csv

with open("zone2_shifts_full.csv", "r") as f:
    r = next(csv.DictReader(f))
    v = ast.literal_eval(r["blocks"])
    
tail = v[-90:]
dips = []
for i, a in enumerate(tail):
    if a >= 3:
        dips.append((89 - i) % 18)
        
from collections import Counter
print("Phases in tail:", Counter(dips))
