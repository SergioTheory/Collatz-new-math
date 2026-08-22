from crt_solver import collatz_peak

def extract_shifts(n, max_steps=2_000_000):
    """Извлекает shift-вектор (количество делений на 2 после каждого 3n+1)"""
    cur = n
    shifts = []
    for _ in range(max_steps):
        if cur <= 1:
            break
        if cur & 1:
            cur = cur * 3 + 1
            count = 0
            while cur > 1 and cur % 2 == 0:
                cur >>= 1
                count += 1
            shifts.append(count)
        else:
            # Если начинаем с чётного — просто делим (но в Zone 2 числа нечётные, так что не нужно)
            while cur > 1 and cur % 2 == 0:
                cur >>= 1
    return shifts

def common_prefix(a, b):
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))

n_orig = 20152090995747160937051
bits_orig = n_orig.bit_length()
shifts_orig = extract_shifts(n_orig)
peak_orig, _, _ = collatz_peak(n_orig)

print(f"Оригинал: bits={bits_orig}, peak={peak_orig}, d={len(shifts_orig)}")
print(f"Первые 20 сдвигов: {shifts_orig[:20]}")

print("\n=== Инверсия бит в Zone 2 числе ===")
for bit_pos in range(5, bits_orig, 5):
    n_mut = n_orig ^ (1 << bit_pos)
    # Убедимся, что число остаётся нечётным (иначе траектория изменится)
    if n_mut % 2 == 0:
        n_mut |= 1
    bits = n_mut.bit_length()
    peak, _, _ = collatz_peak(n_mut)
    shifts_mut = extract_shifts(n_mut)
    cp = common_prefix(shifts_orig, shifts_mut)
    print(f"  бит {bit_pos:2d}: bits={bits}, peak={peak}, d={len(shifts_mut)}, common_prefix={cp}/{len(shifts_orig)}")