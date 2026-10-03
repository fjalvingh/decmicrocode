import numpy as np, json, pickle
from lib import load_ink, deskew

G=json.load(open('geom.json'))

def datarow_slots(occ):
    big=[o for o in occ if o>200]; med=np.median(big)
    filled=[i for i,o in enumerate(occ) if o>med*0.25]
    groups=[]; s=filled[0]; prev=filled[0]
    for i in filled[1:]:
        if i==prev+1: prev=i
        else: groups.append((s,prev)); s=i; prev=i
    groups.append((s,prev))
    hdr=groups[0]
    rows=list(range(hdr[1]-3,hdr[1]+1))
    for a,b in groups[1:]: rows+=list(range(a,b+1))
    return rows, hdr[1]-4   # also the dash slot

store={}
for name in G:
    g=G[name]
    ink,a,t = load_ink(f'/home/jal/1105rom/{name}.png')
    ang,ink = deskew(ink)
    rows,dash = datarow_slots(g['occ'])
    rp,rf,cp,cf = g['rp'],g['rf'],g['cp'],g['cf']
    H,W=ink.shape
    ncol=int((W-cf)/cp)
    # per-column ink fraction over data rows
    half=rp*0.45
    band=np.zeros(W)
    for r in rows:
        y=rf+r*rp
        band+=ink[max(0,int(y-half)):int(y+half),:].sum(axis=0)
    colink=[]
    for c in range(ncol):
        x=cf+c*cp
        colink.append(float(band[max(0,int(x-cp/2)):int(x+cp/2+1)].sum()))
    store[name]=dict(rows=rows,dash=dash,ncol=ncol,colink=colink)
    mx=max(colink)
    s=''.join('#' if v>mx*0.25 else ('+' if v>mx*0.05 else '.') for v in colink)
    print(f'{name:7s} ncol={ncol} rows={len(rows)}')
    print('        '+s)
pickle.dump(store, open('cols.pkl','wb'))
