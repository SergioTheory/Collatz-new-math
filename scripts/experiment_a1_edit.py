import ast

with open(r'C:\Users\Admin\Documents\Collatz\data\zone2_shifts.csv', 'r') as f:
    line = f.readlines()[1]
zone2_shifts = ast.literal_eval(line.strip().split(',\"')[1].split('\"')[0])
core_shifts = zone2_shifts[-251:]

N = 4000
inv11 = pow(11, -1, 1 << N)
x = (-29 * inv11) % (1 << N)
shadow_shifts = []
for _ in range(251):
    x = 3*x + 1
    a = (x & -x).bit_length() - 1
    x >>= a
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

dist = edit_distance(core_shifts, shadow_shifts)
print(f"Edit distance: {dist}")
print(f"Percentage: {dist / 251 * 100:.2f}%")
