import json

with open('extra_seeds.json') as f:
    data = json.load(f)

print("# Добавить в PATH_RECORDS_BINARY (Zone 3 и выше)")
for seed in data['seeds']:
    bits = seed['bits']
    peak = seed['peak_bits']
    if peak >= 233:
        binary = seed['binary']
        ratio = peak / bits
        print(f'    "{binary}",  # {bits} бит, peak={peak}, ratio={ratio:.5f} (Zone 3/4)')