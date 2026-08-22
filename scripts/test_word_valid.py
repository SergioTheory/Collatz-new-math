def test_word_validity():
    M = 10
    d = 5
    S = 10
    mod_exact = 1 << (S + 1)
    inv3_d = pow(3, -d, mod_exact)
    
    # Just take one composition
    w = (1, 2, 2, 2, 3) # Sum = 10
    S_arr = [0, 1, 3, 5, 7, 10]
    
    c_w = 0
    for j in range(1, d + 1):
        c_w += (3**(d - j)) * (1 << S_arr[j-1])
        
    rho_w = (( (1 << S) - c_w ) * inv3_d) % mod_exact
    if rho_w % 2 == 0:
        rho_w += mod_exact
        
    print(f"Testing word {w}, rho_w = {rho_w}")
    
    # Simulate
    curr = rho_w
    word_sim = []
    for step in range(1, d + 1):
        curr = 3 * curr + 1
        a = 0
        while curr % 2 == 0:
            a += 1
            curr //= 2
        word_sim.append(a)
        
    print(f"Simulated word = {tuple(word_sim)}")

test_word_validity()
