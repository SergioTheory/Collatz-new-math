#!/usr/bin/env python3
"""Replace Monte-Carlo fresh kernels by exhaustive dyadic-bucket kernels."""
from __future__ import annotations
import argparse,json,os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def evolve(x,n0,d):
    for _ in range(d):
        z=3*x+1; a=(z&-z).bit_length()-1; x=z>>a
        if x<=n0:return 0
    return x.bit_length()

def fresh_chunk(task):
    B,bit,d,lo,hi=task; n0=1<<B; c=Counter()
    for x in range(lo|1,hi,2):c[evolve(x,n0,d)]+=1
    return B,bit,d,c

def compare(real,fresh):
    nr=sum(real.values());nf=sum(fresh.values());keys=set(real)|set(fresh)
    pr={k:v/nr for k,v in real.items()};pf={k:v/nf for k,v in fresh.items()}
    tv=.5*sum(abs(pr.get(k,0)-pf.get(k,0)) for k in keys)
    ratios=[(pr.get(k,0)/pf.get(k,0),k,pr.get(k,0),pf.get(k,0)) for k in keys if pr.get(k,0)>0 and pf.get(k,0)>0]
    mx=max(ratios)
    return tv,mx,pr,pf,nr,nf

def load_rows(paths):
    rows=[]
    for path in paths:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        rows.extend(data)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--out',default='restart_scale_kernel_exact.json');args=ap.parse_args()
    source=load_rows(['restart_scale_kernel_small.json','restart_scale_kernel.json'])
    unique={}
    for run in source:
        B=run['B']
        for row in run['rows']:unique[(B,row['bitlen'],row['d2'])]=None
    tasks=[];chunks_per_bucket=max(4,args.workers//3)
    for B,bit,d in unique:
        low=max((1<<B)+1,1<<(bit-1));high=1<<bit;odd_count=(high-(low|1)+1)//2;per=(odd_count+chunks_per_bucket-1)//chunks_per_bucket
        for i in range(chunks_per_bucket):
            lo=(low|1)+2*i*per;hi=min(high,lo+2*per)
            if lo<hi:tasks.append((B,bit,d,lo,hi))
    print(f'exact fresh: {len(unique)} buckets, {len(tasks)} chunks, {args.workers} workers',flush=True)
    merged={}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for B,bit,d,c in pool.map(fresh_chunk,tasks,chunksize=1):merged.setdefault((B,bit,d),Counter()).update(c)
    out=[]
    for run in source:
        rr={'B':run['B'],'alpha':run['alpha'],'d1':run['d1'],'rows':[]}
        for row in run['rows']:
            real=Counter({int(k):v*row['real_N'] for k,v in row['real_kernel'].items()})
            # JSON probabilities recover integer counts up to floating precision; round.
            real=Counter({k:int(round(v)) for k,v in real.items()})
            fresh=merged[(run['B'],row['bitlen'],row['d2'])]
            tv,mx,pr,pf,nr,nf=compare(real,fresh)
            rr['rows'].append({'bitlen':row['bitlen'],'d2':row['d2'],'real_N':nr,'fresh_N':nf,'kernel_tv_exact':tv,'max_state_ratio':mx[0],'max_state':mx[1],'max_state_real_prob':mx[2],'max_state_fresh_prob':mx[3],'real_kernel':pr,'fresh_kernel_exact':pf})
        out.append(rr)
        wt=sum(x['kernel_tv_exact']*x['real_N'] for x in rr['rows'])/sum(x['real_N'] for x in rr['rows']);mx=max(x['kernel_tv_exact'] for x in rr['rows'])
        print('B=%d alpha=%.2f maxTV=%.6f weightedTV=%.6f'%(rr['B'],rr['alpha'],mx,wt),flush=True)
    Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
    print('saved',args.out)
if __name__=='__main__':main()
