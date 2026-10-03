"""Column layout of the KD11-B microcode listing, relative to the first column
of the NAM field (which sits at a different left margin on each scanned page)."""
NAM = [0,1,2,3,4]
LOC = [6,7,8]
BITS = ([12,13,14,15, 19,20,21,22]      # NXT 8
      + [26,27,28,29, 33]               # ALU 5
      + [35,37,39]                      # CRI FSH AUX
      + [43,45,47,49]                   # PSW SP1 SP3 DIP
      + [53,55,57,59]                   # SM0 SP0 SM1 BBT
      + [63,65,67,69]                   # BAR BTP SPF SP2
      + [73,75,77,78]                   # CKO ABT TNS(2)
      + [82,83,85,86]                   # ALG(2) BRG(2)
      + [90,91,92,93])                  # BUT 4
assert len(BITS)==40
FIELDS=[('NXT',8),('ALU',5),('CRI',1),('FSH',1),('AUX',1),('PSW',1),('SP1',1),('SP3',1),('DIP',1),
        ('SM0',1),('SP0',1),('SM1',1),('BBT',1),('BAR',1),('BTP',1),('SPF',1),('SP2',1),
        ('CKO',1),('ABT',1),('TNS',2),('ALG',2),('BRG',2),('BUT',4)]
assert sum(w for _,w in FIELDS)==40
ALLCOLS = NAM+LOC+BITS
