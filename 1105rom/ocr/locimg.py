import numpy as np, pickle
from PIL import Image
from layout import LOC
D=pickle.load(open('cells2.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}
def km(X,k,seed):
    rng=np.random.default_rng(seed)
    c=[X[rng.integers(len(X))]]; d2=((X-c[0])**2).sum(1)
    for _ in range(k-1):
        p=d2/d2.sum(); c.append(X[rng.choice(len(X),p=p)]); d2=np.minimum(d2,((X-c[-1])**2).sum(1))
    c=np.stack(c)
    for _ in range(200):
        d=((X[:,None,:]-c[None,:,:])**2).sum(2); lab=d.argmin(1)
        cn=np.stack([X[lab==j].mean(0) if (lab==j).any() else X[rng.integers(len(X))] for j in range(k)])
        if np.allclose(cn,c): break
        c=cn
    d=((X[:,None,:]-c[None,:,:])**2).sum(2); lab=d.argmin(1)
    sd=np.sort(d,1); return lab,c,(sd[:,1]-sd[:,0])/(sd[:,1]+1e-9),d.min(1)
res={}
for s,pages in SETS.items():
    keys=[(p,ri,k) for p in pages for ri in range(len(D[p])) for k in LOC]
    X=np.stack([D[p][ri][k].ravel() for p,ri,k in keys])
    best=None
    for seed in range(12):
        lab,c,conf,dm=km(X,8,seed)
        if best is None or dm.sum()<best[0]: best=(dm.sum(),lab,c,conf)
    _,lab,c,conf=best
    res[s]=dict(keys=keys,lab=lab,cent=c,conf=conf)
    # ordered by cluster size desc for stable reading; keep original index in title
    tiles=[np.pad(np.clip(c[j].reshape(20,14),0,1),((1,1),(2,2))) for j in range(8)]
    img=np.hstack(tiles)
    Image.fromarray(((1-img)*255).astype(np.uint8)).resize((img.shape[1]*14,img.shape[0]*14),Image.LANCZOS).save(f'loc8_{s}.png')
    print(s,'cluster sizes (idx 0..7):',[int((lab==j).sum()) for j in range(8)])
pickle.dump(res, open('loc8.pkl','wb'))
