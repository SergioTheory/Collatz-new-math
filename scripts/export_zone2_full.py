import json, csv

def ctz(y): return (y & -y).bit_length() - 1

def shift_vector_to_peak(n, margin=40, cap=5000):
    """Shift-вектор строго до пика (even spike включён)."""
    x = int(n); best = 0; best_i = -1; shifts = []
    for i in range(cap):
        y = 3 * x + 1
        a = ctz(y)
        shifts.append(a)
        if y > best:
            best, best_i = y, i
        x = y >> a
        # спустились на margin бит ниже пика — пик точно позади
        if best.bit_length() - x.bit_length() > margin:
            break
    return shifts[:best_i + 1], best

def main(src="expand_913.json", dst="zone2_shifts_full.csv"):
    raw = json.load(open(src))
    rows, bad = [], 0
    for d in raw:
        n = int(str(d.get("n", d.get("n "))).strip())
        shifts, peak = shift_vector_to_peak(n)
        bits, pbits = n.bit_length(), peak.bit_length()
        if pbits != 140: bad += 1
        dd, S = len(shifts), sum(shifts)
        rows.append([n, bits, pbits, dd, S, S / dd,
                     dd * 1.5849625007211562 - S, shifts])
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "bits", "peak_bits", "d", "S", "S_d", "gain", "blocks"])
        w.writerows(rows)
    print(f"saved {len(rows)}; peak!=140: {bad}")
    # sanity: d и S должны совпасть с инвариантами статьи
    ds = {r[3] for r in rows}
    print("unique d:", ds, "| S==bits+271:", all(r[4] == r[1] + 271 for r in rows))

if __name__ == "__main__":
    main()
