import ast
import stage4a_instanton_validate as s4

blocks, _, _ = s4.load_grammar('zone2_shifts.csv')
x = 329409787129088108212379710537829645932061

valids = 0
for b in blocks:
    if s4.apply_block(x, b, 6) is not None:
        valids += 1
print('Total unique blocks:', len(blocks))
print('Valid blocks from peak:', valids)
