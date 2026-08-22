import itertools

def check_words(M, d):
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
            naive_words[w] = naive_words.get(w, 0) + 1
            
    theory_words = {}
    for S in range(d, M + 1):
        spots = list(range(1, S))
        for combo in itertools.combinations(spots, d - 1):
            S_arr = [0] + list(combo) + [S]
            word = []
            for j in range(1, d + 1):
                word.append(S_arr[j] - S_arr[j-1])
            w = tuple(word)
            
            # The word should appear 2^{M - S} times in the naive simulation
            theory_words[w] = 1 << (M - S)
            
    # Compare
    all_w = set(naive_words.keys()).union(set(theory_words.keys()))
    mismatch = False
    for w in all_w:
        n_c = naive_words.get(w, 0)
        t_c = theory_words.get(w, 0)
        if n_c != t_c:
            print(f"Mismatch for word {w}: Naive count = {n_c}, Theory count = {t_c}")
            mismatch = True
            
    if not mismatch:
        print("All word counts match exactly!")

check_words(10, 5)
