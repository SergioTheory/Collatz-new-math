import random
import math
from collections import defaultdict, Counter

def make_block(shifts):
    S = 0
    c = 0
    for a in shifts:
        c = 3 * c + (1 << S)
        S += a
    return (S, len(shifts), c)

def reverse_block(x, blk):
    y = (x << blk[0]) - blk[2]
    for _ in range(blk[1]):
        if y % 3 != 0: return None
        y //= 3
    return y if (y & 1) else None

def test():
    # just test one macro step on one seed
    seed = ( (1<<139) - 1 ) // 3 + 1
    if seed % 4 != 3: seed += (3 - seed % 4)
    x = seed
    
    blk = make_block([2, 1, 1]*10)
    print("Block:", blk)
    y = reverse_block(x, blk)
    print("Reverse:", y is not None)

test()
