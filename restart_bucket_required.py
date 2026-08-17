#!/usr/bin/env python3
"""Sparse bucket-conditioned restart transport at each bucket's required modulus."""
from __future__ import annotations
import argparse,json,math,os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

LAM=math.log2(3); ACAP=2/LAM

def schedule(B,bitlen):
    alpha=bitlen/B
    if alpha>=ACAP:return None
    lo=(alpha-1)/(2-LAM);hi=1/LAM;t=.5*(lo+hi)
    d=max(1,math.floor(t*B));m=math.ceil(LAM*d+(bitlen-B))
    return alpha,d,m

def chunk(task):
    lo,hi,n0,d0,B=task; out={}; totals=Counter()
    for n in range(lo|1,hi,2):
        x=n;ok=x>n0
        if ok:
            for _ in range(d0):
                z=3*x+1;a=(z&-z).bit_length()-1;x=z>>a
                if x<=n0:ok=False;break
        if not ok:continue
        bit=x.bit_length(); sc=schedule(B,bit)
        if sc is None:continue
        _,_,m=sc; K=1<<(m-1); residue=(x>>1)&(K-1)
        out.setdefault(bit,Counter())[residue]+=1;totals[bit]+=1
    return out,totals

def run(B,alpha,workers):
    n0=1<<B;yb=math.ceil(alpha*B);Y=1<<yb;lo=(alpha-1)/(2-LAM);hi=1/LAM;t=.5*(lo+hi);d0=max(1,math.floor(t*B));cnt=Y//2;per=(cnt+workers-1)//workers;tasks=[]
    for i in range(workers):
        a=Y+2*i*per;b=min(2*Y,a+2*per)
        if a<b:tasks.append((a,b,n0,d0,B))
    with ProcessPoolExecutor(max_workers=workers) as p:parts=list(p.map(chunk,tasks,chunksize=1))
    merged={}; totals=Counter()
    for dd,tt in parts:
        totals.update(tt)
        for bit,c in dd.items():merged.setdefault(bit,Counter()).update(c)
    rows=[]
    for bit,c in sorted(merged.items()):
        a,d,m=schedule(B,bit);K=1<<(m-1);Q=totals[bit];mu=Q/K;vals=list(c.values());occupied=len(vals);maxc=max(vals);minc=min(vals) if occupied==K else 0
        # TV including empty classes: sum over occupied deviations plus empty mass.
        tv=.5*(sum(abs(v/Q-1/K) for v in vals)+(K-occupied)/K)
        chi=(sum((v-mu)**2/mu for v in vals)+(K-occupied)*mu)/max(1,K-1)
        rows.append({'bitlen':bit,'alpha_bucket':a,'next_d':d,'m_required':m,'classes':K,'Q':Q,'occupancy':mu,'occupied':occupied,'empty_fraction':1-occupied/K,'max_ratio':maxc/mu,'min_ratio':minc/mu if mu else 0,'tv':tv,'chi_df':chi})
    return {'B':B,'start_alpha':alpha,'Ybits':yb,'first_d':d0,'eligible_total':sum(totals.values()),'buckets':rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--out',default='restart_bucket_required.json');args=ap.parse_args();out=[]
    for a in (1.05,1.10,1.20):
        print('B=20 alpha',a,flush=True);r=run(20,a,args.workers);out.append(r)
        for x in r['buckets']:print(' bit=%d m=%d Q=%d occ=%.3g empty=%.3f K=%.3f TV=%.3f'%(x['bitlen'],x['m_required'],x['Q'],x['occupancy'],x['empty_fraction'],x['max_ratio'],x['tv']),flush=True)
        Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
