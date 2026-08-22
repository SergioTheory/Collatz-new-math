import csv
import glob

def test_alpha():
    centers = []
    
    files = ['confluence_census.csv', 'targeted_31_50.csv', 'targeted_41_50.csv']
    
    for f in files:
        try:
            with open(f, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    c = int(row['center'])
                    p = int(row.get('peak', 0))
                    hr = float(row.get('hit_rate', row.get('hr_depth_15', 0)))
                    status = row.get('status', 'Unknown')
                    if p > 0:
                        centers.append((c, p, hr, status))
        except Exception as e:
            pass
            
    print(f"Loaded {len(centers)} centers.")
    print(f"{'Center':>15} | {'Bits':>4} | {'Peak':>4} | {'Peak/2':>6} | {'Diff (Bits - P/2)':>18} | {'Hit Rate':>8} | {'Status':>10}")
    print("-" * 80)
    
    # Sort by peak
    centers.sort(key=lambda x: x[1])
    
    # Deduplicate by center
    seen = set()
    unique_centers = []
    for c, p, hr, st in centers:
        if c not in seen:
            seen.add(c)
            unique_centers.append((c, p, hr, st))
            
    diffs_complete = []
    diffs_trans = []
    
    for c, p, hr, status in unique_centers:
        bits = c.bit_length()
        diff = bits - (p / 2)
        print(f"{c:15} | {bits:4} | {p:4} | {p/2:6.1f} | {diff:18.4f} | {hr:8.4f} | {status}")
        
        # Consider a center complete if HR > 0.99 or status is CONFIRMED
        if hr > 0.99 or status == 'CONFIRMED' or status == 'CANDIDATE':
            # Actually, Candidate might also be complete. Let's group by HR
            pass
            
        if hr >= 0.7:  # Complete or nearly complete
            diffs_complete.append(diff)
        else:
            diffs_trans.append(diff)
            
    if diffs_complete:
        avg_comp = sum(diffs_complete) / len(diffs_complete)
        print(f"\nAverage Diff for Centers with HR >= 0.70 (n={len(diffs_complete)}): {avg_comp:.4f}")
    if diffs_trans:
        avg_trans = sum(diffs_trans) / len(diffs_trans)
        print(f"Average Diff for Transitional Centers HR < 0.70 (n={len(diffs_trans)}): {avg_trans:.4f}")

if __name__ == "__main__":
    test_alpha()
