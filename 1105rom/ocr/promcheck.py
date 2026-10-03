"""Round trip: reassemble the 40-bit microwords from the ten PROM images and compare
against the listing they were generated from."""
import csv, glob, re
D='/home/jal/1105rom/derived'
def load(p): return [r for r in csv.DictReader((l for l in open(p) if not l.startswith('#')),delimiter='\t')]
ok=True
for rev,tsv in [('E',f'{D}/kd11b-microcode-1973.tsv'),('F',f'{D}/kd11b-microcode-1976.tsv')]:
    imgs={}
    for f in sorted(glob.glob(f'{D}/proms/rev{rev}/*.bin')):
        lo,hi=map(int,re.search(r'bits(\d+)-(\d+)',f).groups())
        imgs[(lo,hi)]=open(f,'rb').read()
    assert len(imgs)==10 and sum(hi-lo+1 for lo,hi in imgs)==40, 'slices do not cover 40 bits'
    rows=load(tsv); bad=0
    for r in rows:
        a=int(r['LOC'],8)
        bits=[0]*40
        for (lo,hi),img in imgs.items():
            v=img[a]
            for i,b in enumerate(range(lo,hi+1)): bits[b]=(v>>i)&1
        # schematic bit b sits at LISTCOL 39-b
        word=''.join(str(bits[39-c]) for c in range(40))
        if word!=r['WORD40']:
            bad+=1
            if bad<4: print(f'  MISMATCH rev{rev} {r["NAM"]}@{r["LOC"]}\n    from images {word}\n    from tsv    {r["WORD40"]}')
    print(f'rev {rev}: {len(rows)-bad}/{len(rows)} microwords reassemble exactly from the images'
          + ('' if bad==0 else f'  -- {bad} MISMATCHES'))
    ok &= bad==0
    # the holes must all read as the fill
    have=set(int(r['LOC'],8) for r in rows)
    holes=[a for a in range(256) if a not in have]
    allf=all(all(img[a]==0xF for (lo,hi),img in imgs.items()) for a in holes)
    print(f'        {len(holes)} unlisted locations, all ten images read F at every one: {allf}')
    ok &= allf
print('\nround trip', 'PASSED' if ok else 'FAILED')
