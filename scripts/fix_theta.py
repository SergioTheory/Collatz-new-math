import sys
for file in ['renewal_white_point_analysis.py', 'polymer_free_energy.py']:
    with open(file, 'r', encoding='utf8') as f:
        content = f.read()
    
    def replacement(m):
        return """def compute_theta(self, j, l):
        j, l = int(j), int(l)
        # We need the fractional part of 2^{s-l+1} / 3^{n-2j+2}
        power = self.n - 2*j + 2
        if power <= 0:
            return 0.0 # It's an integer
        mod = 3**power
        num = pow(2, self.s - l + 1, mod)
        theta = num / mod
        if theta > 0.5:
            theta -= 1.0
        return theta"""
    import re
    content = re.sub(r'def compute_theta\(self, j, l\):.*?return self\.theta_cache\[key\]', replacement(None), content, flags=re.DOTALL)
    
    # Also fix the standalone one
    def replacement2(m):
        return """def compute_theta(j, l, s, n):
    j, l, s, n = int(j), int(l), int(s), int(n)
    power = n - 2*j + 2
    if power <= 0:
        return 0.0
    mod = 3**power
    num = pow(2, s - l + 1, mod)
    theta = num / mod
    if theta > 0.5:
        theta -= 1.0
    return theta"""
    content = re.sub(r'def compute_theta\(j, l, s, n\):.*?return theta', replacement2(None), content, flags=re.DOTALL)
    
    with open(file, 'w', encoding='utf8') as f:
        f.write(content)
