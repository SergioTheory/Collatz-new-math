#!/usr/bin/env python3
"""Diagnostic for a Cramer-rate Lyapunov weight in the non-autonomous operator."""
from __future__ import annotations
import argparse, json, math, os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def p_b(b): return (b-1)*2.0**(-b)

def rate_geom_sum(L,r):
    # Sum of r Geom(1/2) variables on {1,2,...}; Cramer rate per summand.
    if r<=0: return 0.0
    x=max(1.0,L/r)
    # Lambda(t)=t-log(2-exp(t)); optimizer exp(t)=2*x/(x+1)
    if x<=1.0: return math.log(2.0)
    t=math.log(2.0*(x-1.0)/x)
    lam=t-math.log(2-math.exp(t))
    return t*x-lam

def V(j,L,alpha):
    r=2*(j-1)
    if r==0: return 1.0
    # For unreachable L<r, retain a finite diagnostic value.
    if L<r: return 1.0
    return math.exp(alpha*r*rate_geom_sum(L,r))

def is_white(n,j,L,xi,eps):
    k=n-2*j+2; mod=3**k; inv2=(mod+1)//2
    z=((xi%mod)*pow(inv2,L+2,mod))%mod
    return min(z,mod-z)>eps*mod

def task(x):
    n,eps,xi,a,r,alpha,bmax=x
    # Evaluate states over a broad 6-sigma window at the block start.
    mu=4*(a-1); sd=2*math.sqrt(max(1,a-1))
    lo=max(0,math.floor(mu-6*sd)); hi=math.ceil(mu+6*sd)
    Lmax=hi+bmax*r+5
    v=[V(a+r,L,alpha) for L in range(Lmax+1)]
    tail=1-sum(p_b(b) for b in range(2,bmax+1))
    for j in range(a+r-1,a-1,-1):
        prev=[1.0]*(Lmax+1)
        for L in range(0,hi+bmax*(j-a)+1):
            white=is_white(n,j,L,xi,eps)
            total=tail*V(j+1,L+bmax+1,alpha) # rough upper-tail representative
            for b in range(2,bmax+1):
                weight=math.exp(-(-math.log(math.cos(math.pi*eps)))) if b==3 and white else 1.0
                total+=p_b(b)*weight*v[L+b]
            prev[L]=total
        v=prev
    ratios=[]
    for L in range(lo,hi+1):
        denom=V(a,L,alpha)
        ratios.append((v[L]/denom,L))
    mx,Lmx=max(ratios); mn,Lmn=min(ratios)
    return {"n":n,"epsilon":eps,"xi":xi,"start":a,"length":r,"alpha":alpha,
            "max_ratio":mx,"argmax_L":Lmx,"argmax_z":(Lmx-mu)/sd,
            "min_ratio":mn,"argmin_L":Lmn,"rate_max":-math.log(mx)/r}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1)); ap.add_argument('--out',default='front_c_weight_test.json'); args=ap.parse_args()
    # n=400 resonant post blocks, plus alpha sweep
    n=400; eps=.05; xi=pow(2,629,3**n)
    jobs=[(n,eps,xi,a,r,alpha,100) for a,r in ((168,5),(168,10),(168,20),(178,10),(188,10)) for alpha in (.05,.1,.2,.4,.6)]
    with ProcessPoolExecutor(max_workers=args.workers) as pool: out=list(pool.map(task,jobs))
    for x in out: print('a=%d r=%d alpha=%.2f max=%.9f rate=%.3g L=%d z=%.2f'%(x['start'],x['length'],x['alpha'],x['max_ratio'],x['rate_max'],x['argmax_L'],x['argmax_z']),flush=True)
    Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')

if __name__=='__main__': main()
