import csv

def load_all_centers():
    files = ['confluence_census.csv', 'targeted_31_50.csv', 'targeted_41_50.csv', 'targeted_missing.csv']
    centers = {} # peak -> (bits, hr)
    for f in files:
        try:
            with open(f, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    c = int(row['center'])
                    p = int(row.get('peak', 0))
                    hr = float(row.get('hit_rate', 0.0))
                    if p > 0:
                        if p not in centers or hr > centers[p][1]:
                            centers[p] = (c.bit_length(), hr)
        except Exception as e:
            pass
    return centers

def analyze_alpha():
    centers = load_all_centers()
    full = []
    trans = []
    
    for p, (bits, hr) in centers.items():
        # Effective alpha = bits / p
        # "True" alpha is the slope. Let's compute effective alpha first
        eff_alpha = bits / p
        
        # We can also compute deviation from the expected Class B formula
        # expected_bits = 0.498 * p + 6.29
        # diff = bits - expected_bits
        
        if hr >= 0.7:
            full.append((p, bits, eff_alpha))
        else:
            trans.append((p, bits, eff_alpha))
            
    avg_full = sum(x[2] for x in full) / len(full) if full else 0
    avg_trans = sum(x[2] for x in trans) / len(trans) if trans else 0
    
    print(f"Total Unique Peaks: {len(centers)}")
    print(f"Full Centers (HR >= 0.7): {len(full)}")
    print(f"Transitional Centers (HR < 0.7): {len(trans)}")
    print(f"---")
    print(f"Avg Effective Alpha for Full Centers: {avg_full:.4f}")
    print(f"Avg Effective Alpha for Transitional Centers: {avg_trans:.4f}")
    
    print("\nDetailed list of Transitional Centers:")
    for p, bits, eff_alpha in trans:
        print(f"Peak {p:3} | Bits {bits:2} | Alpha = {eff_alpha:.4f}")

if __name__ == "__main__":
    analyze_alpha()
