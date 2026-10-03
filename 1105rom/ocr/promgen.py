"""Assemble the ten 256x4 control-store PROM images from the transcribed microcode.

Conventions, all of them stated because two of them are NOT known from the sources:

  ADDRESS ORDER  images are in TRUE microaddress order: image[a] holds the microword whose
                 LOC is a. The MPC signals are active low, so if the microaddress latch drives
                 the PROM address pins directly the device may want the complement; that wiring
                 has not been read off the schematic. Set COMPLEMENT_ADDRESS to flip it.
  NIBBLE ORDER   the lowest schematic bit of a slice is taken as D0 of the PROM. Which schematic
                 bit reaches which data output pin is not in the notes. Set MSB_FIRST to flip it.
  HOLES          42 of the 256 locations have no microword in the listing; they are filled with
                 0xF, i.e. left unprogrammed on a fusible-link part. That value also decodes to
                 a harmless microword: no bus cycle, no branch, everything inactive, and an
                 unconditional jump to RS-1 at address 000.
"""
import csv, hashlib, os
COMPLEMENT_ADDRESS = False
MSB_FIRST          = False
FILL               = 0xF
D='/home/jal/1105rom/derived'
def load(p): return [r for r in csv.DictReader((l for l in open(p) if not l.startswith('#')),delimiter='\t')]
F=load(f'{D}/kd11b-fields.tsv')
slices={}
for r in F:
    slices.setdefault((r['PROM_E'],r['PROM_F']),[]).append(int(r['SCHBIT']))
slices={k:sorted(v) for k,v in slices.items()}

def images(tsv, rev):
    rows=load(tsv)
    word={}
    for r in rows:
        w=r['WORD40']                       # listing order: LISTCOL 0..39
        # schematic bit b is at LISTCOL 39-b
        word[int(r['LOC'],8)]=[int(w[39-b]) for b in range(40)]
    out={}
    for (pe,pf),bits in slices.items():
        part = pe if rev=='E' else pf
        img=bytearray(256)
        holes=[]
        for a in range(256):
            pa = a ^ 0xFF if COMPLEMENT_ADDRESS else a
            src = word.get(pa)
            if src is None:
                img[a]=FILL; holes.append(a); continue
            order = bits[::-1] if MSB_FIRST else bits
            v=0
            for i,b in enumerate(order): v |= src[b]<<i
            img[a]=v
        out[part]=(bytes(img), bits, holes)
    return out

report=[]
for rev,tsv in [('E',f'{D}/kd11b-microcode-1973.tsv'),('F',f'{D}/kd11b-microcode-1976.tsv')]:
    d=f'{D}/proms/rev{rev}'; os.makedirs(d,exist_ok=True)
    for part,(img,bits,holes) in sorted(images(tsv,rev).items(), key=lambda x:x[1][1][0]):
        base=f'{d}/{part}_bits{bits[0]:02d}-{bits[-1]:02d}'
        open(base+'.bin','wb').write(img)
        with open(base+'.hex','w') as f:
            f.write(f'# KD11-B control store, rev {rev}, PROM {part}, schematic bits '
                    f'{bits[0]}..{bits[-1]} (D0..D3 = bit {bits[0]}..{bits[-1]})\n')
            f.write(f'# 256 x 4. One hex nibble per location, 16 per row, true microaddress order.\n')
            f.write(f'# {len(holes)} locations have no microword in the listing and are set to '
                    f'{FILL:X} (unprogrammed).\n')
            for r0 in range(0,256,16):
                f.write(f'{r0:03o}: '+' '.join(f'{v:X}' for v in img[r0:r0+16])+'\n')
        report.append((rev,part,bits,hashlib.sha256(img).hexdigest()[:16],len(holes),img))
    print(f'rev {rev}: 10 images written to {d}')
import pickle; pickle.dump(report, open('/tmp/promreport.pkl','wb'))
