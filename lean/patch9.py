p = r'C:\Users\Admin\Documents\Collatz_NewMath\lean\CollatzLean\LemmaT1_step1_pure.lean'
s = open(p, encoding='utf-8').read()
old = \"  have hk : p % (2 * n) + 2 * K = q % (2 * n) + 2 * n := by omega\"
new = \"  have hk : p % (2 * n) + 2 * K = q % (2 * n) + 2 * n := linarith [hD, hK]\"
assert old in s
s = s.replace(old, new)
open(p,'w',encoding='utf-8').write(s)
print(\"patched v9 OK\")
