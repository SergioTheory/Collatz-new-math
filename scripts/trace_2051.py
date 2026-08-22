def trace(n):
    x = int(n)
    m = x
    c = 0
    while x > 1:
        if x % 2 != 0:
            x = 3*x + 1
            if x > m: m = x
        else:
            x //= 2
        c += 1
        if c > 1000: break
    print(f"Max value for {n}: {m.bit_length()} bits, {m}")

trace(2051)
trace(35)
