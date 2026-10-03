import numpy as np, pickle
from layout import LOC
D=pickle.load(open('cells2.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}
def kmeans(X,k,seed=0):
    rng=np.random.default_rng(seed)
    c=X[rng.choice(len(X),k,replace=False)].copy()
    for _ in range(200):
        d=((X[:,None,:]-c[None,:,:])**2).sum(2); lab=d.argmin(1)
        cn=np.stack([X[lab==j].mean(0) if (lab==j).any() else X[rng.integers(len(X))] for j in range(k)])
        if np.allclose(cn,c): break
        c=cn
    d=((X[:,None,:]-c[None,:,:])**2).sum(2); lab=d.argmin(1)
    sd=np.sort(d,1); conf=(sd[:,1]-sd[:,0])/(sd[:,1]+1e-9)
    return lab,c,conf
out={}
for s,pages in SETS.items():
    keys=[(p,ri,k) for p in pages for ri in range(len(D[p])) for k in LOC]
    X=np.stack([D[p][ri][k].ravel() for p,ri,k in keys])
    best=None
    for seed in range(6):
        lab,c,conf=kmeans(X,8,seed)
        inert=sum((((X[lab==j]-c[j])**2).sum()) for j in range(8))
        if best is None or inert<best[0]: best=(inert,lab,c,conf)
    _,lab,c,conf=best
    out[s]=dict(keys=keys,lab=lab,cent=c,conf=conf)
    print(f'=== set {s}  n={len(keys)}  cluster sizes {[int((lab==j).sum()) for j in range(8)]}')
    for j in range(8):
        g=c[j].reshape(20,14)
        print(f'  cluster {j} (n={(lab==j).sum()}):')
        for r in g[2:19]:
            print('    |'+''.join('#' if v>0.5 else ('+' if v>0.2 else '.') for v in r)+'|')
pickle.dump(out, open('locclust.pkl','wb'))
