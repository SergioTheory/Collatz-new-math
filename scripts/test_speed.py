import time
import sys

def test_speed(M):
    mod_exact = 1 << (M + 1)
    inv3 = pow(3, -1, mod_exact)
    curr = (1 * inv3) % mod_exact
    
    t0 = time.time()
    inv3_d = inv3
    for d in range(1, M + 2):
        curr = (curr * inv3) % mod_exact
        inv3_d = (inv3_d * inv3) % mod_exact
        if d % 10000 == 0:
            print(f"Done {d}/{M}")
    t1 = time.time()
    print(f"Time for M={M}: {t1 - t0:.2f}s")

if __name__ == '__main__':
    test_speed(100000)
