#!/usr/bin/env python3
"""Alpha stability sweep for finite-window r=5 Front-C block contraction."""
from __future__ import annotations
import json,math,os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from front_c_finite_block import finite_block
SRC=Path('front_c_large_results.json'); OUT=Path('front_c_alpha_sweep.json')
R=5;B=40;SIG=6.;OFF=.5
ALPHAS=(.001,.002,.005,.01,.02,.05,.1,.2)
def main():
 d=json.loads(SRC.read_text(encoding='utf-8'));jobs=[];meta=[]
 for n in (200,400):
  Rn=next(x for x in d['results'] if x['n']==n)
  for row in Rn['rows']:
   eps=row['epsilon']; s=row['best_low_power']['low_s']; xi=pow(2,s,3**n); first=math.ceil((s+2)/4+OFF*math.sqrt(n));end=n//2-math.ceil(math.log(n))
   for alpha in ALPHAS:
    for j in range(first,end-R+2,R): jobs.append((n,eps,xi,j,R,alpha,B,SIG));meta.append((n,eps,s,alpha,j))
 print('tasks',len(jobs),flush=True)
 with ProcessPoolExecutor(max_workers=min(30,os.cpu_count() or 1)) as p: vals=list(p.map(finite_block,jobs,chunksize=1))
 rec=[]
 for m,x in zip(meta,vals): n,e,s,a,j=m;x.update(n=n,epsilon=e,s=s,alpha=a,j=j);rec.append(x)
 sums=[]
 for n in (200,400):
  for eps in (.1,.05,.02,.01):
   eta=-math.log(math.cos(math.pi*eps));ciid=-math.log(1-.25*(1-2*eps)*(1-math.exp(-eta)))
   for alpha in ALPHAS:
    rr=[x for x in rec if x['n']==n and x['epsilon']==eps and x['alpha']==alpha]
    if not rr:continue
    M=(2**alpha/(2-2**alpha))**2;A=sum((b-1)*2**(-b)*2**(alpha*b) for b in range(2,B+1));tail=M**R-A**R;w=max(rr,key=lambda x:x['finite_sup']);full=w['finite_sup']+tail;rate=-math.log(full)/R
    sums.append({'n':n,'epsilon':eps,'alpha':alpha,'worst_start':w['j'],'finite':w['finite_sup'],'blocktail':tail,'full':full,'rate':rate,'iid':ciid,'ratio':rate/ciid})
   best=max([x for x in sums if x['n']==n and x['epsilon']==eps],key=lambda x:x['rate'])
   print('n=%d eps=%.2f bestalpha=%.3g rate=%+.7g iid=%.7g ratio=%+.3f full=%.9f'%(n,eps,best['alpha'],best['rate'],ciid,best['ratio'],best['full']),flush=True)
 OUT.write_text(json.dumps({'summaries':sums,'blocks':rec},indent=2),encoding='utf-8')
if __name__=='__main__':main()
