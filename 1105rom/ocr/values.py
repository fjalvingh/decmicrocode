"""Symbolic value tables for the KD11-B microword fields, from the schematic notes
in ~/1105rom/pdp-1105-microcode.txt, with the printed-column order each one needs."""
ALUOP={0o1:'AL',0o0:'AA',0o3:'AB',0o5:'A*notB',0o7:'ZERO',0o11:'A_or_B',0o13:'BL',0o14:'A_plus_B',
       0o15:'A_xor_B',0o22:'A_minus_B_minus_1',0o25:'not_B',0o31:'MINUS1',0o36:'A_minus_1',
       0o37:'not_A',0o30:'ASL',0o32:'ROL',0o34:'ASR'}
BUT={0o17:'NON',0o13:'JMP/JSR',0o07:'IR-DECODE',0o03:'BYTE',0o15:'CONST',0o11:'DEST',0o05:'MOV',
     0o01:'INTR',0o16:'INIT',0o12:'UNARY',0o06:'SWITCHES',0o02:'NON-MOD',0o14:'SERVICE',
     0o10:'SSYNC',0o04:'ENOFLO',0o00:'IR-CLK'}
BRG={3:'LOAD',1:'SLEFT',2:'SRIGHT',0:'HOLD'}
TNS={3:'NONE',2:'DATI',1:'DATO'}
ALG={3:'SP',2:'NULL',1:'SPR',0:'PSW'}
SPM={3:'ROM',2:'IRS',1:'IRD',0:'BA'}
SPF={1:'READ',0:'WRITE'}
ABT={1:'NO',0:'YES'}
FSH={1:'NO',0:'SHIFT'}
CKO={1:'OFF',0:'ON'}      # CKOFF-L, processor clock off; see kd11b-README.md on the polarity
BLEG={(1,1):'BREG',(0,1):'SEX',(0,0):'+1'}      # (BTP,BBT); (1,0) is not named in the notes

def but(s):   # the value is the printed nibble, CS bits 03..00 left to right
    # (corrected 2026-10-02). It was unscrambled into BUT-3..BUT-0 signal order,
    # which put IR-DECODE on RST-1. Read as printed, every BUT the manual's flow
    # listing names lands where it says: IR-DECODE on F-5, SSYNC on INT-1 ("SET
    # SLAVE SYNC"), IR-CLK on F-4, DEST on S0-2, BYTE on S1-2, SERVICE on B2-2B,
    # INTR on BG-1, SWITCHES on H-2 - 13 of 13 (EK-KD11B-MM-001 ch. 2).
    return int(s,2)
def brg(s):   # printed cols are CS bit 05 (BMODE-0, to 74194 S0) then 04 (BMODE-1, S1)
    # (corrected 2026-10-02). Value = (S0<<1)|S1, the printed pair as is: the
    # 74194 shifts right on S1=L S0=H (printed 10 = SRIGHT) and left on S1=H S0=L
    # (01 = SLEFT), EK-KD11B-MM-001 4.3.6. The old (BMODE1<<1)|BMODE0 had the
    # shifts the wrong way round; B-1, the branch offset times two, is 01.
    return int(s,2)
def tns(s):   # printed cols are DATO-L, DATI-L
    return (int(s[0])<<1)|int(s[1])
def alg(s):   # printed cols are RALEG-1, RALEG-0
    return (int(s[0])<<1)|int(s[1])
def spm(sm0,sm1):  # SPA-MUX-1 is the high bit
    return (int(sm1)<<1)|int(sm0)
def bleg(btp,bbt):
    return BLEG.get((int(btp),int(bbt)),'BREG/+1')
