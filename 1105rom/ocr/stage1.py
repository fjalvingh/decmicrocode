import numpy as np, sys, json
from lib import load_ink, deskew, fit_comb

pages = [f'73-{i}' for i in range(1,7)] + [f'76-p{i}' for i in range(1,7)]
out={}
for name in pages:
    ink,a,t = load_ink(f'/home/jal/1105rom/{name}.png')
    ang,ink = deskew(ink)
    H,W = ink.shape
    big = name.startswith('76')
    rp,rf,_ = fit_comb(ink.sum(axis=1), 19 if big else 12.5, 24 if big else 16, 900)
    # occupancy per slot
    cen=[rf+k*rp for k in range(int((H-rf)/rp)+1)]
    occ=[float(ink[max(0,int(c)-int(rp*0.42)):int(c)+int(rp*0.42), :].sum()) for c in cen]
    cp,cf,_ = fit_comb(ink.sum(axis=0), 11 if big else 7, 15 if big else 10, 1200)
    out[name]=dict(thr=float(t),ang=float(ang),H=H,W=W,rp=rp,rf=rf,cp=cp,cf=cf,occ=occ)
    print(f'{name}: skew {ang:+.2f}  rowpitch {rp:.3f} phase {rf:.2f}  colpitch {cp:.3f} phase {cf:.2f}  slots {len(cen)}')
    print('   occ:', ' '.join(str(int(o)) for o in occ))
json.dump(out, open('geom.json','w'), indent=1)
