#!/usr/bin/env python3
"""One-step Cramer-weight drift diagnostic with a long, untruncated b sum."""
from __future__ import annotations
import argparse, json, math, os
from concurrent.futures import ProcessPoolExecutor
from front_c_weight_test import V, is_white
from front_c_adversarial import nb_support


def pb(b): return (b-1)*2.0**(-b)

def one(task):
    n,eps,xi,j,alpha,z,bmax=task
    mu=4*(j-1); sd=2*math.sqrt(max(1,j-1)); L=round(mu+z*sd)
    denom=V(j,L,alpha); total=0.0
    for b in range(2,bmax+1):
        w=math.exp(-(-math.log(math.cos(math.pi*eps)))) if b==3 and is_white(n,j,L,xi,eps) else 1.0
        total += pb(b)*w*V(j+1,L+b,alpha)
    tailprob=sum(pb(b) for b in range(bmax+1, bmax+1000))
    ratio=total/denom
    return {"j":j,"alpha":alpha,"z":z,"L":L,"ratio":ratio,
            "rate":-math.log(ratio),"tailprob_after_bmax":tailprob,"bmax":bmax}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1)); ap.add_argument('--out',default='front_c_one_step.json'); args=ap.parse_args()
    n=400; eps=.05; xi=pow(2,629,3**n)
    jobs=[(n,eps,xi,j,a,z,1000) for j in (168,178,188) for a in (.02,.05,.1,.2,.4) for z in (-4,-2,0,2,4)]
    with ProcessPoolExecutor(max_workers=args.workers) as pool: out=list(pool.map(one,jobs))
    for x in out: print('j=%d alpha=%.2f z=%+.0f R=%.9f rate=%+.6g'%(x['j'],x['alpha'],x['z'],x['ratio'],x['rate']),flush=True)
    import pathlib; pathlib.Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')

if __name__=='__main__': main()
