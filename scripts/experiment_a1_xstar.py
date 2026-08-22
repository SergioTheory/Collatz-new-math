x = 20152090995747160937051
shifts = []
for _ in range(251):
    x = 3*x + 1
    a = (x & -x).bit_length() - 1
    x >>= a
    shifts.append(a)

N = 4000
inv11 = pow(11, -1, 1 << N)
x_shadow = (-29 * inv11) % (1 << N)
shadow_shifts = []
for _ in range(251):
    x_shadow = 3*x_shadow + 1
    a = (x_shadow & -x_shadow).bit_length() - 1
    x_shadow >>= a
    shadow_shifts.append(a)

def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
    return dp[m][n]

dist = edit_distance(shifts, shadow_shifts)
print(f"Edit distance: {dist}")

mismatches = sum(1 for i in range(251) if shifts[i] != shadow_shifts[i])
print(f"Rigid mismatches: {mismatches} ({mismatches/251*100:.2f}%)")

print("X* shifts:", shifts[:20])
print("Shadow shifts:", shadow_shifts[:20])
