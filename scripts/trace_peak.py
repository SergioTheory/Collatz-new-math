def trace_peak():
    x_star = 20152090995747160937051
    curr = x_star
    peak = curr
    peak_odd_steps = 0
    odd_steps = 0
    shifts = []
    while curr > 1:
        if curr % 2 != 0:
            curr = 3*curr + 1
            a = (curr & -curr).bit_length() - 1
            shifts.append(a)
            curr >>= a
            odd_steps += 1
            if curr > peak: 
                peak = curr
                peak_odd_steps = odd_steps
        else:
            curr //= 2
    
    print(f"Peak: {peak}")
    print(f"Total odd steps: {odd_steps}")
    print(f"Odd steps to peak: {peak_odd_steps}")
    
    # Check phases from peak
    shifts_to_peak = shifts[:peak_odd_steps]
    dips = []
    for i, a in enumerate(shifts_to_peak):
        if a >= 3:
            dist_from_peak = peak_odd_steps - 1 - i
            phase = dist_from_peak % 18
            dips.append(phase)
    
    from collections import Counter
    print("Dips phases mod 18:", Counter(dips))

trace_peak()
