import numpy as np, pickle, os, collections
from layout import FIELDS
import values as V
d=pickle.load(open('decoded.pkl','rb'))
A=np.array(d['bits']['73'])          # 1973, low-res scan
Bm=np.array(d['bits']['76']).copy()  # 1976
Lg=np.load('b73l.npy').copy()        # 1973, hi-res scan  -> primary for that revision
rows=[l.split() for l in open('names.txt') if l.strip()]
nm=[r[0] for r in rows]; loc=[int(r[1],8) for r in rows]
ix={n:i for i,n in enumerate(nm)}

# Corrections established by looking at all three scans side by side (adj3a/adj3b.png).
FIX73=[('CCS-1',13,0,'faded slashed zero in both 1973 scans; 1976 shows a clear 0'),
       ('CCS-3',13,0,'same'),
       ('CD1-1',13,0,'same'),
       ('CD1-1',36,0,'same; 1976 shows BUT=0110'),
       ('F-2'  ,34,1,'1973 hi-res classifier slip; old 1973 and 1976 both show 1'),
       ('R2-2' , 0,0,'faded slashed zero in both 1973 scans; 1976 shows NXT=0110')]
FIX76=[('SBO-3',18,0,'1976 classifier slip (conf 0.17); all three scans show 0'),
       ('SBO-3',27,0,'1976 classifier slip (conf 0.04); all three scans show 0'),
       ('SBO-4',27,0,'1976 classifier slip (conf 0.13); all three scans show 0')]
for n,j,v,_ in FIX73: Lg[ix[n]][j]=v
for n,j,v,_ in FIX76: Bm[ix[n]][j]=v

def fieldof(j):
    t=0
    for fn,fw in FIELDS:
        if t<=j<t+fw: return fn,j-t
        t+=fw
rev=[(i,j) for i in range(214) for j in range(40) if Lg[i][j]!=Bm[i][j]]
print('revision differences after correction:',len(rev),'in',len(set(i for i,_ in rev)),'microwords')
print('  by field:',collections.Counter(fieldof(j)[0] for _,j in rev).most_common())
# residual disagreement between the two 1973 scans (quality metric only)
q=[(i,j) for i in range(214) for j in range(40) if Lg[i][j]!=A[i][j]]
print('1973 hi-res vs 1973 low-res after correction:',len(q))

OUT='/home/jal/1105rom/derived'
def split(w):
    o=[];t=0
    for fn,fw in FIELDS: o.append(''.join(map(str,w[t:t+fw]))); t+=fw
    return o
ALUOP={0o1:'AL',0o0:'AA',0o3:'AB',0o5:'A*notB',0o7:'ZERO',0o11:'A_or_B',0o13:'BL',
       0o14:'A_plus_B',0o15:'A_xor_B',0o22:'A_minus_B_minus_1',0o25:'not_B',0o31:'MINUS1',
       0o36:'A_minus_1',0o37:'not_A',0o30:'ASL',0o32:'ROL',0o34:'ASR'}
def alu(w):
    v=int(''.join(map(str,w[8:13])),2)
    return v, ALUOP.get(v,'?')
def spa(w):   # ROM-SPA-3..0, scattered over listing columns 18,27,17,21
    return (w[18]<<3)|(w[27]<<2)|(w[17]<<1)|w[21]
def sym(w):
    g=lambda a,b=None: ''.join(map(str,w[a:b] if b else [w[a]]))
    return dict(BUTNAME=V.BUT[V.but(g(36,40))], BRGNAME=V.BRG[V.brg(g(34,36))],
                TNSNAME=V.TNS.get(V.tns(g(30,32)),'??'), ALGNAME=V.ALG[V.alg(g(32,34))],
                SPAMUX=V.SPM[V.spm(w[20],w[22])], SPFNAME=V.SPF[w[26]],
                ABTNAME=V.ABT[w[29]], FSHNAME=V.FSH[w[14]], CKONAME=V.CKO[w[28]],
                BLEG=V.bleg(w[25],w[23]))
HEAD=("KD11-B (PDP-11/05) control store, transcribed by OCR from the microcode listing\n"
      "pages of the PDP-11/05 engineering drawings, %s set.\n"
      "214 of the 256 control-store locations are listed; the other 42 are not printed.\n\n"
      "Bits are AS PRINTED. The NXT field is stored ACTIVE LOW: the effective next\n"
      "microaddress is NXT XOR 0377, given in the NXT-> column. This was established by\n"
      "structural test, not assumed - see kd11b-README.md.\n\n")
for tag,W,label in [('1973',Lg,'October 1973'),('1976',Bm,'July 1976')]:
    hdr=['NAM','LOC','NXT->']+[fn for fn,_ in FIELDS]
    widths=[6,4,6]+[max(len(fn),fw) for fn,fw in FIELDS]
    with open(f'{OUT}/kd11b-microcode-{tag}.txt','w') as f:
        f.write(HEAD%label)
        f.write(' '.join(h.ljust(w) for h,w in zip(hdr,widths))+'\n')
        f.write(' '.join('-'*w for w in widths)+'\n')
        for i in range(214):
            w=W[i]; nxt=int(''.join(map(str,w[:8])),2)^0xFF
            f.write(' '.join(c.ljust(ww) for c,ww in zip([nm[i],f'{loc[i]:03o}',f'{nxt:03o}']+split(w),widths))+'\n')
    with open(f'{OUT}/kd11b-microcode-{tag}.tsv','w') as f:
        f.write('# KD11-B control store, %s drawing set. Bits as printed; NXT is active low.\n'%label)
        f.write('# NXTADDR is the decoded next microaddress (MPC complemented). ALUCODE/ALUOP decode\n')
        f.write('# the 5-bit ALU field against the operation table in EK-KD11B-MM-001. SPA is the\n')
        f.write('# 4-bit scratchpad address ROM-SPA-3..0, which the listing prints as four separate\n')
        f.write('# non-adjacent single-bit columns (SP3 SP2 SP1 SP0) and is assembled here.\n')
        SY=['BUTNAME','ALUOP','BRGNAME','BLEG','TNSNAME','ALGNAME','SPAMUX','SPFNAME','ABTNAME','FSHNAME','CKONAME']
        f.write('# Symbolic columns decode the fields per kd11b-fieldvalues.tsv. BUT and BRG need the\n')
        f.write('# printed bits unscrambled first; see kd11b-README.md.\n')
        f.write('NAM\tLOC\tNXTADDR\tALUCODE\tSPA\t'+'\t'.join(SY)+'\t'
                +'\t'.join(fn for fn,_ in FIELDS)+'\tWORD40\n')
        for i in range(214):
            w=W[i]; nxt=int(''.join(map(str,w[:8])),2)^0xFF
            av,an=alu(w); sy=sym(w); sy['ALUOP']=an
            f.write(f'{nm[i]}\t{loc[i]:03o}\t{nxt:03o}\t{av:02o}\t{spa(w):d}\t'
                    +'\t'.join(sy[k] for k in SY)+'\t'
                    +'\t'.join(split(w))+'\t'+''.join(map(str,w))+'\n')
with open(f'{OUT}/kd11b-revision-diff.txt','w') as f:
    f.write("Bits where the 1973 and 1976 drawing sets genuinely differ.\n\n")
    f.write("Three independent transcriptions back this: two scans of the 1973 listing (at\n")
    f.write("815 px and 1460 px wide) and one of the 1976 listing. The two 1973 scans agree\n")
    f.write("with each other and disagree with 1976 at every one of these positions, and each\n")
    f.write("was checked by eye against all three images. They are not OCR errors: the two\n")
    f.write("drawing sets carry different microcode revisions.\n\n")
    f.write("The clearest case is U1-1..U5-1, five consecutive microwords where 1973 has\n")
    f.write("AUX=1, CKO=0 and 1976 has AUX=0, CKO=1, with URTR immediately after identical\n")
    f.write("in both. Which revision is in the machine is open - see MC1105.md phase 6.\n\n")
    f.write(f'{"NAM":6s} {"LOC":4s} {"bit":4s} {"field":6s} {"ofs":4s} {"1973":5s} {"1976":5s}\n')
    for i,j in rev:
        fn,off=fieldof(j)
        f.write(f'{nm[i]:6s} {loc[i]:03o}  {j:<4d} {fn:6s} {off:<4d} {Lg[i][j]:<5d} {Bm[i][j]:<5d}\n')
    f.write(f'\n{len(rev)} bits in {len(set(i for i,_ in rev))} microwords.\n')
    f.write('by field: %s\n'%collections.Counter(fieldof(j)[0] for _,j in rev).most_common())
with open(f'{OUT}/kd11b-corrections.txt','w') as f:
    f.write("Bits corrected by hand after looking at all three scans side by side.\n\n")
    f.write("Each of these is a place where a classifier misread a glyph and the other two\n")
    f.write("scans plus a zoomed look at the image settled it. They are applied in the\n")
    f.write("shipped listings; this file is the record of what was changed and why.\n\n")
    f.write("-- 1973 listing (primary source: the 1460px scans) --\n")
    for n,j,v,why in FIX73:
        f.write(f'   {n:6s} {loc[ix[n]]:03o} bit {j:2d} {fieldof(j)[0]:4s} -> {v}   {why}\n')
    f.write("\n-- 1976 listing --\n")
    for n,j,v,why in FIX76:
        f.write(f'   {n:6s} {loc[ix[n]]:03o} bit {j:2d} {fieldof(j)[0]:4s} -> {v}   {why}\n')
if os.path.exists(f'{OUT}/kd11b-ocr-uncertain.txt'): os.remove(f'{OUT}/kd11b-ocr-uncertain.txt')
np.save('final73.npy',Lg); np.save('final76.npy',Bm)
locset=set(loc)
for tag,W in [('1973',Lg),('1976',Bm)]:
    nxt=[int(''.join(map(str,w[:8])),2)^0xFF for w in W]
    print(f'  {tag}: NXT resolves for {sum(1 for v in nxt if v in locset)}/214')
