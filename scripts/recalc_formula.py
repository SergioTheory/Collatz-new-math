import csv
import math

def linregress(x, y):
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_x2 = sum(xi*xi for xi in x)
    sum_xy = sum(xi*yi for xi, yi in zip(x, y))
    
    denominator = n * sum_x2 - sum_x**2
    if denominator == 0:
        return 0, 0, 0
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    # R^2 calculation
    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y)**2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept))**2 for xi, yi in zip(x, y))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return slope, intercept, r_squared

def update_and_recalc():
    new_points = [
        {'peak': 15, 'center': 1127, 'center_bits': 11, 'hit_rate': 0.75, 'status': 'CANDIDATE'},
        {'peak': 17, 'center': 3503, 'center_bits': 12, 'hit_rate': 0.875, 'status': 'CANDIDATE'},
        {'peak': 20, 'center': 4763, 'center_bits': 13, 'hit_rate': 1.0, 'status': 'CONFIRMED'},
        {'peak': 28, 'center': 124463, 'center_bits': 17, 'hit_rate': 1.0, 'status': 'CONFIRMED'},
        {'peak': 29, 'center': 195923, 'center_bits': 18, 'hit_rate': 1.0, 'status': 'CONFIRMED'}
    ]
    
    # Let's write them to targeted_missing.csv
    with open('targeted_missing.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['peak', 'center', 'center_bits', 'hit_rate', 'status'])
        writer.writeheader()
        for p in new_points:
            writer.writerow(p)
            
    # Load all centers to recalculate formula
    files = ['confluence_census.csv', 'targeted_31_50.csv', 'targeted_41_50.csv', 'targeted_missing.csv']
    centers = []
    seen = set()
    for f in files:
        try:
            with open(f, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    c = int(row['center'])
                    p = int(row.get('peak', 0))
                    if p > 0 and c not in seen:
                        seen.add(c)
                        centers.append((p, c.bit_length()))
        except Exception as e:
            pass
            
    peaks = [x[0] for x in centers]
    bits = [x[1] for x in centers]
    
    slope, intercept, r_squared = linregress(peaks, bits)
    print(f"Total Unique Centers: {len(centers)}")
    print(f"Formula: center_bits = {slope:.6f} * peak + {intercept:.4f}")
    print(f"R^2 = {r_squared:.4f}")

if __name__ == "__main__":
    update_and_recalc()
