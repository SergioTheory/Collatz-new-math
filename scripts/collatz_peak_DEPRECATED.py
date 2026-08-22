import math

def collatz_peak(n: int, max_steps: int = 2_000_000):
    """
    Поиск глобального пика через ускоренную динамику Коллатца.
    Возвращает (peak_bits, peak_idx, converged)
    """
    cur = n
    peak_bits = n.bit_length()
    peak_idx = 0
    
    for k in range(max_steps):
        # Если число чётное, сначала делаем его нечётным (хотя обычно на вход подают нечётные)
        if cur % 2 == 0:
            while cur % 2 == 0:
                cur >>= 1
        
        if cur == 1:
            return peak_bits, peak_idx, True
            
        cur = 3 * cur + 1
        a = 0
        while cur % 2 == 0:
            cur >>= 1
            a += 1
            
        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()
            peak_idx = k + 1  # Индекс шага, на котором достигнут пик
            
        if cur == 1:
            return peak_bits, peak_idx, True
            
    return peak_bits, peak_idx, False

def analyze_to_peak(n: int, max_steps: int = 2_000_000):
    """
    Возвращает полную статистику до глобального пика.
    """
    cur = n
    peak_bits = n.bit_length()
    peak_idx = 0
    shifts = []
    
    for k in range(max_steps):
        if cur % 2 == 0:
            while cur % 2 == 0:
                cur >>= 1
                
        if cur == 1:
            break
            
        cur = 3 * cur + 1
        a = 0
        while cur % 2 == 0:
            cur >>= 1
            a += 1
        shifts.append(a)
        
        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()
            peak_idx = len(shifts)
            
    d = peak_idx
    shifts_to_peak = shifts[:d]
    S = sum(shifts_to_peak)
    S_over_d = S / d if d > 0 else 0.0
    gain = d * math.log2(3) - S
    
    return {
        "n": n,
        "peak_bits": peak_bits,
        "d": d,
        "S": S,
        "S_over_d": S_over_d,
        "shift_vector": shifts_to_peak,
        "gain": gain
    }
