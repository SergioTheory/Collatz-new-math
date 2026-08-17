import numpy as np

def ifs_dist(n, a_max=60):
    """Exact IFS distribution p_n on Z/3^n (length 3^n)."""
    probs = {0: 1.0}
    for m in range(1, n + 1):
        p3 = 3 ** m
        inv2 = (p3 + 1) // 2
        new = {}
        for x, w in probs.items():
            base = (3 * x + 1) % p3
            for a in range(1, a_max + 1):
                y = (base * pow(inv2, a, p3)) % p3
                new[y] = new.get(y, 0.0) + w * 2 ** (-a)
        probs = new
    arr = np.zeros(3 ** n)
    for x, w in probs.items():
        arr[x] = w
    return arr

def order2mod3(n):
    """multiplicative order of 2 mod 3^n = 2*3^(n-1)."""
    return 2 * 3 ** (n - 1)

print("n | ord(2) | mass_orbit | mass_total(3^n*sum p^2) | mass_units(3-nondiv) | ratio_orbit/total | ratio_orbit/units")
for n in range(1, 14):
    p = ifs_dist(n)
    p3 = 3 ** n
    # full spectral mass
    mu = np.fft.fft(p)  # mu[xi] = sum_x p(x) e^{-2pi i xi x/3^n}, unnormalized
    mass_total = 3 ** n * np.sum(p ** 2)
    mass_from_fft = np.sum(np.abs(mu) ** 2)
    assert abs(mass_total - mass_from_fft) < 1e-9 * mass_total, (n, mass_total, mass_from_fft)
    # units: xi with 3-nondiv
    idx = np.arange(p3)
    unit_idx = idx[idx % 3 != 0]
    mass_units = np.sum(np.abs(mu[unit_idx]) ** 2)
    # orbit of 2 mod 3^n: s=0..ord-1, xi = 2^s mod 3^n (distinct)
    ord2 = order2mod3(n)
    xi = 1
    s = 0
    orbit = []
    seen = set()
    while True:
        if xi in seen:
            break
        seen.add(xi)
        orbit.append(xi)
        xi = (xi * 2) % p3
        s += 1
    assert len(orbit) == ord2, (n, len(orbit), ord2)
    mass_orbit = np.sum(np.abs(mu[np.array(orbit)]) ** 2)
    print(f"n={n:2d} | {ord2:9d} | {mass_orbit:.6e} | {mass_total:.6e} | {mass_units:.6e} | {mass_orbit/mass_total:.3e} | {mass_orbit/mass_units:.3e}")
