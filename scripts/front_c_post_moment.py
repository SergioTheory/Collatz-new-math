#!/usr/bin/env python3
"""Monte-Carlo calibration of the post-resonance white-point moment.

Uses exact modular phases and the conditioned renewal event b_j=3.  For each
frequency, epsilon and finite-n offset A*sqrt(n), it measures moments on
  j_start=ceil((s+2)/4 + A*sqrt(n)), j_end=n/2-r.
This is finite-n calibration, not a proof of post-resonance mixing.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def is_white(n, j, l_prev, xi, eps):
    k = n - 2*j + 2
    mod = 3 ** k
    inv2 = (mod + 1) // 2
    r = ((xi % mod) * pow(inv2, l_prev + 2, mod)) % mod
    return min(r, mod-r) > eps * mod


def simulate_chunk(task):
    n, xi, eps, paths, seed, offsets, cutoffs = task
    rng = random.Random(seed)
    eta_cos = -math.log(math.cos(math.pi*eps))
    eta_eps3 = eps**3
    s_meta = task[-1] if False else None
    # starts are supplied through offsets as absolute (label,start); cutoffs (label,end)
    keys = [(ol, start, cl, end) for ol, start in offsets for cl, end in cutoffs if start <= end]
    acc = {f"{ol}|{cl}": {"sum_N":0.0, "sum_cos":0.0, "sum_eps3":0.0,
                            "zero":0, "paths":0, "start":start, "end":end}
           for ol,start,cl,end in keys}
    max_j = n//2
    for _ in range(paths):
        L = 0
        white_prefix = [0]*(max_j+1)
        for j in range(1,max_j+1):
            b=0
            for _ in range(2):
                a=1
                while rng.random()<0.5:
                    a+=1
                b+=a
            L+=b
            w=1 if b==3 and is_white(n,j,L-3,xi,eps) else 0
            white_prefix[j]=white_prefix[j-1]+w
        for ol,start,cl,end in keys:
            N=white_prefix[end]-white_prefix[start-1]
            a=acc[f"{ol}|{cl}"]
            a["sum_N"]+=N; a["sum_cos"]+=math.exp(-eta_cos*N)
            a["sum_eps3"]+=math.exp(-eta_eps3*N); a["zero"]+=(N==0); a["paths"]+=1
    return acc


def merge(parts,n,eps):
    out={}
    eta_cos=-math.log(math.cos(math.pi*eps)); eta_eps3=eps**3
    for part in parts:
        for key,a in part.items():
            if key not in out:
                out[key]={k:a[k] for k in ("start","end")}
                out[key].update(sum_N=0.0,sum_cos=0.0,sum_eps3=0.0,zero=0,paths=0)
            for k in ("sum_N","sum_cos","sum_eps3","zero","paths"):
                out[key][k]+=a[k]
    for a in out.values():
        P=a["paths"]; length=a["end"]-a["start"]+1
        a["window_length"]=length; a["mean_Nwhite"]=a.pop("sum_N")/P
        a["moment_eta_cos"]=a.pop("sum_cos")/P; a["moment_eta_eps3"]=a.pop("sum_eps3")/P
        a["zero_fraction"]=a.pop("zero")/P
        a["eta_cos"]=eta_cos; a["eta_eps3"]=eta_eps3
        a["rate_cos_per_n"]=-math.log(a["moment_eta_cos"])/n
        a["rate_cos_per_window"]=-math.log(a["moment_eta_cos"])/length
        a["rate_eps3_per_n"]=-math.log(a["moment_eta_eps3"])/n
        a["rate_eps3_per_window"]=-math.log(a["moment_eta_eps3"])/length
    return out


def load_rows(path,n):
    data=json.loads(path.read_text(encoding="utf-8"))
    return next(r for r in data["results"] if r["n"]==n)["rows"]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ns",nargs="+",type=int,default=[200,400])
    ap.add_argument("--epsilons",nargs="+",type=float,default=[.1,.05,.02,.01])
    ap.add_argument("--offsets",nargs="+",type=float,default=[0,.5,1.0])
    ap.add_argument("--paths",type=int,default=30000)
    ap.add_argument("--workers",type=int,default=min(30,os.cpu_count() or 1))
    ap.add_argument("--source",default="front_c_large_results.json")
    ap.add_argument("--out",default="front_c_post_moments.json")
    args=ap.parse_args(); source=Path(args.source)
    jobs=[]; meta=[]
    for n in args.ns:
        rows=load_rows(source,n)
        for eps in args.epsilons:
            row=next(r for r in rows if abs(r["epsilon"]-eps)<1e-15)
            for kind,rec in (("resonant",row["best_low_power"]),("bulk_sample",row["best_random_unit"])):
                s=rec["low_s"] if rec["low_s"] is not None else row["best_low_power"]["low_s"]
                jc=(s+2)/4
                offsets=[(f"A={A:g}",max(1,math.ceil(jc+A*math.sqrt(n)))) for A in args.offsets]
                cutoffs=[("r=0",n//2),("r=logn",n//2-math.ceil(math.log(n)))]
                chunks=[args.paths//args.workers+(i<args.paths%args.workers) for i in range(args.workers)]
                tasks=[(n,rec["xi"],eps,p,1000000*n+10000*round(eps*1000)+i,offsets,cutoffs)
                       for i,p in enumerate(chunks) if p]
                jobs.append((n,eps,kind,s,jc,tasks))
    results=[]
    # Run one configuration at a time, using all workers; avoids nested process pools.
    for n,eps,kind,s,jc,tasks in jobs:
        print(f"n={n} eps={eps:g} {kind} s={s} jc={jc:.2f}",flush=True)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            parts=list(pool.map(simulate_chunk,tasks))
        windows=merge(parts,n,eps)
        results.append({"n":n,"epsilon":eps,"kind":kind,"s_reference":s,
                        "j_c":jc,"windows":windows})
        for key,a in windows.items():
            print(f"  {key} j={a['start']}..{a['end']} len={a['window_length']} "
                  f"EN={a['mean_Nwhite']:.3f} zero={a['zero_fraction']:.5f} "
                  f"rate/J={a['rate_cos_per_window']:.7g}",flush=True)
        Path(args.out).write_text(json.dumps({"params":vars(args),"results":results},indent=2),encoding="utf-8")
    print(f"saved {args.out}")

if __name__=="__main__": main()
