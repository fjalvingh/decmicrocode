import values as V, csv, collections
rows=[r for r in csv.DictReader((l for l in open('/home/jal/1105rom/derived/kd11b-microcode-1976.tsv') if not l.startswith('#')),delimiter='\t')]
def cnt(col): return collections.Counter(r[col] for r in rows)
OUT='/home/jal/1105rom/derived/kd11b-fieldvalues.tsv'
with open(OUT,'w') as f:
    f.write('# Symbolic values for the KD11-B microword fields.\n')
    f.write('# Value names come from the M7261 schematics via ../pdp-1105-microcode.txt.\n')
    f.write('# VALUE is the field value in octal. PRINTED is the bit pattern as it appears in the\n')
    f.write('# listing, left to right. For BUT and BRG the value is the printed pattern as is\n')
    f.write('# (corrected 2026-10-02: they were unscrambled, which was wrong; see kd11b-README.md).\n')
    f.write('# COUNT is how many of the 214 microwords use it in the 1976 (rev F) listing.\n')
    f.write('FIELD\tVALUE\tPRINTED\tNAME\tCOUNT\tNOTE\n')
    # BUT: enumerate all printed nibbles
    seen=cnt('BUT')
    for pr in sorted({format(i,'04b') for i in range(16)}):
        v=V.but(pr); f.write(f'BUT\t{v:02o}\t{pr}\t{V.BUT[v]}\t{seen.get(pr,0)}\tCS bits 03..00 as printed\n')
    for pr in ['00','01','10','11']:
        v=V.brg(pr); f.write(f'BRG\t{v}\t{pr}\t{V.BRG[v]}\t{cnt("BRG").get(pr,0)}\tCS bit 05 (S0) then 04 (S1) of the 74194\n')
    for pr in ['00','01','10','11']:
        v=V.tns(pr); f.write(f'TNS\t{v}\t{pr}\t{V.TNS.get(v,"(not named)")}\t{cnt("TNS").get(pr,0)}\t'
                             f'{"only in A145, the all-zero filler microword" if v==0 else ""}\n')
    for pr in ['00','01','10','11']:
        v=V.alg(pr); f.write(f'ALG\t{v}\t{pr}\t{V.ALG[v]}\t{cnt("ALG").get(pr,0)}\tprinted order is RALEG-1,RALEG-0\n')
    smc=collections.Counter(r['SPAMUX'] for r in rows)
    for v,n in sorted(V.SPM.items(), reverse=True):
        f.write(f'SPAMUX\t{v}\t{"SM0="+str(v&1)+" SM1="+str(v>>1)}\t{n}\t{smc.get(n,0)}\t'
                f'{"IRS/IRD ordering not confirmed by the data" if n in("IRS","IRD") else ""}\n')
    for v,n in sorted(V.ALUOP.items()):
        pr=format(v,'05b'); f.write(f'ALU\t{v:02o}\t{pr}\t{n}\t{cnt("ALU").get(pr,0)}\t\n')
    for fld,tab,col in [('SPF',V.SPF,'SPF'),('ABT',V.ABT,'ABT'),('FSH',V.FSH,'FSH'),('CKO',V.CKO,'CKO')]:
        for v,n in sorted(tab.items(), reverse=True):
            f.write(f'{fld}\t{v}\t{v}\t{n}\t{cnt(col).get(str(v),0)}\t\n')
    blc=collections.Counter(r['BLEG'] for r in rows)
    for (btp,bbt),n in sorted(V.BLEG.items(), reverse=True):
        f.write(f'BTP/BBT\t-\tBTP={btp} BBT={bbt}\t{n}\t{blc.get(n,0)}\tB-leg source\n')
    f.write(f'BTP/BBT\t-\tBTP=1 BBT=0\t(not named)\t{blc.get("BREG/+1",0)}\tobserved but absent from the notes\n')
print(open(OUT).read())
