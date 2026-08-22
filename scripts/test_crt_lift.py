import csv

def get_shift_vector_zone2():
    with open('zone2_shifts.csv', 'r') as f:
        reader = csv.DictReader(f)
        row = next(reader)
        shifts_str = row['blocks'].strip('[]')
        w = [int(x) for x in shifts_str.split(',')]
        return w[:251]

def get_shift_vector_sim(n, max_d):
    w = []
    cur = n
    d = 0
    while cur % 2 == 0:
        cur //= 2
    
    while d < max_d:
        cur = cur * 3 + 1
        shift = 0
        while cur % 2 == 0:
            cur //= 2
            shift += 1
        w.append(shift)
        d += 1
    return w

def collatz_peak(n):
    pb = n.bit_length()
    cur = n
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
        else:
            cur = cur // 2
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb

def crt_lift(w, name):
    d = len(w)
    S = sum(w)
    print(f"[{name}] d = {d}, S = {S}")
    
    c_d = 0
    current_S = 0
    for i in range(d):
        c_d += (3**(d - 1 - i)) * (2**current_S)
        current_S += w[i]
        
    mod = 1 << (2 * S)
    inv = pow(3**d - (1 << S), -1, mod)
    x0 = (-c_d * inv) % mod
    
    w_expected = w + w
    w2 = get_shift_vector_sim(x0, 2*d)
    
    # If the last parity is even instead of odd, we add 2^{2S}
    if w2[-1] != w_expected[-1]:
        x0 += mod
        w2 = get_shift_vector_sim(x0, 2*d)
        
    if w2[-1] != w_expected[-1]:
        # Still not odd? Try adding another mod
        x0 += mod
        w2 = get_shift_vector_sim(x0, 2*d)
        
    if w2 == w_expected:
        print(f"[{name}] SUCCESS: shift vector matches w^2 exactly!")
        peak = collatz_peak(x0)
        ratio = peak / (2 * S)
        print(f"[{name}] Peak: {peak} bits")
        print(f"[{name}] Ratio: {ratio:.4f}")
    else:
        print(f"[{name}] FAILURE: shift vector does not match w^2.")
        for i in range(len(w_expected)):
            if w2[i] != w_expected[i]:
                print(f"[{name}] Diff at {i}: got {w2[i]} vs expected {w_expected[i]}")
                break
        
    print("-" * 50)

def main():
    w_zone2 = get_shift_vector_zone2()
    crt_lift(w_zone2, "Zone 2 Core")
    
    n_barina = 1765856170146672440559
    w_barina = get_shift_vector_sim(n_barina, 213)
    crt_lift(w_barina, "Barina")

if __name__ == "__main__":
    main()
