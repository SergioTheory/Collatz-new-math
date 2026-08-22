def check_cw():
    d = 3
    S_arr = [0, 1, 3, 5]  # a1=1, a2=2, a3=2
    # simulate
    c = 0
    for i in range(1, d+1):
        c = 3 * c + (1 << S_arr[i-1])
    
    # formula
    c_w = 0
    for j in range(1, d + 1):
        c_w += (3**(d - j)) * (1 << S_arr[j-1])
        
    print(f"c={c}, c_w={c_w}")

check_cw()
