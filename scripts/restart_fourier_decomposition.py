#!/usr/bin/env python3
"""Decompose endpoint Fourier peaks into valuation-word and scale contributions."""
from __future__ import annotations
import argparse,cmath,json,math,os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

def worker(task):
 lo,hi,n0,d,mmax=task;K=1<<(mmax-1);hist=np.zeros(K,dtype=np.int64);buckets={};stats={};Q=0
 for n in range(lo|1,hi,2):
  x=n;word=[];ok=x>n0
  if ok:
   for _ in range(d):
    z=3*x+1;a=(z&-z).bit_length()-1;word.append(a);x=z>>a
    if x<=n0:ok=False;break
  if not ok:continue
  Q+=1;idx=(x>>1)&(K-1);hist[idx]+=1;bit=x.bit_length();buckets.setdefault(bit,np.zeros(K,dtype=np.int64))[idx]+=1
  key=tuple(word);old=stats.get(key)
  if old is None:stats[key]=[1,x,x]
  else:old[0]+=1;old[1]=min(old[1],x);old[2]=max(old[2],x)
 return Q,hist,buckets,stats

def fold(h,m):K=1<<(m-1);return h.reshape(-1,K).sum(0)
def spectrum(h):
 p=h/h.sum();return np.fft.fft(p)
def top_modes(h,top):
 f=spectrum(h);idx=np.argsort(np.abs(f[1:]))[::-1][:top]+1
 return [{'h':int(i),'abs':float(abs(f[i])),'phase':float(np.angle(f[i]))} for i in idx]
def geom_word(count,x0,d,h,K):
 z0=(x0-1)//2;step=pow(3,d,K);r=(h*step)%K;phase0=cmath.exp(-2j*math.pi*((h*z0)%K)/K)
 if r==0:return count*phase0
 den=1-cmath.exp(-2j*math.pi*r/K)
 num=1-cmath.exp(-2j*math.pi*((r*count)%K)/K)
 return phase0*num/den
def decompose_words(stats,d,h,K,Q):
 vals=[];total=0j;bad=0
 step_abs=2*3**d
 for word,(count,xmin,xmax) in stats.items():
  if count>1 and xmax-xmin != step_abs*(count-1):bad+=1
  a=geom_word(count,xmin,d,h,K);vals.append((abs(a),a,count,word));total+=a
 l1=sum(v[0] for v in vals);l2=sum(v[0]**2 for v in vals);vals.sort(reverse=True,key=lambda x:x[0])
 return {'abs_total_over_Q':abs(total)/Q,'word_l1_over_Q':l1/Q,'interword_coherence':abs(total)/l1 if l1 else 0,'effective_words_l1_sq_over_l2':l1*l1/l2 if l2 else 0,'largest_word_abs_over_Q':vals[0][0]/Q if vals else 0,'top10_word_l1_fraction':sum(v[0] for v in vals[:10])/l1 if l1 else 0,'noncontiguous_word_stats':bad,'word_count':len(vals),'top_words':[{'abs_over_Q':v[0]/Q,'count':v[2],'word':list(v[3])} for v in vals[:10]]}
def decompose_buckets(buckets,h,K,Q):
 rows=[];total=0j;l1=0
 for bit,arr in sorted(buckets.items()):
  p=np.fft.fft(arr.astype(float))[h] # unnormalized endpoint phase sum
  # np fft uses the desired negative sign
  total+=p;l1+=abs(p);rows.append({'bitlen':bit,'count':int(arr.sum()),'abs_over_Q':float(abs(p)/Q),'phase':float(np.angle(p))})
 return {'abs_total_over_Q':abs(total)/Q,'bucket_l1_over_Q':l1/Q,'interbucket_coherence':abs(total)/l1 if l1 else 0,'buckets':rows}
def run(B,alpha,mmax,top,workers):
 lam=math.log2(3);t=.5*((alpha-1)/(2-lam)+1/lam);n0=1<<B;yb=math.ceil(alpha*B);Y=1<<yb;d=max(1,math.floor(t*B));cnt=Y//2;per=(cnt+workers-1)//workers;tasks=[]
 for i in range(workers):
  lo=Y+2*i*per;hi=min(2*Y,lo+2*per)
  if lo<hi:tasks.append((lo,hi,n0,d,mmax))
 with ProcessPoolExecutor(max_workers=workers) as p:parts=list(p.map(worker,tasks,chunksize=1))
 K=1<<(mmax-1);hist=np.zeros(K,dtype=np.int64);buckets={};stats={};Q=0
 for q,h,bb,ss in parts:
  Q+=q;hist+=h
  for bit,a in bb.items():buckets.setdefault(bit,np.zeros(K,dtype=np.int64));buckets[bit]+=a
  for word,(c,x0,x1) in ss.items():
   old=stats.get(word)
   if old is None:stats[word]=[c,x0,x1]
   else:old[0]+=c;old[1]=min(old[1],x0);old[2]=max(old[2],x1)
 projections={};targets=set()
 for m in range(6,mmax+1,2):
  hh=fold(hist,m);tm=top_modes(hh,top);projections[str(m)]={'top':tm,'count':int(hh.sum())}
  if m==mmax:targets.update(x['h'] for x in tm)
 # Add lifts to max modulus of top modes from all coarser projections.
 for sm,v in projections.items():
  m=int(sm);factor=1<<(mmax-m)
  for x in v['top']:targets.add(x['h']*factor)
 dec={}
 for h in sorted(targets):dec[str(h)]={'word':decompose_words(stats,d,h,K,Q),'scale':decompose_buckets(buckets,h,K,Q)}
 return {'B':B,'alpha':alpha,'Ybits':yb,'d':d,'mmax':mmax,'Q':Q,'word_count':len(stats),'projections':projections,'max_mod_decomposition':dec}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--mmax',type=int,default=14);ap.add_argument('--top',type=int,default=8);ap.add_argument('--out',default='restart_fourier_decomposition.json');args=ap.parse_args();out=[]
 for a in (1.05,1.10,1.20):
  print('decompose B=20 alpha',a,flush=True);r=run(20,a,args.mmax,args.top,args.workers);out.append(r)
  top=r['projections'][str(args.mmax)]['top'][0];d=r['max_mod_decomposition'][str(top['h'])];print(' Q=%d W=%d peak h=%d abs=%.5g wordcoh=%.4f scalecoh=%.4f l1word=%.4f'%(r['Q'],r['word_count'],top['h'],top['abs'],d['word']['interword_coherence'],d['scale']['interbucket_coherence'],d['word']['word_l1_over_Q']),flush=True)
  Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
