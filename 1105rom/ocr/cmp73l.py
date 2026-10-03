import numpy as np, pickle
from layout import BITS, FIELDS
L=pickle.load(open('l73.pkl','rb')); cells=L['cells']
PAGES=['73l-1','73l-2','73l-3','73l-4','73l-5','73l-6']
keys=[(p,ri,k) for p in PAGES for ri in range(len(cells[p])) for k in BITS]
X=np.stack([cells[p][ri][k].ravel() for p,ri,k in keys])
area=X.sum(1)
c=np.stack([X[area>=np.percentile(area,85)].mean(0), X[area<=np.percentile(area,15)].mean(0)])
for _ in range(60):
    d=((X[:,None,:]-c[None,:,:])**2).sum(2); lab=d.argmin(1)
    cn=np.stack([X[lab==j].mean(0) if (lab==j).any() else c[j] for j in range(2)])
    if np.allclose(cn,c): break
    c=cn
d=((X[:,None,:]-c[None,:,:])**2).sum(2); lab=d.argmin(1)
sd=np.sort(d,1); conf=(sd[:,1]-sd[:,0])/(sd[:,1]+1e-9)
def spread(v):
    m=v.reshape(20,14).sum(0); m=m/max(m.sum(),1e-9); x=np.arange(14); mu=(m*x).sum()
    return np.sqrt((m*(x-mu)**2).sum())
zi=int(np.argmax([spread(c[0]),spread(c[1])]))
bits=np.where(lab==zi,0,1)
print(f'73l: {len(keys)} bit cells, ones {bits.mean()*100:.1f}%')
print(f'  confidence: min {conf.min():.4f}  p0.1 {np.percentile(conf,0.1):.4f}  p1 {np.percentile(conf,1):.4f}  median {np.percentile(conf,50):.3f}')
for j in range(2):
    print(f'  centroid {j}:'); 
    for r in c[j].reshape(20,14)[3:18]:
        print('    |'+''.join('#' if v>0.5 else ('+' if v>0.2 else '.') for v in r)+'|')
idx={k:i for i,k in enumerate(keys)}
B73l=[[int(bits[idx[(p,ri,k)]]) for k in BITS] for p in PAGES for ri in range(len(cells[p]))]
C73l=[[float(conf[idx[(p,ri,k)]]) for k in BITS] for p in PAGES for ri in range(len(cells[p]))]
np.save('b73l.npy',np.array(B73l)); np.save('c73l.npy',np.array(C73l))
pickle.dump(conf,open('conf73l.pkl','wb'))
# confidence comparison across all three sets
R=pickle.load(open('bits.pkl','rb'))
for s in ['73','76']:
    cf=R[s]['conf']
    print(f'  set {s} confidence: min {cf.min():.4f} p0.1 {np.percentile(cf,0.1):.4f} p1 {np.percentile(cf,1):.4f} median {np.percentile(cf,50):.3f}')
