#!/usr/bin/env python3
"""Global-only restart transport at large dyadic modulus."""
from __future__ import annotations
import argparse,json,math,os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

def chunk(t):
 lo,hi,n0,d,m=t; h=np.zeros(1<<(m-1),dtype=np.int64); q=0
 for n in range(lo|1,hi,2):
  x=n;ok=x>n0
  if ok:
   for _ in range(d):
    z=3*x+1;a=(z&-z).bit_length()-1;x=z>>a
    if x<=n0:ok=False;break
  if ok:
   h[(x>>1)&((1<<(m-1))-1)]+=1;q+=1
 return q,h

def run(bits,a,m,w):
 lam=math.log2(3);t=.5*((a-1)/(2-lam)+1/lam);n0=1<<bits;yb=math.ceil(a*bits);Y=1<<yb;d=max(1,math.floor(t*bits));cnt=Y//2;per=(cnt+w-1)//w;tasks=[]
 for i in range(w):
  lo=Y+2*i*per;hi=min(2*Y,lo+2*per)
  if lo<hi:tasks.append((lo,hi,n0,d,m))
 with ProcessPoolExecutor(max_workers=w) as p:parts=list(p.map(chunk,tasks))
 h=sum((x[1] for x in parts),np.zeros(1<<(m-1),dtype=np.int64));Q=int(h.sum());K=len(h);mu=Q/K;p=h/Q;hat=np.fft.fft(p);non=np.abs(hat[1:]);tv=.5*np.abs(p-1/K).sum();chi=(((h-mu)**2/mu).sum())/(K-1)
 return {'bits':bits,'alpha':a,'Ybits':yb,'d':d,'m':m,'Q':Q,'classes':K,'occupancy':mu,'max_ratio':float(h.max()/mu),'min_ratio':float(h.min()/mu),'empty':float(np.mean(h==0)),'tv':float(tv),'chi_df':float(chi),'maxhat':float(non.max()),'hmax':int(non.argmax()+1),'iid_hat':1/math.sqrt(Q)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--out',default='restart_transport_large_m.json');args=ap.parse_args();out=[]
 for bits in (16,18,20):
  for a in (1.05,1.1,1.2):
   for m in sorted(set((bits-2,bits))):
    print('bits',bits,'a',a,'m',m,flush=True);r=run(bits,a,m,args.workers);out.append(r);print(' Q=%d occ=%.2f K=%.2f empty=%.3f TV=%.3f maxhat=%.4g/iid%.1f'%(r['Q'],r['occupancy'],r['max_ratio'],r['empty'],r['tv'],r['maxhat'],r['maxhat']/r['iid_hat']),flush=True)
    Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
