import numpy as np, json, pickle
from PIL import Image
from scipy.ndimage import rotate as ndrotate, map_coordinates
from lib import deskew, otsu
from layout import BITS, LOC, NAM, ALLCOLS

G=json.load(open('geom.json')); C=pickle.load(open('cols.pkl','rb'))
B=json.load(open('bases.json'))
PAGES=[f'73-{i}' for i in range(1,7)]+[f'76-p{i}' for i in range(1,7)]
CH,CW=20,14
FX,FY=0.95,0.90
OS=3   # oversample factor for centroid centring

def prep(name):
    a=np.asarray(Image.open(f'/home/jal/1105rom/{name}.png').convert('L')).astype(np.float32)
    ink=(a<otsu(a)).astype(np.float32)
    ang,_=deskew(ink)
    a=ndrotate(a,ang,reshape=False,order=1,mode='nearest')
    bg=np.percentile(a,90); fg=np.percentile(a,2)
    return np.clip((bg-a)/max(1.0,bg-fg),0,1), ang

def sample_row(g, y, xs, rp, cp):
    """sample len(xs) cells centred at (y, xs[i]) -> (n, CH, CW)"""
    ch,cw=CH*OS,CW*OS
    yy=np.linspace(y-FY*rp/2, y+FY*rp/2, ch)
    dxs=np.linspace(-FX*cp/2, FX*cp/2, cw)
    n=len(xs)
    X=np.broadcast_to(np.asarray(xs,dtype=float)[:,None,None]+dxs[None,None,:], (n,ch,cw))
    Y=np.broadcast_to(yy[None,:,None], (n,ch,cw))
    P=map_coordinates(g,[Y.ravel(),X.ravel()],order=1,mode='constant',cval=0.0).reshape(n,ch,cw)
    # centre each cell on its own ink centroid, then crop to CH x CW * OS
    out=np.zeros((n,CH*OS,CW*OS),dtype=np.float32)
    ty,tx=ch//2, cw//2
    for i in range(n):
        p=P[i]
        m=p.sum()
        if m>1e-3:
            gy=(p.sum(1)*np.arange(ch)).sum()/m; gx=(p.sum(0)*np.arange(cw)).sum()/m
            sy=int(round(ty-gy)); sx=int(round(tx-gx))
            sy=int(np.clip(sy,-ch//4,ch//4)); sx=int(np.clip(sx,-cw//4,cw//4))
            p=np.roll(np.roll(p,sy,axis=0),sx,axis=1)
        out[i]=p
    # box-downsample OS
    out=out.reshape(n,CH,OS,CW,OS).mean(axis=(2,4))
    return out

out={}
for name in PAGES:
    gm=G[name]; c=C[name]
    g,ang=prep(name); H,W=g.shape
    rp,rf,cp,cf=gm['rp'],gm['rf'],gm['cp'],gm['cf']
    b=B[name]
    BITCOLS=[b+k for k in BITS]
    ks=[b+k for k in ALLCOLS]
    rows=[]
    for slot in c['rows']:
        y0=rf+slot*rp
        # dy from 1-D row profile of the bit-column strip
        xsb=np.array([cf+k*cp for k in BITCOLS])
        cols=np.round(np.concatenate([xsb[:,None]+np.arange(-2,3)[None,:]])).astype(int).ravel()
        cols=np.clip(cols,0,W-1)
        strip=g[:,cols].sum(axis=1)
        yy=np.arange(max(0,int(y0-4)),min(H,int(y0+5)))
        # centre of mass of the strip within +-0.5 pitch of y0
        lo,hi=max(0,int(y0-rp*0.45)),min(H,int(y0+rp*0.45))
        w=strip[lo:hi]
        dy=(np.arange(lo,hi)*w).sum()/max(w.sum(),1e-6)-y0
        dy=float(np.clip(dy,-2.5,2.5))
        # dx: search narrow, score = sum over 40 cells of ink in a +-0.25cp window
        band=g[max(0,int(y0+dy-rp*0.40)):int(y0+dy+rp*0.40)+1,:].sum(axis=0)
        cs=np.cumsum(np.concatenate([[0.0],band]))
        best=(-1,0.0)
        for dx in np.arange(-0.32*cp,0.321*cp,0.1):
            a0=np.clip((xsb+dx-0.25*cp).astype(int),0,W); a1=np.clip((xsb+dx+0.25*cp).astype(int),0,W)
            s=(cs[a1]-cs[a0]).sum()
            if s>best[0]: best=(s,dx)
        dx=best[1]
        xs=[cf+k*cp+dx for k in ks]
        P=sample_row(g, y0+dy, xs, rp, cp)
        rows.append({k:P[i].astype(np.float32) for i,k in enumerate(ALLCOLS)})
    out[name]=rows
    print(name,'rows',len(rows),f'skew {ang:+.2f}',flush=True)
pickle.dump(out, open('cells2.pkl','wb'))
