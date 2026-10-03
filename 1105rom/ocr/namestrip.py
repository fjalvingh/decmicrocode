import numpy as np, json, pickle
from PIL import Image
from scipy.ndimage import rotate as ndrotate
from lib import deskew, otsu
G=json.load(open('geom.json')); C=pickle.load(open('cols.pkl','rb')); B=json.load(open('bases.json'))
for name in [f'76-p{i}' for i in range(1,7)]:
    a=np.asarray(Image.open(f'/home/jal/1105rom/{name}.png').convert('L')).astype(np.float32)
    ang,_=deskew((a<otsu(a)).astype(np.float32))
    a=ndrotate(a,ang,reshape=False,order=1,mode='nearest')
    g=G[name]; c=C[name]; b=B[name]
    rp,rf,cp,cf=g['rp'],g['rf'],g['cp'],g['cf']
    x0=int(cf+(b-0.7)*cp); x1=int(cf+(b+9.7)*cp)
    tiles=[]
    for slot in c['rows']:
        y=rf+slot*rp
        tiles.append(a[int(y-rp*0.5):int(y-rp*0.5)+int(rp), x0:x1])
    h=min(t.shape[0] for t in tiles); w=min(t.shape[1] for t in tiles)
    tiles=[t[:h,:w] for t in tiles]
    half=(len(tiles)+1)//2
    colA=np.vstack([np.pad(t,((1,1),(0,0)),constant_values=255) for t in tiles[:half]])
    colB=np.vstack([np.pad(t,((1,1),(0,0)),constant_values=255) for t in tiles[half:]])
    if colB.shape[0]<colA.shape[0]:
        colB=np.vstack([colB,np.full((colA.shape[0]-colB.shape[0],w),255.0)])
    img=np.hstack([colA,np.full((colA.shape[0],14),255.0),colB])
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).resize((img.shape[1]*3,img.shape[0]*3),Image.LANCZOS)
    im=im.point(lambda v: 0 if v<150 else (255 if v>200 else v))
    im.save(f'names_{name}.png'); print(name, im.size, 'rows',len(tiles))
