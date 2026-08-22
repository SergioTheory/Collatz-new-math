#!/usr/bin/env python3
"""Stability sweep of finite-window Front-C block contraction."""
from __future__ import annotations
import json, math, os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from front_c_finite_block import finite_block

SOURCE=Path('front_c_large_results.json')
OUT=Path('front_c_block_stability.json')
R=5; ALPHA=.1; B=40; SIGMA=6.0; OFFSET=.5

def main():
 data=json.loads(SOURCE.read_text(encoding='utf-8')); jobs=[]; meta=[]
 for n in (200,400):
  result=next(x for x in data['results'] if x['n']==n)
  for row in result['rows']:
   eps=row['epsilon']; s_adv=row['best_low_power']['low_s']; s_e6=row['e6_sstar']
   for kind,s in (('adv',s_adv),('e6',s_e6)):
    xi=pow(2,s,3**n); first=math.ceil((s+2)/4+OFFSET*math.sqrt(n)); end=n//2-math.ceil(math.log(n))
    starts=list(range(first,end-R+2,R))
    for j in starts:
     jobs.append((n,eps,xi,j,R,ALPHA,B,SIGMA)); meta.append((n,eps,kind,s,j))
 print('tasks',len(jobs),'workers',min(30,os.cpu_count() or 1),flush=True)
 with ProcessPoolExecutor(max_workers=min(30,os.cpu_count() or 1)) as pool: vals=list(pool.map(finite_block,jobs,chunksize=1))
 records=[]
 for m,x in zip(meta,vals):
  n,eps,kind,s,j=m; x.update(n=n,epsilon=eps,kind=kind,s=s); records.append(x)
 q=2**(-(1-ALPHA)); M=(2**ALPHA/(2-2**ALPHA))**2; A=sum((b-1)*2**(-b)*2**(ALPHA*b) for b in range(2,B+1)); blocktail=M**R-A**R
 summaries=[]
 for n in (200,400):
  for eps in (.1,.05,.02,.01):
   eta=-math.log(math.cos(math.pi*eps)); ciid=-math.log(1-.25*(1-2*eps)*(1-math.exp(-eta)))
   for kind in ('adv','e6'):
    rr=[x for x in records if x['n']==n and abs(x['epsilon']-eps)<1e-15 and x['kind']==kind]
    if not rr: continue
    worst=max(rr,key=lambda x:x['finite_sup']); full=worst['finite_sup']+blocktail; cert=-math.log(full)/R
    z={'n':n,'epsilon':eps,'kind':kind,'s':worst['s'],'blocks':len(rr),'worst_start':worst['j'],
       'worst_finite':worst['finite_sup'],'block_tail':blocktail,'full_bound':full,
       'cert_rate':cert,'iid_rate':ciid,'cert_over_iid':cert/ciid}
    summaries.append(z)
    print('n=%d eps=%.2f %s s=%d blocks=%d full=%.9f cert=%.7g iid=%.7g ratio=%.3f'%(n,eps,kind,worst['s'],len(rr),full,cert,ciid,cert/ciid),flush=True)
 OUT.write_text(json.dumps({'params':{'r':R,'alpha':ALPHA,'B':B,'sigma':SIGMA,'offset':OFFSET},'summaries':summaries,'blocks':records},indent=2),encoding='utf-8')
 print('saved',OUT)
if __name__=='__main__':main()
