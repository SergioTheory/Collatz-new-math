#!/usr/bin/env python3
"""Exact Fourier overlap of transported endpoint law with the next bad-cylinder union."""
from __future__ import annotations
import argparse,json,math,os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
LAM=math.log2(3); CAP=2/LAM

def schedule(B,bit):
    alpha=bit/B
    if alpha>=CAP:return None
    t=.5*((alpha-1)/(2-LAM)+1/LAM);d=max(1,math.floor(t*B));A=LAM*d+(bit-B);M=math.ceil(A)-1
    return d,M,M+1

def endpoints_chunk(task):
    lo,hi,n0,d1,B=task; out={}
    for n in range(lo|1,hi,2):
        x=n;ok=x>n0
        if ok:
            for _ in range(d1):
                z=3*x+1;a=(z&-z).bit_length()-1;x=z>>a
                if x<=n0:ok=False;break
        if not ok:continue
        bit=x.bit_length();sc=schedule(B,bit)
        if sc is None:continue
        _,M,_=sc;K=1<<M;out.setdefault(bit,[]).append((x>>1)&(K-1))
    return {b:np.asarray(v,dtype=np.uint32) for b,v in out.items()}

def bad_chunk(task):
    lo,hi,d,M=task; arr=np.zeros(hi-lo,dtype=np.uint8)
    for ii,z0 in enumerate(range(lo,hi)):
        x=2*z0+1;S=0
        for _ in range(d):
            y=3*x+1;a=(y&-y).bit_length()-1;S+=a
            if S>M:break
            x=y>>a
        if S<=M:arr[ii]=1
    return lo,arr

def build_bad(K,d,M,workers):
    per=(K+workers-1)//workers;tasks=[(i,min(K,i+per),d,M) for i in range(0,K,per)]
    out=np.zeros(K,dtype=np.float64)
    with ProcessPoolExecutor(max_workers=workers) as p:
        for lo,a in p.map(bad_chunk,tasks,chunksize=1):out[lo:lo+len(a)]=a
    return out

def top_overlap(nu,bad,d1,top):
    K=len(nu);half=K//2
    # For real inputs, the h and K-h terms are conjugates.  Work with the
    # non-redundant real FFT and form their real pair contribution directly.
    fnu=np.fft.rfft(nu);fb=np.fft.rfft(bad);cross=fnu*np.conj(fb)/K
    pairs=2.0*cross[1:].real;pairs[-1]=cross[-1].real
    magnitudes=np.abs(pairs);total=float(pairs.sum());abs_l1=float(magnitudes.sum())
    n=min(top,half)
    if n:
        selected=np.argpartition(magnitudes,half-n)[half-n:]
        selected=selected[np.lexsort((selected,-magnitudes[selected]))]
    else:selected=np.empty(0,dtype=np.intp)
    ret=[]
    for i in selected:
        h=int(i)+1;z=float(pairs[i]);a=(h*pow(3,d1,K))%K
        signed_a=a if a<=K//2 else a-K
        ret.append({'h':h,'co_moving_a':signed_a,'term_real':z,'term_imag':0.0,'term_abs':abs(z),'endpoint_abs':float(abs(fnu[h])),'bad_abs_over_K':float(abs(fb[h])/K)})
    return {'fourier_difference_real':total,'fourier_difference_imag':0.0,'pair_l1':abs_l1,'cancellation_ratio':abs(total)/abs_l1 if abs_l1 else 0,'top_terms':ret}

def run(B,alpha,workers,top):
    n0=1<<B;yb=math.ceil(alpha*B);Y=1<<yb;t=.5*((alpha-1)/(2-LAM)+1/LAM);d1=max(1,math.floor(t*B));cnt=Y//2;per=(cnt+workers-1)//workers;tasks=[]
    for i in range(workers):
        lo=Y+2*i*per;hi=min(2*Y,lo+2*per)
        if lo<hi:tasks.append((lo,hi,n0,d1,B))
    merged={}
    with ProcessPoolExecutor(max_workers=workers) as p:
        for dd in p.map(endpoints_chunk,tasks,chunksize=1):
            for bit,a in dd.items():merged.setdefault(bit,[]).append(a)
    rows=[]
    for bit,parts in sorted(merged.items()):
        d2,M,modexp=schedule(B,bit);K=1<<M;idx=np.concatenate(parts);counts=np.bincount(idx,minlength=K).astype(np.float64);nu=counts/counts.sum();bad=build_bad(K,d2,M,workers);direct=float(np.dot(nu,bad));fresh=float(bad.mean());dec=top_overlap(nu,bad,d1,top)
        rows.append({'bitlen':bit,'d2':d2,'M_shift_threshold':M,'modulus_exponent':modexp,'classes':K,'Q':int(counts.sum()),'endpoint_bad_probability':direct,'fresh_bad_probability':fresh,'difference':direct-fresh,'ratio':direct/fresh if fresh else None,'decomposition':dec})
        print(' bit=%d d2=%d M=%d K=%d Q=%d bad %.6g/%.6g diff=%+.3g spectral=%+.3g l1=%.3g cancel=%.3g'%(bit,d2,M,K,int(counts.sum()),direct,fresh,direct-fresh,dec['fourier_difference_real'],dec['pair_l1'],dec['cancellation_ratio']),flush=True)
        del counts,nu,bad
    return {'B':B,'alpha':alpha,'Ybits':yb,'d1':d1,'rows':rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--B',type=int,default=20);ap.add_argument('--workers',type=int,default=min(30,os.cpu_count() or 1));ap.add_argument('--alphas',nargs='+',type=float,default=[1.10]);ap.add_argument('--top',type=int,default=20);ap.add_argument('--out',default='restart_bad_spectral_overlap.json');args=ap.parse_args();out=[]
    for a in args.alphas:
        print(f'B={args.B} alpha',a,flush=True);r=run(args.B,a,args.workers,args.top);out.append(r);Path(args.out).write_text(json.dumps(out,indent=2),encoding='utf-8')
    print('saved',args.out)
if __name__=='__main__':main()
