import numpy as np, collections
from layout import FIELDS
SCH={0:('BUT-3-L','L'),1:('BUT-2-L','L'),2:('BUT-0-L','L'),3:('BUT-1-L','L'),
 4:('BMODE-1-H','H'),5:('BMODE-0-H','H'),6:('RALEG-0-L','L'),7:('RALEG-1-L','L'),
 8:('DATI-L','L'),9:('DATO-L','L'),10:('ALLOW-BYTE-L','L'),11:('CKOFF-L','L'),
 12:('ROM-SPA-2-H','H'),13:('SP-WRITE-L','L'),14:('BTOP-H','H'),15:('BA-CLOCK-L','L'),
 16:('BBOT-H','H'),17:('SPA-MUX-1-H','H'),18:('ROM-SPA-0-H','H'),19:('SPA-MUX-0-H','H'),
 20:('ENAB-IN-PAUSE-L','L'),21:('ROM-SPA-3-H','H'),22:('ROM-SPA-1-H','H'),23:('LOAD-PSW-L','L'),
 24:('AUX-CONTROL-L','L'),25:('F-SHIFT-L','L'),26:('CIN-H','H'),27:('ALU-MODE-H','H'),
 28:('ALU-S0-L','L'),29:('ALU-S1-L','L'),30:('ALU-S2-L','L'),31:('ALU-S3-L','L'),
 32:('MPC-0-L','L'),33:('MPC-1-L','L'),34:('MPC-2-L','L'),35:('MPC-3-L','L'),
 36:('MPC-4-L','L'),37:('MPC-5-L','L'),38:('MPC-6-L','L'),39:('MPC-7-L','L')}
PROM={}
for (lo,hi),e,f in [((0,3),'23A18A2','23A18A2'),((4,7),'23A05A2','23A05A2'),((8,11),'23A14A2','23A19A2'),
      ((12,15),'23A17A2','23A17A2'),((16,19),'23A13A2','23A13A2'),((20,23),'23A16A2','23A16A2'),
      ((24,27),'23A15A2','23A20A2'),((28,31),'23A11A2','23A11A2'),((32,35),'23A10A2','23A10A2'),
      ((36,39),'23A04A2','23A04A2')]:
    for b in range(lo,hi+1): PROM[b]=(e,f,e!=f)
cols=[]
for fn,fw in FIELDS:
    for k in range(fw): cols.append((fn,k,fw))
OUT='/home/jal/1105rom/derived'
with open(f'{OUT}/kd11b-fields.tsv','w') as f:
    f.write('# KD11-B microword field table.\n')
    f.write('# LISTCOL is the 0-based column of the bit as printed in the listing (0 = leftmost).\n')
    f.write('# SCHBIT is the bit number used by the schematics and EK-KD11B-MM-001.\n')
    f.write('# The listing prints SCHBIT 39 leftmost and SCHBIT 0 rightmost: SCHBIT = 39 - LISTCOL.\n')
    f.write('# ACTIVE is the signal polarity from its name: L = asserted low, H = asserted high.\n')
    f.write('# PROM_E / PROM_F are the DEC part numbers of the PROM holding that bit; CHANGED marks\n')
    f.write('# the two slices that differ between board revision E (1973) and F (1976).\n')
    f.write('LISTFIELD\tBITINFIELD\tLISTCOL\tSCHBIT\tSIGNAL\tACTIVE\tPROM_E\tPROM_F\tCHANGED\n')
    for j,(fn,k,fw) in enumerate(cols):
        b=39-j; sig,act=SCH[b]; e,fp,ch=PROM[b]
        f.write(f'{fn}\t{k}\t{j}\t{b}\t{sig}\t{act}\t{e}\t{fp}\t{"yes" if ch else ""}\n')
print(open(f'{OUT}/kd11b-fields.tsv').read().count('\n')-8,'field rows written')
# validate the scattered scratchpad address
B=np.load('final76.npy')
SPA={ 'SP0':21,'SP1':17,'SP2':27,'SP3':18 }   # listing columns
spa=[ (B[i][SPA['SP3']]<<3)|(B[i][SPA['SP2']]<<2)|(B[i][SPA['SP1']]<<1)|B[i][SPA['SP0']] for i in range(214)]
c=collections.Counter(spa)
print('\nsynthesised 4-bit scratchpad address ROM-SPA-3..0, assembled from four non-adjacent columns:')
print('  values seen:',sorted(c),' (16 possible)')
for v in sorted(c): print(f'    {v:2d} ({v:04b})  {c[v]:3d} microwords')
sm=[ (B[i][22]<<1)|B[i][20] for i in range(214)]   # SM1,SM0
print('\nSPA-MUX (SPA-MUX-1,SPA-MUX-0):',dict(sorted(collections.Counter(sm).items())))
