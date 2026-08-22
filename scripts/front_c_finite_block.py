#!/usr/bin/env python3
"""Finite-b block calibration for the weighted r-step inequality."""
from __future__ import annotations
import argparse, json, math, os
from concurrent.futures import ProcessPoolExecutor
from front_c_weight_test import V, is_white
from front_c_adversarial import nb_support


def pb(b): return (b-1)*2.0**(-b)

def finite_block(task):
    n,eps,xi,j,r,alpha,B,sigma=task
    mu=4*(j-1); sd=2*math.sqrt(max(1,j-1))
    lo=max(0,math.floor(mu-sigma*sd)); hi=math.ceil(mu+sigma*sd)
    Lmax=hi+B*r+2
    v=[V(j+r,L,alpha) for L in range(Lmax+1)]
    for t in range(r-1,-1,-1):
        jj=j+t; prev=[1.0]*(Lmax+1)
        for L in range(0,hi+B*t+1):
            white=is_white(n,jj,L,xi,eps)
            total=0.0
            for b in range(2,B+1):
                w=math.exp(-(-math.log(math.cos(math.pi*eps)))) if b==3 and white else 1.0
                total += pb(b)*w*v[L+b]
            prev[L]=total
        v=prev
    ratios=[(v[L]/V(j,L,alpha),L) for L in range(lo,hi+1)]
    mx,Lmx=max(ratios); mn,Lmn=min(ratios)
    weights=nb_support(j,1e-14)
    wdict=dict(weights); avg=sum(wdict.get(L,0)*v[L]/V(j,L,alpha) for L in range(lo,hi+1))
    q=2**(-(1-alpha)); tail=q**(B+1)*(B/(1-q)+q/(1-q)**2)
    return {"j":j,"r":r,"alpha":alpha,"B":B,"sigma":sigma,"Llo":lo,"Lhi":hi,
            "finite_sup":mx,"argmax_L":Lmx,"argmax_z":(Lmx-mu)/sd,
            "finite_inf":mn,"NB_avg":avg,"tail_bound_relative":tail,
            "full_sup_bound":mx+tail,"target_c_1e3":math.exp(-.001*r),
            "finite_rate_sup":-math.log(mx)/r,"full_bound_rate":-math.log(mx+tail)/r}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1)); ap.add_argument('--out',default='front_c_finite_block.json'); args=ap.parse_args()
    n=400; eps=.05; xi=pow(2,629,3**n)
    jobs=[(n,eps,xi,j,5,alpha,B,6) for j in (168,173,178,183,188)
          for alpha in (.05,.1,.2,.3,.5) for B in (20,40,60)]
    with ProcessPoolExecutor(max_workers=args.workers) as pool: out=list(pool.map(finite_block,jobs))
    for x in out: print('j=%d alpha=%.2f B=%d finite=%.9f full<=%.9f target=%.9f z=%.2f tail=%.3g'%(x['j'],x['alpha'],x['B'],x['finite_sup'],x['full_sup_bound'],x['target_c_1e3'],x['argmax_z'],x['tail_bound_relative']),flush=True)
    import pathlib; pathlib.Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')

if __name__=='__main__': main()
