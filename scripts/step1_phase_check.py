import math

def theta_real(j, l, xi, n):
    # Real phase: xi * 3^(2j) * 2^(-l) mod 1
    # Note: 2^(-l) is extremely small, so we use float or Decimal if needed,
    # but for small j,l float is fine. Actually, for large j, 3^(2j) is large, 2^(-l) is small.
    # To avoid overflow, we can compute it using floating point.
    val = xi * (3**(2*j)) * (2.0**(-l))
    return val % 1.0

def theta_mod(j, l, xi, n):
    # Modular phase: (xi * 3^(2j-2) * (2^(-(l-1)) mod 3^n)) / 3^n mod 1
    # Modular inverse of 2^(l-1) mod 3^n
    modulus = 3**n
    try:
        inv_2 = pow(2, -(l-1), modulus)
    except ValueError:
        # If l-1 is negative, pow handles it in Python 3.8+ for modular inverse
        # Wait, pow(base, exp, mod) where exp < 0 computes modular inverse of base, then raises to |exp|.
        # Let's ensure l >= 1
        inv_2 = pow(2, - (l - 1), modulus)
    
    numerator = xi * (3**(2*j - 2)) * inv_2
    val = (numerator / modulus) % 1.0
    return val

def main():
    n = 10
    xi = 1
    
    print(f"Comparing phases for n={n}, xi={xi} along trajectory l = 4j\n")
    print(f"{'j':<5} {'l':<5} | {'theta_real':<20} | {'theta_mod':<20}")
    print("-" * 55)
    
    for j in range(1, 21):
        l = 4 * j
        t_r = theta_real(j, l, xi, n)
        t_m = theta_mod(j, l, xi, n)
        print(f"{j:<5} {l:<5} | {t_r:<20.6f} | {t_m:<20.6f}")

    # Let's also do a 2D map for j in 1..20, l in 1..80
    print("\n--- Black Triangles Map (theta < 0.05 or theta > 0.95) ---")
    
    print("\nReal Phase (theta_real):")
    for j in range(1, 16):
        row = []
        for l in range(1, 61):
            t_r = theta_real(j, l, xi, n)
            if t_r < 0.05 or t_r > 0.95:
                row.append("X") # Black
            else:
                row.append(".") # White
        print(f"j={j:<2} " + "".join(row))

    print("\nModular Phase (theta_mod):")
    for j in range(1, 16):
        row = []
        for l in range(1, 61):
            t_m = theta_mod(j, l, xi, n)
            if t_m < 0.05 or t_m > 0.95:
                row.append("X") # Black
            else:
                row.append(".") # White
        print(f"j={j:<2} " + "".join(row))

if __name__ == '__main__':
    main()
