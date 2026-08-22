import random
import stage4b_instanton_1400 as s4

blocks_list, _ = s4.load_grammar('zone2_shifts.csv')
max_surv = 0

for _ in range(100):
    x = random.randint(1<<1399, (1<<1400)-1)
    if x % 2 == 0: x += 1
    
    surv = 0
    while True:
        valids = [b for b in blocks_list if s4.apply_block(x, b, 6) is not None]
        if not valids: break
        
        x = s4.apply_block(x, random.choice(valids), 6)
        surv += 6
        if surv >= 2500: break
        
    if surv > max_surv:
        max_surv = surv

print('Max survival over 100 random seeds:', max_surv)
