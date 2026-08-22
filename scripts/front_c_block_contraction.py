#!/usr/bin/env python3
"""Non-autonomous Front-C block-transfer contraction diagnostic.

The cumulative-L transfer is time dependent; a stationary eigenvalue gap is not
the relevant object.  This script computes an upper-bound transfer factor
(T_a...T_{a+r-1} 1)(L) for typical start states L, with the NB(2,1/2) increment
law P(b)=(b-1)2^-b.  The b-tail is treated pessimistically with value 1.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def pb_table(bmax):
    vals=[(b,(b-1)*2.0**(-b)) for b in range(2,bmax+1)]
    return vals,1.0-sum(p for _,p in vals)


def is_white(n,j,Lprev,xi,eps):
    k=n-2*j+2; mod=3**k; inv2=(mod+1)//2
    r=((xi%mod)*pow(inv2,Lprev+2,mod))%mod
    return min(r,mod-r)>eps*mod


def nb_weights_at_j(j,Llo,Lhi):
    """Unnormalized exact law of L_{j-1} over requested integer window."""
    r=2*(j-1)
    if r==0: return {0:1.0}
    # Stable recurrence starting at l=r.
    p=2.0**(-r); out={}; l=r
    while l<=Lhi:
        if l>=Llo: out[l]=p
        p*=0.5*l/(l-r+1); l+=1
    z=sum(out.values())
    return {l:p/z for l,p in out.items()} if z else {}


def block_task(task):
    n,eps,xi,kind,a,r,sigma,bmax=task
    mu=4*(a-1); sd=2*math.sqrt(max(1,a-1))
    lo=max(0,math.floor(mu-sigma*sd)); hi=math.ceil(mu+sigma*sd)
    probs,tail=pb_table(bmax)
    # Enough room for every retained increment in r steps.
    Lmax=hi+bmax*r
    v=[1.0]*(Lmax+1)
    for j in range(a+r-1,a-1,-1):
        prev=[1.0]*(Lmax+1)
        max_needed=hi+bmax*(j-a)
        for L in range(0,max_needed+1):
            white=is_white(n,j,L,xi,eps)
            total=tail  # omitted b-tail bounded by 1
            for b,p in probs:
                w=math.exp(-(-math.log(math.cos(math.pi*eps)))) if (b==3 and white) else 1.0
                total+=p*w*v[L+b]
            prev[L]=total
        v=prev
    vals=v[lo:hi+1]
    weights=nb_weights_at_j(a,lo,hi)
    weighted=sum(weights.get(L,0.0)*v[L] for L in range(lo,hi+1))
    mx=max(vals); mn=min(vals)
    argmax_L=lo+vals.index(mx)
    argmin_L=lo+vals.index(mn)
    return {"n":n,"epsilon":eps,"kind":kind,"xi":xi,"block_start":a,"block_length":r,
            "sigma_window":sigma,"L_lo":lo,"L_hi":hi,"bmax":bmax,"b_tail":tail,
            "factor_max":mx,"factor_min":mn,"argmax_L":argmax_L,"argmin_L":argmin_L,
            "argmax_z":(argmax_L-mu)/sd,"argmax_window_probability":weights.get(argmax_L,0.0),
            "factor_NB_window":weighted,
            "rate_max_per_step":-math.log(mx)/r,
            "rate_NB_per_step":-math.log(weighted)/r}


def load_target(source,n,eps,kind):
    data=json.loads(source.read_text(encoding="utf-8")); R=next(x for x in data["results"] if x["n"]==n)
    row=next(x for x in R["rows"] if abs(x["epsilon"]-eps)<1e-15)
    rec=row["best_low_power"] if kind=="resonant" else row["best_random_unit"]
    s=row["best_low_power"]["low_s"]
    return rec["xi"],s


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ns",nargs="+",type=int,default=[200,400])
    ap.add_argument("--epsilons",nargs="+",type=float,default=[.05,.02])
    ap.add_argument("--lengths",nargs="+",type=int,default=[5,10,20])
    ap.add_argument("--sigmas",nargs="+",type=float,default=[2,4,6])
    ap.add_argument("--offset",type=float,default=.5)
    ap.add_argument("--bmax",type=int,default=60)
    ap.add_argument("--workers",type=int,default=min(30,os.cpu_count() or 1))
    ap.add_argument("--source",default="front_c_large_results.json")
    ap.add_argument("--out",default="front_c_block_contraction.json")
    args=ap.parse_args(); source=Path(args.source); tasks=[]
    for n in args.ns:
      for eps in args.epsilons:
       for kind in ("resonant","bulk_sample"):
        xi,s=load_target(source,n,eps,kind); first=math.ceil((s+2)/4+args.offset*math.sqrt(n)); end=n//2-math.ceil(math.log(n))
        for r in args.lengths:
         for a in range(first,end-r+2,r):
          for sigma in args.sigmas:
           tasks.append((n,eps,xi,kind,a,r,sigma,args.bmax))
    print(f"computing {len(tasks)} block operators on {args.workers} workers",flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results=list(pool.map(block_task,tasks,chunksize=1))
    # Aggregate worst conditional factor across post blocks.
    summaries=[]
    groups={}
    for x in results:
        key=(x["n"],x["epsilon"],x["kind"],x["block_length"],x["sigma_window"])
        groups.setdefault(key,[]).append(x)
    for key,rr in groups.items():
        n,eps,kind,r,sigma=key; worst=max(rr,key=lambda x:x["factor_max"]); avg_rate=sum(x["rate_NB_per_step"] for x in rr)/len(rr)
        eta=-math.log(math.cos(math.pi*eps)); iid=-math.log(1-.25*(1-2*eps)*(1-math.exp(-eta)))
        rec={"n":n,"epsilon":eps,"kind":kind,"block_length":r,"sigma_window":sigma,
             "block_count":len(rr),"worst_factor_max":worst["factor_max"],
             "worst_rate_max_per_step":worst["rate_max_per_step"],
             "worst_block_start":worst["block_start"],"mean_NB_rate_per_step":avg_rate,"iid_rate":iid}
        summaries.append(rec)
        print(f"n={n} eps={eps:g} {kind} r={r} sig={sigma:g} blocks={len(rr)} "
              f"maxfac={rec['worst_factor_max']:.8f} maxrate={rec['worst_rate_max_per_step']:.3g} "
              f"NBrate={avg_rate:.6g} iid={iid:.6g}",flush=True)
    Path(args.out).write_text(json.dumps({"params":vars(args),"summaries":summaries,"blocks":results},indent=2),encoding="utf-8")
    print(f"saved {args.out}")

if __name__=="__main__": main()
