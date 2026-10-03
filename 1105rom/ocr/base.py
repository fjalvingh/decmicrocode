import numpy as np, json, pickle
from layout import ALLCOLS, NAM, LOC, BITS
C=pickle.load(open('cols.pkl','rb'))
mask=np.zeros(96); 
for k in ALLCOLS: mask[k]=1
bases={}
for name,c in C.items():
    ci=np.array(c['colink']); ci=ci/ci.max()
    best=(-1,None)
    for b in range(0,6):
        s=0.0
        for k in ALLCOLS:
            j=b+k
            if j<len(ci): s+=ci[j]
        # penalise ink at positions that should be blank
        blanks=[j for j in range(b, min(len(ci), b+95)) if (j-b) not in set(ALLCOLS)]
        s-=sum(ci[j] for j in blanks)
        if s>best[0]: best=(s,b)
    bases[name]=best[1]
    print(f'{name:7s} base={best[1]} score={best[0]:.1f}  ncol={c["ncol"]}')
json.dump(bases, open('bases.json','w'))
