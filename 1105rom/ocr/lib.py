import numpy as np
from PIL import Image
from scipy.ndimage import rotate as ndrotate

def otsu(a):
    hist,_ = np.histogram(a, bins=256, range=(0,256))
    tot=a.size; sa=(np.arange(256)*hist).sum(); wB=0; sB=0; best=(0,128)
    for t in range(256):
        wB+=hist[t]
        if wB==0: continue
        wF=tot-wB
        if wF==0: break
        sB+=t*hist[t]
        v=wB*wF*((sB/wB)-((sa-sB)/wF))**2
        if v>best[0]: best=(v,t)
    return best[1]

def load_ink(path):
    a=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    t=otsu(a)
    return (a<t).astype(np.float32), a, t

def sharpness(ink):
    p=ink.sum(axis=1)
    return float(((p-p.mean())**2).sum())

def deskew(ink, lo=-1.5, hi=1.5, steps=61):
    best=(-1,0.0,ink)
    for ang in np.linspace(lo,hi,steps):
        r=ndrotate(ink, ang, reshape=False, order=1, mode='constant', cval=0.0)
        s=sharpness(r)
        if s>best[0]: best=(s,ang,r)
    return best[1], best[2]

def fit_comb(prof, plo, phi, npitch=1200, nphase=None):
    n=len(prof); best=(-1,None,None)
    for p in np.linspace(plo,phi,npitch):
        ph=nphase or max(10,int(p*6))
        k=np.arange(0,int(n/p)+1)
        for f in np.linspace(0,p,ph,endpoint=False):
            pos=f+k*p; pos=pos[(pos>=0)&(pos<n-1)]
            i0=pos.astype(int); fr=pos-i0
            v=(prof[i0]*(1-fr)+prof[i0+1]*fr).sum()/len(pos)
            if v>best[0]: best=(v,p,f)
    return best[1],best[2],best[0]
