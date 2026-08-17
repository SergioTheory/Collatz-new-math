#!/usr/bin/env python3
"""Compare second-block scale transition kernels: transported endpoints vs fresh starts."""
from __future__ import annotations
import argparse,json,math,os,random
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
LAM=math.log2(3); CAP=2/LAM

def sched(B,b):
 a=b/B
 if a>=CAP:return None
 t=.5*((a-1)/(2-LAM)+1/LAM);return max(1,math.floor(t*B))
def evolve(x,n0,d):
 for _ in range(d):
  z=3*x+1;a=(z&-z).bit_length()-1;x=z>>a
  if x<=n0:return 0
 return x.bit_length()
def chunk(t):
 lo,hi,n0,d1,B=t; kernels={}
 for n in range(lo|1,hi,2):
  b=evolve(n,n0,d1)
  if not b:continue
  d2=sched(B,b)
  if d2 is None:continue
  # Recompute endpoint to preserve it (evolve above returned only bit length).
  x=n
  for _ in range(d1):
   z=3*x+1;a=(z&-z).bit_length()-1;x=z>>a
  state=evolve(x,n0,d2)  # 0=descent, else next endpoint bit length
  kernels.setdefault(b,Counter())[state]+=1
 return kernels
def normalize(c):
 n=sum(c.values());return {k:v/n for k,v in c.items()},n
def compare(a,b):
 pa,na=normalize(a);pb,nb=normalize(b);keys=set(pa)|set(pb);tv=.5*sum(abs(pa.get(k,0)-pb.get(k,0)) for k in keys);maxex=max((pa.get(k,0)/(pb.get(k,0)) if pb.get(k,0)>0 else float('inf'),k) for k in keys if pa.get(k,0)>0)
 return tv,maxex,na,nb,pa,pb
def run(B,alpha,w,freshN=300000):
 n0=1<<B;yb=math.ceil(alpha*B);Y=1<<yb;t=.5*((alpha-1)/(2-LAM)+1/LAM);d1=max(1,math.floor(t*B));cnt=Y//2;per=(cnt+w-1)//w;tasks=[]
 for i in range(w):
  a=Y+2*i*per;b=min(2*Y,a+2*per)
  if a<b:tasks.append((a,b,n0,d1,B))
 with ProcessPoolExecutor(max_workers=w) as p:parts=list(p.map(chunk,tasks))
 real={}
 for dd in parts:
  for bit,c in dd.items():real.setdefault(bit,Counter()).update(c)
 rows=[]
 for bit,c in sorted(real.items()):
  d2=sched(B,bit);rng=random.Random(B*100000+bit);low=max(n0+1,1<<(bit-1));high=1<<bit;fresh=Counter()
  for _ in range(freshN):
   x=rng.randrange(low|1,high,2);fresh[evolve(x,n0,d2)]+=1
  tv,mx,nr,nf,pr,pf=compare(c,fresh)
  rows.append({'bitlen':bit,'d2':d2,'real_N':nr,'fresh_N':nf,'kernel_tv':tv,'max_state_ratio':mx[0],'max_state':mx[1],'real_kernel':pr,'fresh_kernel':pf})
 return {'B':B,'alpha':alpha,'d1':d1,'rows':rows}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--out',default='restart_scale_kernel.json');args=ap.parse_args();out=[]
 for a in (1.05,1.1,1.2):
  print('alpha',a,flush=True);r=run(20,a,args.workers);out.append(r)
  for x in r['rows']:print(' bit=%d Q=%d d2=%d TV=%.4f maxratio=%.3f state=%s'%(x['bitlen'],x['real_N'],x['d2'],x['kernel_tv'],x['max_state_ratio'],x['max_state']),flush=True)
  Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
