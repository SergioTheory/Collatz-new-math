import ast
import stage4a_instanton_validate as s4

blocks, _, _ = s4.load_grammar('zone2_shifts.csv')
x = 329409787129088108212379710537829645932061

req_parity = 0 if x % 3 == 1 else 1
first_match = [b for b in blocks if b[0] % 2 == req_parity]
fully_valid = [b for b in blocks if s4.apply_block(x, b, 6) is not None]

print('Total blocks:', len(blocks))
print('Blocks matching first parity:', len(first_match))
print('Blocks fully valid:', len(fully_valid))
