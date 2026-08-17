#!/usr/bin/env python3
"""Direct two-block restart test: endpoint law vs fresh uniform law per dyadic bucket."""
from __future__ import annotations
import argparse,json,math,os,random
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
LAM=math.log2(3);CAP=2/LAM

def sched(B,b):
 a=b/B
 if a>=CAP:return None
 lo=(a-1)/(2-LAM);hi=1/LAM;t=.5*(lo+hi);return max(1,math.floor(t*B))
def survive(x,n0,d):
 for _ in range(d):
  z=3*x+1;a=(z&-z).bit_length()-1;x=z>>a
  if x<=n0:return False,x
 return True,x
def chunk(t):
 lo,hi,n0,d1,B=t; ep=Counter();second=Counter()
 for n in range(lo|1,hi,2):
  ok,x=survive(n,n0,d1)
  if not ok:continue
  b=x.bit_length();d2=sched(B,b)
  if d2 is None:continue
  ep[b]+=1;ok2,_=survive(x,n0,d2);second[b]+=ok2
 return ep,second
def run(B,alpha,w,freshN=200000):
 n0=1<<B;yb=math.ceil(alpha*B);Y=1<<yb;lo=(alpha-1)/(2-LAM);hi=1/LAM;t=.5*(lo+hi);d1=max(1,math.floor(t*B));cnt=Y//2;per=(cnt+w-1)//w;tasks=[]
 for i in range(w):
  a=Y+2*i*per;b=min(2*Y,a+2*per)
  if a<b:tasks.append((a,b,n0,d1,B))
 with ProcessPoolExecutor(max_workers=w) as p:parts=list(p.map(chunk,tasks))
 ep=Counter();sec=Counter()
 for a,b in parts:ep.update(a);sec.update(b)
 rows=[]
 for bit,Q in sorted(ep.items()):
  d2=sched(B,bit);rng=random.Random(100000*B+bit);fresh=0
  # deterministic pseudo-random odd sample from exact dyadic bucket
  low=max(n0+1,1<<(bit-1)); high=1<<bit
  for _ in range(freshN):
   x=rng.randrange(low|1,high,2);ok,_=survive(x,n0,d2);fresh+=ok
  p_ep=sec[bit]/Q;p_fr=fresh/freshN;se=math.sqrt(max(1e-30,p_fr*(1-p_fr)*(1/Q+1/freshN)))
  rows.append({'bitlen':bit,'d2':d2,'Q':Q,'endpoint_second_survival':p_ep,'fresh_survival':p_fr,'ratio':p_ep/p_fr if p_fr else None,'z_difference':(p_ep-p_fr)/se if se else None})
 return {'B':B,'alpha':alpha,'d1':d1,'rows':rows}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--out',default='restart_two_block.json');args=ap.parse_args();out=[]
 for a in (1.05,1.1,1.2):
  print('alpha',a,flush=True);r=run(20,a,args.workers);out.append(r)
  for x in r['rows']:print(' bit=%d Q=%d d2=%d endpoint=%.5f fresh=%.5f ratio=%.3f z=%+.2f'%(x['bitlen'],x['Q'],x['d2'],x['endpoint_second_survival'],x['fresh_survival'],x['ratio'],x['z_difference']),flush=True)
  Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
