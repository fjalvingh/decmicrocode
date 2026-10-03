import numpy as np, pickle, os
from layout import FIELDS, BITS
d=pickle.load(open('decoded.pkl','rb'))
R=pickle.load(open('bits.pkl','rb'))
SETS={'73':[f'73-{i}' for i in range(1,7)], '76':[f'76-p{i}' for i in range(1,7)]}
D=pickle.load(open('cells2.pkl','rb'))
def rowseq(s): return [(p,ri) for p in SETS[s] for ri in range(len(D[p]))]
conf={}
for s in SETS:
    idx={k:i for i,k in enumerate(R[s]['keys'])}
    c=R[s]['conf']
    conf[s]=[[c[idx[(p,ri,k)]] for k in BITS] for p,ri in rowseq(s)]
B={s:d['bits'][s] for s in SETS}
rows=[l.split() for l in open('names.txt') if l.strip()]
nm=[r[0] for r in rows]; loc=[int(r[1],8) for r in rows]
locset=set(loc)

merged=[]; disputes=[]
for i in range(214):
    w=[]
    for j in range(40):
        a,b=B['73'][i][j],B['76'][i][j]
        ca,cb=conf['73'][i][j],conf['76'][i][j]
        if a==b: w.append(a)
        else:
            w.append(b if cb>=ca else a)
            fld=None; off=0; t=0
            for fn,fw in FIELDS:
                if t<=j<t+fw: fld,off=fn,j-t; break
                t+=fw
            disputes.append((i,nm[i],loc[i],j,fld,off,a,ca,b,cb,'76' if cb>=ca else '73'))
    merged.append(w)

os.makedirs('/home/jal/1105rom/derived',exist_ok=True)
def split(w):
    out=[];t=0
    for fn,fw in FIELDS: out.append(''.join(map(str,w[t:t+fw]))); t+=fw
    return out
# machine-readable
with open('/home/jal/1105rom/derived/kd11b-microcode.tsv','w') as f:
    f.write('# KD11-B (PDP-11/05) control store - OCR draft from the engineering drawing listings\n')
    f.write('# Bits are AS PRINTED. The NXT field is stored active-low: next address = NXT XOR 0377.\n')
    f.write('NAM\tLOC\tNXTADDR\t'+'\t'.join(fn for fn,_ in FIELDS)+'\tWORD40\n')
    for i in range(214):
        w=merged[i]; nxt=int(''.join(map(str,w[:8])),2)^0xFF
        f.write(f'{nm[i]}\t{loc[i]:03o}\t{nxt:03o}\t'+'\t'.join(split(w))+'\t'+''.join(map(str,w))+'\n')
# human-readable, in the original column order
hdr=['NAM','LOC','NXT->']+[fn for fn,_ in FIELDS]
with open('/home/jal/1105rom/derived/kd11b-microcode.txt','w') as f:
    f.write('KD11-B (PDP-11/05) control store - OCR draft, 214 of 256 microwords\n')
    f.write('Bits AS PRINTED. NXT is active-low: effective next address = NXT XOR 0377 (column "NXT->").\n\n')
    widths=[6,4,6]+[max(len(fn),fw) for fn,fw in FIELDS]
    f.write(' '.join(h.ljust(w) for h,w in zip(hdr,widths))+'\n')
    f.write(' '.join('-'*w for w in widths)+'\n')
    for i in range(214):
        w=merged[i]; nxt=int(''.join(map(str,w[:8])),2)^0xFF
        cells=[nm[i],f'{loc[i]:03o}',f'{nxt:03o}']+split(w)
        f.write(' '.join(c.ljust(ww) for c,ww in zip(cells,widths))+'\n')
# disputes
with open('/home/jal/1105rom/derived/kd11b-disputes.txt','w') as f:
    f.write(f'Bits where the 1973 and 1976 scans disagree: {len(disputes)} of 8560 ({len(disputes)/8560*100:.2f}%)\n')
    f.write('Each needs a human look at the two scans before this data is trusted.\n')
    f.write('"taken" is the scan whose classifier was more confident; it is a guess, not a decision.\n\n')
    f.write(f'{"NAM":6s} {"LOC":4s} {"bit":4s} {"field":6s} {"ofs":4s} {"73":3s} {"conf":6s} {"76":3s} {"conf":6s} taken\n')
    for i,n,l,j,fld,off,a,ca,b,cb,tk in disputes:
        f.write(f'{n:6s} {l:03o}  {j:<4d} {fld:6s} {off:<4d} {a:<3d} {ca:<6.3f} {b:<3d} {cb:<6.3f} {tk}\n')
np.save('merged.npy',np.array(merged))
print('disputes',len(disputes))
print('rows with >=1 dispute',len(set(x[0] for x in disputes)))
import collections
print('by field',collections.Counter(x[4] for x in disputes).most_common())
