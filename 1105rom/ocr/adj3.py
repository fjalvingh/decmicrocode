import numpy as np, json, pickle, sys
from PIL import Image
from scipy.ndimage import rotate as ndrotate
from lib import deskew, otsu
from layout import BITS, ALLCOLS
G=json.load(open('geom.json')); C=pickle.load(open('cols.pkl','rb')); B=json.load(open('bases.json'))
L=pickle.load(open('l73.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)],
      '73l':['73l-1','73l-2','73l-3','73l-4','73l-5','73l-6']}
D=pickle.load(open('cells2.pkl','rb'))
def nrows(s,p): return len(D[p]) if s!='73l' else len(L['cells'][p])
def rowseq(s): return [(p,ri) for p in SETS[s] for ri in range(nrows(s,p))]
IMG={}
for s in SETS:
    for n in SETS[s]:
        a=np.asarray(Image.open(f'/home/jal/1105rom/{n}.png').convert('L')).astype(np.float32)
        ang,_=deskew((a<otsu(a)).astype(np.float32))
        IMG[n]=ndrotate(a,ang,reshape=False,order=1,mode='nearest')
def geom(s,p):
    if s=='73l':
        g=L['geom'][p]; return g['rp'],g['rf'],g['cp'],g['cf'],L['cols'][p]['base'],L['cols'][p]['rows']
    g=G[p]; return g['rp'],g['rf'],g['cp'],g['cf'],B[p],C[p]['rows']
def cut(s,i,c0,c1,h=90):
    p,ri=rowseq(s)[i]; rp,rf,cp,cf,b,rws=geom(s,p)
    y=rf+rws[ri]*rp
    t=IMG[p][int(y-rp*0.55):int(y+rp*0.55), int(cf+(b+c0-0.6)*cp):int(cf+(b+c1+0.6)*cp)]
    z=max(1,int(round(h/max(t.shape[0],1))))
    return np.asarray(Image.fromarray(np.clip(t,0,255).astype(np.uint8)).resize((t.shape[1]*z,t.shape[0]*z),Image.LANCZOS))
targets=[tuple(x) for x in np.load('extra.npy')]
rows=[l.split() for l in open('names.txt') if l.strip()]; nm=[r[0] for r in rows]
panels=[]
for i,j in targets:
    col=BITS[j]
    segs=[]
    for s in ['73','73l','76']:
        a=cut(s,i,0,8); m=cut(s,i,max(0,col-4),col+4)
        h=max(a.shape[0],m.shape[0])
        def pd(x):
            o=np.full((h,x.shape[1]),255.0); o[:x.shape[0]]=x; return o
        segs.append(np.hstack([pd(a),np.full((h,20),255.),pd(m)]))
    w=max(x.shape[1] for x in segs)
    segs=[np.hstack([x,np.full((x.shape[0],w-x.shape[1]),255.)]) for x in segs]
    panels.append(np.vstack([segs[0],np.full((2,w),210.),segs[1],np.full((2,w),210.),segs[2],np.full((8,w),0.)]))
w=max(p.shape[1] for p in panels)
panels=[np.hstack([p,np.full((p.shape[0],w-p.shape[1]),255.)]) for p in panels]
img=np.vstack(panels)
n=len(targets)
half=(n+1)//2
Image.fromarray(np.clip(np.vstack(panels[:half]),0,255).astype(np.uint8)).save('adj3a.png')
Image.fromarray(np.clip(np.vstack(panels[half:]),0,255).astype(np.uint8)).save('adj3b.png')
for k,(i,j) in enumerate(targets):
    print(k, nm[i], 'bit',j,'rel col',BITS[j], 'panel', 'a' if k<half else 'b')
