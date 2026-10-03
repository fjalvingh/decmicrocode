from layout import FIELDS
# schematic bit map, from ~/pdp-1105-microcode.txt
SCH={0:('BUT-3-L','BUT'),1:('BUT-2-L','BUT'),2:('BUT-0-L','BUT'),3:('BUT-1-L','BUT'),
 4:('BMODE-1-H','BMODE'),5:('BMODE-0-H','BMODE'),6:('RALEG-0-L','ALG'),7:('RALEG-1-L','ALG'),
 8:('DATI-L','TNS'),9:('DATO-L','TNS'),10:('ALLOW-BYTE-L','ABT'),11:('CKOFF-L','CKO'),
 12:('ROM-SPA-2-H','SPA'),13:('SP-WRITE-L','SPF'),14:('BTOP-H','BPT'),15:('BA-CLOCK-L','BAR'),
 16:('BBOT-H','BBT'),17:('SPA-MUX-1-H','SPM'),18:('ROM-SPA-0-H','SPA'),19:('SPA-MUX-0-H','SPM'),
 20:('ENAB-IN-PAUSE-L','DIP'),21:('ROM-SPA-3-H','SPA'),22:('ROM-SPA-1-H','SPA'),23:('LOAD-PSW-L','PSW'),
 24:('AUX-CONTROL-L','AUX'),25:('F-SHIFT-L','FSH'),26:('CIN-H','CRI'),27:('ALU-MODE-H','ALU'),
 28:('ALU-S0-L','ALU'),29:('ALU-S1-L','ALU'),30:('ALU-S2-L','ALU'),31:('ALU-S3-L','ALU'),
 32:('MPC-0-L','MPC'),33:('MPC-1-L','MPC'),34:('MPC-2-L','MPC'),35:('MPC-3-L','MPC'),
 36:('MPC-4-L','MPC'),37:('MPC-5-L','MPC'),38:('MPC-6-L','MPC'),39:('MPC-7-L','MPC')}
PROM=[((0,3),'23A18A2','23A18A2'),((4,7),'23A05A2','23A05A2'),((8,11),'23A14A2','23A19A2'),
      ((12,15),'23A17A2','23A17A2'),((16,19),'23A13A2','23A13A2'),((20,23),'23A16A2','23A16A2'),
      ((24,27),'23A15A2','23A20A2'),((28,31),'23A11A2','23A11A2'),((32,35),'23A10A2','23A10A2'),
      ((36,39),'23A04A2','23A04A2')]
# my listing columns, left to right
cols=[]
for fn,fw in FIELDS:
    for k in range(fw): cols.append((fn,k,fw))
print(f'{"listing":22s} {"->":2s} {"schematic":18s} {"field":6s} match')
ok=0
for j,(fn,k,fw) in enumerate(cols):
    b=39-j
    sig,sf=SCH[b]
    lbl=f'{fn}[{k}]' if fw>1 else fn
    m = (fn==sf) or (fn,sf) in {('FSH','FREE'),('BRG','BMODE'),('BTP','BPT'),
                                ('SP0','SPA'),('SP1','SPA'),('SP2','SPA'),('SP3','SPA'),
                                ('SM0','SPM'),('SM1','SPM'),('NXT','MPC')}
    ok+=m
    print(f'  col {j:2d} {lbl:14s} -> bit {b:2d} {sig:16s} {sf:6s} {"ok" if m else "MISMATCH"}')
print(f'\n{ok}/40 positions consistent')
print()
print('PROMs that change between rev E (1973) and rev F (1976):')
for (lo,hi),e,f in PROM:
    if e!=f:
        names=sorted(set(SCH[b][1] for b in range(lo,hi+1)))
        sigs=[SCH[b][0] for b in range(lo,hi+1)]
        print(f'  bits {lo}-{hi}: {e} -> {f}   fields {names}')
        print(f'      signals: {", ".join(sigs)}')
