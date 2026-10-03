import numpy as np, pickle
from scipy.optimize import linear_sum_assignment
from layout import LOC
D=pickle.load(open('cells2.pkl','rb'))
L=pickle.load(open('loc8.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}
MAP={'76':{0:'7',1:'0',2:'2',3:'5',4:'4',5:'3',6:'6',7:'1'},
     '73':{0:'3',1:'0',2:'6',3:'7',4:'1',5:'5',6:'4',7:'2'}}
def rowseq(s): return [(p,ri) for p in SETS[s] for ri in range(len(D[p]))]
def nrm(v):
    v=v-v.mean(); return v/(np.linalg.norm(v)+1e-9)
RS={s:rowseq(s) for s in SETS}
# feature matrices per set: (214,3,dim)
FEAT={}; PAGE={}
for s in SETS:
    idx={k:i for i,k in enumerate(L[s]['keys'])}
    X=np.stack([nrm(D[p][ri][k].ravel()) for p,ri,k in L[s]['keys']])
    FEAT[s]=np.stack([[X[idx[(p,ri,k)]] for k in LOC] for p,ri in RS[s]])
    PAGE[s]=np.array([RS[s][i][0] for i in range(214)])
# initial labels from cluster maps
lab0={}
for s in SETS:
    idx={k:i for i,k in enumerate(L[s]['keys'])}
    lab0[s]=np.array([[int(MAP[s][L[s]['lab'][idx[(p,ri,k)]]]) for k in LOC] for p,ri in RS[s]])
truth="145 015 147 146 305 333 335 343 013 040 045 112 151 350 316 276 272 313 303 374 314 372 312 337 317 307 326 315 371 311 375 367 100 322 321 101 157 162 155 332".split()
cur=None
for it in range(6):
    logit=np.zeros((214,3,8))
    for s in SETS:
        for pg in sorted(set(PAGE[s])):        # per-page templates
            m=PAGE[s]==pg
            F=FEAT[s][m]; Lb=(lab0[s][m] if cur is None else cur[s][m])
            T=np.zeros((8,F.shape[2])); have=np.zeros(8,bool)
            for dgt in range(8):
                sel=F[Lb==dgt]
                if len(sel)>=3: T[dgt]=nrm(sel.mean(0)); have[dgt]=True
            for dgt in range(8):
                if not have[dgt]:              # fall back to global template
                    sel=FEAT[s][lab0[s]==dgt] if cur is None else FEAT[s][cur[s]==dgt]
                    if len(sel): T[dgt]=nrm(sel.mean(0))
            logit[m]+=np.einsum('rpd,kd->rpk',F,T)*12.0
    cost=np.zeros((214,256))
    for a in range(256):
        d=[(a>>6)&7,(a>>3)&7,a&7]
        cost[:,a]=-(logit[:,0,d[0]]+logit[:,1,d[1]]+logit[:,2,d[2]])
    r,c=linear_sum_assignment(cost); addr=np.zeros(214,int); addr[r]=c
    got=[f'{a:03o}' for a in addr]
    ok=sum(1 for i in range(40) if got[i]==truth[i])
    print(f'  iter {it}: page-1 {ok}/40   distinct {len(set(got))}')
    newlab=np.stack([[ (a>>6)&7,(a>>3)&7,a&7] for a in addr])
    cur={s:newlab for s in SETS}
    if ok==40 and it>0: break
print('final page-1 mismatches:',[(i,got[i],truth[i]) for i in range(40) if got[i]!=truth[i]])
np.save('addr.npy',addr)
