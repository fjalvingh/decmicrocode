import numpy as np, pickle
from PIL import Image
from layout import NAM
D=pickle.load(open('cells2.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}
def rowseq(s): return [(p,ri) for p in SETS[s] for ri in range(len(D[p]))]
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
    return lab,c,d.min(1)
K=48
out={}
for s in SETS:
    keys=[(p,ri,k) for p,ri in rowseq(s) for k in NAM]
    X=np.stack([D[p][ri][k].ravel() for p,ri,k in keys])
    best=None
    for seed in range(8):
        lab,c,dm=km(X,K,seed)
        if best is None or dm.sum()<best[0]: best=(dm.sum(),lab,c)
    _,lab,c=best
    out[s]=dict(keys=keys,lab=lab,cent=c)
    tiles=[np.pad(np.clip(c[j].reshape(20,14),0,1),((1,1),(2,2))) for j in range(K)]
    rows=[np.hstack(tiles[i:i+8]) for i in range(0,K,8)]
    img=np.vstack(rows)
    Image.fromarray(((1-img)*255).astype(np.uint8)).resize((img.shape[1]*10,img.shape[0]*10),Image.LANCZOS).save(f'nam_{s}.png')
    print(s,'sizes',[int((lab==j).sum()) for j in range(K)])
pickle.dump(out, open('namclust.pkl','wb'))
