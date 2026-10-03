import numpy as np, pickle, json
from layout import BITS, LOC, NAM
D=pickle.load(open('cells2.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}

def kmeans(X,k,init):
    c=init.copy()
    for _ in range(60):
        d=((X[:,None,:]-c[None,:,:])**2).sum(2)
        lab=d.argmin(1)
        cn=np.stack([X[lab==j].mean(0) if (lab==j).any() else c[j] for j in range(k)])
        if np.allclose(cn,c): break
        c=cn
    d=((X[:,None,:]-c[None,:,:])**2).sum(2)
    lab=d.argmin(1)
    sd=np.sort(d,axis=1)
    conf=(sd[:,1]-sd[:,0])/(sd[:,1]+1e-9)
    return lab,c,conf

result={}
for s,pages in SETS.items():
    keys=[(p,ri,k) for p in pages for ri in range(len(D[p])) for k in BITS]
    X=np.stack([D[p][ri][k].ravel() for p,ri,k in keys])
    area=X.sum(1)
    init=np.stack([X[area>=np.percentile(area,85)].mean(0), X[area<=np.percentile(area,15)].mean(0)])
    lab,c,conf=kmeans(X,2,init)
    # label 0 = the wider glyph ('0'), 1 = narrow ('1'): decide by horizontal ink spread
    def spread(v):
        m=v.reshape(20,14).sum(0); m=m/max(m.sum(),1e-9)
        x=np.arange(14); mu=(m*x).sum()
        return np.sqrt((m*(x-mu)**2).sum())
    sp=[spread(c[0]),spread(c[1])]
    zero_idx=int(np.argmax(sp))
    bits=np.where(lab==zero_idx,0,1)
    print(f'set {s}: {len(keys)} bit cells, cluster sizes {(lab==0).sum()}/{(lab==1).sum()}, '
          f'spread {sp[0]:.2f}/{sp[1]:.2f}, zero=cluster{zero_idx}, ones={bits.sum()} ({bits.mean()*100:.1f}%)')
    print(f'   confidence: min {conf.min():.4f}  p0.1 {np.percentile(conf,0.1):.4f}  p1 {np.percentile(conf,1):.4f}  median {np.percentile(conf,50):.3f}')
    result[s]=dict(keys=keys,bits=bits,conf=conf,cent=c)
    for j in range(2):
        print(f'   centroid {j}:')
        for r in c[j].reshape(20,14):
            print('     |'+''.join('#' if v>0.5 else ('+' if v>0.2 else '.') for v in r)+'|')
pickle.dump(result, open('bits.pkl','wb'))
