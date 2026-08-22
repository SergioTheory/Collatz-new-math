import csv

def get_centers(peaks):
    files = ['targeted_31_50.csv', 'targeted_41_50.csv', 'confluence_census.csv']
    centers = {}
    for f in files:
        try:
            with open(f, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    p = int(row.get('peak', 0))
                    if p in peaks:
                        hr = float(row.get('hit_rate', 0.0))
                        c = int(row['center'])
                        if p not in centers or hr > centers[p][1]:
                            centers[p] = (c, hr)
        except Exception as e:
            pass
    return {p: c for p, (c, hr) in centers.items()}

peaks_to_test = [35, 37, 41, 48, 49]
centers_map = get_centers(peaks_to_test)
for p in peaks_to_test:
    if p in centers_map:
        print(f"Peak {p}: {centers_map[p]}")
    else:
        print(f"Peak {p}: NOT FOUND")
