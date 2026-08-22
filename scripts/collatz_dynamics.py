import math

def collatz_peak(n: int, max_steps: int = 2_000_000):
    cur = n
    peak_bits = n.bit_length()
    for k in range(max_steps):
        if cur % 2 == 0:
            while cur % 2 == 0: cur >>= 1
        if cur == 1: return peak_bits, k, True
        cur = 3 * cur + 1
        if cur.bit_length() > peak_bits: peak_bits = cur.bit_length()
        while cur % 2 == 0: cur >>= 1
        if cur.bit_length() > peak_bits: peak_bits = cur.bit_length()
    return peak_bits, max_steps, False

def analyze_to_peak(n: int, max_steps: int = 2_000_000):
    cur = n
    peak_bits = n.bit_length()
    peak_idx = 0
    shifts = []
    for k in range(max_steps):
        if cur % 2 == 0:
            while cur % 2 == 0: cur >>= 1
        if cur == 1: break
        cur = 3 * cur + 1
        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()
            peak_idx = len(shifts)  # The peak is reached AT the current shift
        a = 0
        while cur % 2 == 0:
            cur >>= 1
            a += 1
        shifts.append(a)
        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()
            peak_idx = len(shifts)
    d = peak_idx
    S = sum(shifts[:d])
    return {"n": n, "peak_bits": peak_bits, "d": d, "S": S, "shift_vector": shifts[:d]}
