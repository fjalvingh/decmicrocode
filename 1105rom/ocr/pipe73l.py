import numpy as np, json, pickle
from PIL import Image
from scipy.ndimage import rotate as ndrotate, map_coordinates
from lib import deskew, otsu, fit_comb
from layout import ALLCOLS, NAM, LOC, BITS

PAGES=['73l-1','73l-2','73l-3','73l-4','73l-5','73l-6']
CH,CW=20,14; FX,FY=0.95,0.90; OS=3

def load(name):
    a=np.asarray(Image.open(f'/home/jal/1105rom/{name}.png').convert('L')).astype(np.float32)
    ink=(a<otsu(a)).astype(np.float32)
    ang,ink=deskew(ink)
    return a,ink,ang

geom={}; cols={}
for name in PAGES:
    a,ink,ang=load(name); H,W=ink.shape
    rp,rf,_=fit_comb(ink.sum(axis=1), 22, 30, 900)
    cen=[rf+k*rp for k in range(int((H-rf)/rp)+1)]
    occ=[float(ink[max(0,int(c)-int(rp*0.42)):int(c)+int(rp*0.42),:].sum()) for c in cen]
    cp,cf,_=fit_comb(ink.sum(axis=0), 12, 19, 1200)
    geom[name]=dict(ang=ang,rp=rp,rf=rf,cp=cp,cf=cf,occ=occ,H=H,W=W)
    print(f'{name}: skew {ang:+.2f} rowpitch {rp:.3f} colpitch {cp:.3f} slots {len(cen)}',flush=True)

def datarows(occ):
    big=[o for o in occ if o>200]; med=np.median(big)
    filled=[i for i,o in enumerate(occ) if o>med*0.25]
    groups=[]; s=filled[0]; prev=filled[0]
    for i in filled[1:]:
        if i==prev+1: prev=i
        else: groups.append((s,prev)); s=i; prev=i
    groups.append((s,prev)); hdr=groups[0]
    rows=list(range(hdr[1]-3,hdr[1]+1))
    for x,y in groups[1:]: rows+=list(range(x,y+1))
    return rows, hdr[1]-4

for name in PAGES:
    g=geom[name]; a,ink,ang=load(name); H,W=ink.shape
    rows,dash=datarows(g['occ'])
    rp,rf,cp,cf=g['rp'],g['rf'],g['cp'],g['cf']
    ncol=int((W-cf)/cp); half=rp*0.45
    band=np.zeros(W)
    for r in rows:
        y=rf+r*rp; band+=ink[max(0,int(y-half)):int(y+half),:].sum(axis=0)
    ci=np.array([float(band[max(0,int(cf+c*cp-cp/2)):int(cf+c*cp+cp/2)+1].sum()) for c in range(ncol)])
    ci=ci/ci.max()
    best=(-1,None)
    for b in range(0,6):
        sc=sum(ci[b+k] for k in ALLCOLS if b+k<len(ci))
        sc-=sum(ci[j] for j in range(b,min(len(ci),b+95)) if (j-b) not in set(ALLCOLS))
        if sc>best[0]: best=(sc,b)
    cols[name]=dict(rows=rows,dash=dash,ncol=ncol,base=best[1])
    print(f'{name}: rows {len(rows)} base {best[1]}',flush=True)

def prep(name):
    a=np.asarray(Image.open(f'/home/jal/1105rom/{name}.png').convert('L')).astype(np.float32)
    ink=(a<otsu(a)).astype(np.float32); ang,_=deskew(ink)
    a=ndrotate(a,ang,reshape=False,order=1,mode='nearest')
    bg=np.percentile(a,90); fg=np.percentile(a,2)
    return np.clip((bg-a)/max(1.0,bg-fg),0,1)

def sample_row(g,y,xs,rp,cp):
    ch,cw=CH*OS,CW*OS
    yy=np.linspace(y-FY*rp/2,y+FY*rp/2,ch); dxs=np.linspace(-FX*cp/2,FX*cp/2,cw)
    n=len(xs)
    X=np.broadcast_to(np.asarray(xs,float)[:,None,None]+dxs[None,None,:],(n,ch,cw))
    Y=np.broadcast_to(yy[None,:,None],(n,ch,cw))
    P=map_coordinates(g,[Y.ravel(),X.ravel()],order=1,mode='constant',cval=0.0).reshape(n,ch,cw)
    out=np.zeros((n,ch,cw),np.float32); ty,tx=ch//2,cw//2
    for i in range(n):
        p=P[i]; m=p.sum()
        if m>1e-3:
            gy=(p.sum(1)*np.arange(ch)).sum()/m; gx=(p.sum(0)*np.arange(cw)).sum()/m
            sy=int(np.clip(round(ty-gy),-ch//4,ch//4)); sx=int(np.clip(round(tx-gx),-cw//4,cw//4))
            p=np.roll(np.roll(p,sy,0),sx,1)
        out[i]=p
    return out.reshape(n,CH,OS,CW,OS).mean(axis=(2,4))

cells={}
for name in PAGES:
    g=prep(name); H,W=g.shape
    gm=geom[name]; c=cols[name]; b=c['base']
    rp,rf,cp,cf=gm['rp'],gm['rf'],gm['cp'],gm['cf']
    BC=[b+k for k in BITS]; ks=[b+k for k in ALLCOLS]
    rws=[]
    for slot in c['rows']:
        y0=rf+slot*rp
        xsb=np.array([cf+k*cp for k in BC])
        cc=np.clip(np.round(xsb[:,None]+np.arange(-2,3)[None,:]).astype(int).ravel(),0,W-1)
        strip=g[:,cc].sum(axis=1)
        lo,hi=max(0,int(y0-rp*0.45)),min(H,int(y0+rp*0.45)); w=strip[lo:hi]
        dy=float(np.clip((np.arange(lo,hi)*w).sum()/max(w.sum(),1e-6)-y0,-2.5,2.5))
        band=g[max(0,int(y0+dy-rp*0.40)):int(y0+dy+rp*0.40)+1,:].sum(axis=0)
        cs=np.cumsum(np.concatenate([[0.0],band])); best=(-1,0.0)
        for dx in np.arange(-0.32*cp,0.321*cp,0.1):
            a0=np.clip((xsb+dx-0.25*cp).astype(int),0,W); a1=np.clip((xsb+dx+0.25*cp).astype(int),0,W)
            s=(cs[a1]-cs[a0]).sum()
            if s>best[0]: best=(s,dx)
        P=sample_row(g,y0+dy,[cf+k*cp+best[1] for k in ks],rp,cp)
        rws.append({k:P[i].astype(np.float32) for i,k in enumerate(ALLCOLS)})
    cells[name]=rws
    print(name,'extracted',len(rws),flush=True)
pickle.dump(dict(geom=geom,cols=cols,cells=cells),open('l73.pkl','wb'))
