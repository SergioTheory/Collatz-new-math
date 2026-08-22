import itertools

def check_rw(M, d):
    K = 1 << M
    naive_words = {}
    
    for z in range(K):
        N = 2 * z + 1
        curr = N
        S = 0
        word = []
        for step in range(1, d + 1):
            curr = 3 * curr + 1
            a = 0
            while curr % 2 == 0:
                a += 1
                curr //= 2
            word.append(a)
            S += a
        
        if S <= M:
            w = tuple(word)
            if w not in naive_words:
                naive_words[w] = z % (1 << S)
            else:
                if naive_words[w] != z % (1 << S):
                    print(f"Error! Word {w} has multiple residues: {naive_words[w]} and {z % (1<<S)}")
            
    theory_words = {}
    for S in range(d, M + 1):
        spots = list(range(1, S))
        for combo in itertools.combinations(spots, d - 1):
            S_arr = [0] + list(combo) + [S]
            word = []
            for j in range(1, d + 1):
                word.append(S_arr[j] - S_arr[j-1])
            w = tuple(word)
            
            mod_exact = 1 << (S + 1)
            inv3_d = pow(3, -d, mod_exact)
            c_w = 0
            for j in range(1, d + 1):
                c_w += (3**(d - j)) * (1 << S_arr[j-1])
            rho_w = (( (1 << S) - c_w ) * inv3_d) % mod_exact
            if rho_w % 2 == 0:
                rho_w += mod_exact
            r_w = (rho_w - 1) // 2
            
            theory_words[w] = r_w
            
    # Compare
    for w in theory_words:
        if w in naive_words:
            if theory_words[w] != naive_words[w]:
                print(f"Mismatch for word {w}: Naive r_w = {naive_words[w]}, Theory r_w = {theory_words[w]}")
                return
    print("All r_w match exactly!")

check_rw(10, 5)
