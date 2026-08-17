#!/usr/bin/env python3
"""Verify the exact hierarchical Fourier formula for a bad valuation-cylinder union."""
from __future__ import annotations
import cmath,itertools,math,numpy as np

def compositions(total,d,prefix=()):
    if d==1:
        yield prefix+(total,);return
    for a in range(1,total-d+2):yield from compositions(total-a,d-1,prefix+(a,))

def odd_coordinate_residue(word):
    c=0;S=0;d=len(word)
    for a in word:c=3*c+(1<<S);S+=a
    rho=((1<<S)-c)*pow(3,-d,1<<(S+1))%(1<<(S+1))
    assert rho&1
    return (rho-1)//2,S

def formula(d,M,h):
    K=1<<M;z=0j;v=(h&-h).bit_length()-1 if h else M
    for S in range(max(d,M-v),M+1):
        for w in compositions(S,d):
            r,_=odd_coordinate_residue(w)
            z += 2.0**(-S)*cmath.exp(-2j*math.pi*((h*r)%K)/K)
    return z

def direct(d,M):
    K=1<<M;b=np.zeros(K)
    for z in range(K):
        x=2*z+1;S=0
        for _ in range(d):
            y=3*x+1;a=(y&-y).bit_length()-1;S+=a
            if S>M:break
            x=y>>a
        b[z]=(S<=M)
    return np.fft.fft(b)/K

for d,M in ((7,12),(8,14)):
    f=direct(d,M);hs=list(np.argsort(np.abs(f[1:]))[::-1][:10]+1)+[1,2,4,8,16]
    worst=0
    print('d',d,'M',M,'badmass',f[0].real)
    for h0 in sorted(set(hs)):
        h=int(h0); z=formula(d,M,h);err=abs(z-f[h]);worst=max(worst,err)
        print(' h=%d v2=%d fft=%+.8g%+.8gj formula=%+.8g%+.8gj err=%.2e'%(h,(h&-h).bit_length()-1,f[h].real,f[h].imag,z.real,z.imag,err))
    print('worst',worst)
