import os
import sys

from src.collatz_peak import analyze_to_peak

centers = {
    46: 516844415,
    47: 442441855,
    48: 2303929595,
    49: 3830005073,
    50: 1396693151,
    51: 6572463707
}

for peak, center in centers.items():
    stats = analyze_to_peak(center)
    d = stats['d']
    s = stats['S']
    ratio = s / d if d > 0 else 0
    print(f"Peak {peak}: Center={center}, d={d}, S/d={ratio:.3f}")
