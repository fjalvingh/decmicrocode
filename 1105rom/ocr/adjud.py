import numpy as np, json, pickle
from PIL import Image
from scipy.ndimage import rotate as ndrotate
from lib import deskew, otsu
G=json.load(open('geom.json')); C=pickle.load(open('cols.pkl','rb')); B=json.load(open('bases.json'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}
D=pickle.load(open('cells2.pkl','rb'))
def rowseq(s): return [(p,ri) for p in SETS[s] for ri in range(len(D[p]))]
RS={s:rowseq(s) for s in SETS}
IMG={}
for s in SETS:
    for name in SETS[s]:
        a=np.asarray(Image.open(f'/home/jal/1105rom/{name}.png').convert('L')).astype(np.float32)
        ang,_=deskew((a<otsu(a)).astype(np.float32))
        IMG[name]=ndrotate(a,ang,reshape=False,order=1,mode='nearest')
def strip(s,i,c0,c1):
    p,ri=RS[s][i]; g=G[p]; c=C[p]; b=B[p]
    rp,rf,cp,cf=g['rp'],g['rf'],g['cp'],g['cf']
    y=rf+c['rows'][ri]*rp
    x0=int(cf+(b+c0-0.6)*cp); x1=int(cf+(b+c1+0.6)*cp)
    t=IMG[p][int(y-rp*0.55):int(y+rp*0.55), x0:x1]
    z=int(round(90/t.shape[0]))
    return np.asarray(Image.fromarray(np.clip(t,0,255).astype(np.uint8)).resize((t.shape[1]*z,t.shape[0]*z),Image.LANCZOS))
rows=[int(x) for x in open('disputes.txt').read().split()]
tiles=[]
for i in rows:
    a=strip('73',i,0,8); b=strip('76',i,0,8)   # NAM + LOC
    h=max(a.shape[0],b.shape[0]); w=max(a.shape[1],b.shape[1])
    def pad(x): 
        o=np.full((h,w),255.0); o[:x.shape[0],:x.shape[1]]=x; return o
    tiles.append(np.hstack([pad(a),np.full((h,20),255.0),pad(b)]))
w=max(t.shape[1] for t in tiles)
tiles=[np.hstack([t,np.full((t.shape[0],w-t.shape[1]),255.0)]) for t in tiles]
img=np.vstack([np.vstack([t,np.full((6,w),0.0)]) for t in tiles])
Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save('adjud.png')
print('rows',rows,'->',img.shape)
