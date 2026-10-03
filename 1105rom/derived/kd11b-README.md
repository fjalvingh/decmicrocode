# KD11-B control store — transcription and analysis

The PDP-11/05 (KD11-B) microcode, transcribed from the engineering drawings, with the working
that produced it and an account of how far each claim can be trusted.

Everything referred to here lives in `~/1105rom/`: the scans at the top level,
`pdp-1105-microcode.txt` (the bit map and PROM assignments read off the M7261 schematics), the
transcription in `derived/`, and the pipeline in `ocr/`.

## Summary of what was found

1. The drawing sets contain the **microcode listing**, not PROM images — tag, octal address and
   all 40 bits under named field headings.
2. The listing holds **214 microwords**, not 256. The other 42 control-store locations are not
   printed.
3. The field layout is **`NXT` 8, `ALU` 5, seventeen single-bit lines, `TNS`/`ALG`/`BRG` 2 each,
   `BUT` 4** — exactly 40 bits. The fifth ALU bit has a dash but no heading letter.
4. **`NXT` is stored active low.** The next microaddress is `NXT XOR 0377`.
5. The 1973 and 1976 sets are **different microcode revisions** — M7261 rev E and rev F — and
   differ in **20 bits across 14 microwords, confined to `AUX` and `CKO`**.
6. The schematics confirm 3, 4 and 5 independently: all 40 columns match the bit map, `MPC-n-L`
   is active low by name, and the two PROMs whose part numbers change between E and F are exactly
   the two holding `AUX` and `CKO`.
7. The **`ALU` field decodes completely** — all 12 codes are named operations, covering 214 of
   214 microwords.
8. One trap: the scratchpad address is printed as four scattered out-of-order columns. (This
   used to say the `BUT` nibble is bit-scrambled too. It is not, and neither is `BRG`; both read
   as printed. See *Correction, October 2026* in §6.)
9. `FSH` (bit 25) is **`F-SHIFT-L`**, the shifter control on the ALU output — not a spare. The
   transcription confirms it: it is asserted in exactly five chains of seven consecutive shift
   steps.
10. **Every field now has symbolic value names**, from the schematics. `BUT` uses all 16 of its
    microtests, and exactly one microword in the whole microprogram is `IR-DECODE`: `F-5`, the
    last step of the instruction fetch.
11. `AUX` selects whether the ALU control comes from the microword or is decoded from the
    instruction — and the E→F revision **moved which microwords use it**, wholesale.
12. The **ten PROM images per revision** are in `proms/`, assembled from the listing and round-trip
    verified. Eight of ten are byte-identical between revisions, which is what the part numbers
    say — derived independently and asserted, not assumed.

---

## 1. What the sources actually are

The scans are **not PROM dumps**. They are the *microcode listing pages* of the PDP-11/05
engineering drawings — the microassembler's output, with a symbolic tag, the octal control-store
address, and all 40 bits printed one per column under named field headings.

That is a better source than a dump, and it is what removed most of the risk from this job. A
dump has no tags, no field names and no internal redundancy; ten 4-bit PROM slices concatenated
in the wrong order yield 256 entirely plausible microwords with no symptom at all. The listing
prints the assembled word with its field boundaries drawn, so there is no slice map to get wrong.

Two drawing sets, six pages each, the same 214 lines in the same order — and **three** scans,
because the 1973 listing was scanned twice:

| set | files | scan | char pitch | zeros |
| --- | --- | --- | --- | --- |
| October 1973 (rev E) | `73-1` … `73-6` | 815×780 | 8.45 px | slashed `Ø` |
| October 1973 (rev E) | `73l-1` … `73l-6` | ~1465×1400 | **15.18 px** | slashed `Ø` |
| July 1976 (rev F) | `76-p1` … `76-p6` | ~1270×1160 | 13.07 px | plain `0`, except p3 which is slashed |

**`73l` is the source for the 1973 revision and `76` for the 1976 revision.** The original 815 px
`73` scans are superseded — against `73l` they carry 20 bit errors, 19 of which `73l` gets right —
but they are kept, because a third opinion is what made the residual disagreements decidable.

Resolution is not the whole story. `73l` has 16% more pixels per character than `76`, yet its
classifier separates `0` from `1` *less* cleanly (1st-percentile confidence 0.25 against 0.40),
because the 1973 printing renders zero as a slashed `Ø`, whose ink distribution sits much closer
to a `1` than a plain oval does. Where a `Ø` has faded, **both** 1973 scans read it as `1` and
agree with each other, so a majority vote between them is worthless and only the 1976 scan can
catch it. Five of the six corrections to the 1973 listing are exactly this.

## 2. How the transcription was done

A line-printer listing is a rigid monospace grid of glyphs drawn from a tiny alphabet. That makes
grid fitting plus template classification far more reliable than general-purpose OCR, and — more
importantly — it makes the failure modes measurable. The pipeline is in `~/1105rom/ocr/`.

**Grid fitting.** Each page is deskewed by maximising the sharpness of its horizontal ink
profile (skews found: −0.35° to +0.70°). A comb is then fitted to the row profile and to the
column profile, giving a line pitch and a character pitch per page. The listing is a true
printer grid — blank lines between groups of four occupy exactly one line slot — so every text
line sits at `phase + k·pitch` and blank slots simply have low ink. All 18 pages resolve to the
same structure: three heading rows, a dash rule, then 40 data rows per page and 14 on page 6.
**214 lines, and all three scans agree on that exactly.**

**Per-page left margin.** The pages are not cropped identically; the listing starts 0–2
characters further right on some. The column layout is therefore defined relative to the first
column of `NAM`, and each page's origin is found by correlating its per-column ink profile
against the expected mask. Getting this wrong is silent — it shifts every field by one column
and still produces plausible bits — and it was in fact the first bug in this pipeline.

**Cell extraction.** Each character cell is sampled with bilinear interpolation from the
greyscale image (not from a binarised one), 3× oversampled, recentred on its own ink centroid,
and box-downsampled to a fixed 20×14 patch. The centroid recentring absorbs residual skew and
per-row jitter, and it is what makes template matching work across pages with different ink
density.

**Bit classification.** All 8560 bit cells of a scan are clustered into two classes by k-means,
seeded from the ink-area extremes and separated by horizontal ink spread — a `0` is a wide ring
or slashed oval, a `1` a narrow stroke. The cluster centroids are unmistakable in every scan.
Each cell also gets a confidence, the normalised margin between the two cluster distances, and
that number is what drives the adjudication below.

**Addresses (`LOC`).** Three octal digits per line, and the naive per-glyph classification was
about 92% right — not good enough. It is fixed by using the constraint the data carries: the 214
addresses must be **distinct** and **below `0400`**. That makes it an assignment problem — 214
rows against 256 possible addresses, cost from the per-digit template likelihoods — solved
exactly with the Hungarian algorithm, then iterated EM-style with per-page digit templates
rebuilt from the previous solution. It converged in two rounds to 214 distinct in-range
addresses.

**Tags (`NAM`).** Read by eye from upscaled crops of the 1976 scans, all 214 of them. This is
checked, not merely asserted: **the listing is sorted, and the transcribed list sorts exactly in
ASCII order** (`D0-4` < `D1-1` < … < `D7-5` < `DB0-1` < `DBF-1` < `DF-1` < `DO-1` < `DO-10` <
… < `DO-18` < `DO-2` < …). A misread character almost always breaks that ordering, so the sort is
a genuine check on 214 names, and it is what distinguishes `D0-` (digit zero) from `DO-`
(letter O), which are otherwise nearly identical in this font.

**Cross-validation and adjudication.** The scans were transcribed independently and then
compared. The best 1973 scan and the 1976 scan agree on **99.66%** of the 8560 bits. Of the 29
disagreements, 20 are the revision difference (§7) and 9 were classifier slips; every one of the
9 was settled by rendering the disputed cell from all three scans side by side and looking at it.
Those 9 are recorded in `kd11b-corrections.txt` with the reason for each. **No bit is left to a
coin-toss.**

## 3. The listing layout

Established from the **dash rule** printed under the headings, not from the headings themselves.
Character columns are counted from the first column of `NAM`.

| field | columns | bits |
| --- | --- | --- |
| NAM | 0–4 | symbolic tag |
| LOC | 6–8 | 3 octal digits, the control-store address |
| NXT | 12–15, 19–22 | 8 |
| ALU | 26–29, **33** | **5** |
| CRI, FSH, AUX | 35, 37, 39 | 1 each |
| PSW, SP1, SP3, DIP | 43, 45, 47, 49 | 1 each |
| SM0, SP0, SM1, BBT | 53, 55, 57, 59 | 1 each |
| BAR, BTP, SPF, SP2 | 63, 65, 67, 69 | 1 each |
| CKO, ABT, TNS | 73, 75, 77–78 | 1, 1, 2 |
| ALG, BRG | 82–83, 85–86 | 2, 2 |
| BUT | 90–93 | 4 |

40 bits exactly. **Column 33 carries a dash but no heading letter.** It is the fifth ALU bit, not
a fourth unnamed member of the `CRI/FSH/AUX` group — reading the headings alone gets this wrong
and produces a phantom bit in the wrong field. The dash rule is the only thing in the document
that settles it, and the schematics later confirmed it: column 33 is `ALU-MODE-H`, bit 27.

## 4. The field table, confirmed against the schematics

`~/1105rom/pdp-1105-microcode.txt` carries the microword bit map and the PROM assignments read
off the M7261 schematics and `EK-KD11B-MM-001`. It was compiled independently of this
transcription, and the two agree on **all 40 positions**.

The listing prints schematic bit 39 leftmost and bit 0 rightmost: **`SCHBIT = 39 − LISTCOL`**.
Every one of the 23 fields lands on the right signal at the right width. `kd11b-fields.tsv` is
the merged table, one row per bit.

| field | bits | signal(s) | active | distinct values | most common |
| --- | --- | --- | --- | --- | --- |
| NXT | 8 | `MPC-7..0-L` | L | 155 | `11011111` (15) |
| ALU | 5 | `ALU-S3..S0-L`, `ALU-MODE-H` | L / H | 12 | `00001` = `AL` (105) |
| CRI | 1 | `CIN-H` | H | 2 | `0` (192) |
| FSH | 1 | `F-SHIFT-L` | L | 2 | `1` (179) |
| AUX | 1 | `AUX-CONTROL-L` | L | 2 | `1` (205) |
| PSW | 1 | `LOAD-PSW-L` | L | 2 | `1` (208) |
| SP1 | 1 | `ROM-SPA-1-H` | H | 2 | `0` (146) |
| SP3 | 1 | `ROM-SPA-3-H` | H | 2 | `0` (174) |
| DIP | 1 | `ENAB-IN-PAUSE-L` | L | 2 | `1` (208) |
| SM0 | 1 | `SPA-MUX-0-H` | H | 2 | `1` (184) |
| SP0 | 1 | `ROM-SPA-0-H` | H | 2 | `0` (166) |
| SM1 | 1 | `SPA-MUX-1-H` | H | 2 | `1` (186) |
| BBT | 1 | `BBOT-H` | H | 2 | `1` (188) |
| BAR | 1 | `BA-CLOCK-L` | L | 2 | `1` (173) |
| BTP | 1 | `BTOP-H` | H | 2 | `1` (208) |
| SPF | 1 | `SP-WRITE-L` | L | 2 | `1` (157) |
| SP2 | 1 | `ROM-SPA-2-H` | H | 2 | `0` (151) |
| CKO | 1 | `CKOFF-L` | L | 2 | `1` (178) |
| ABT | 1 | `ALLOW-BYTE-L` | L | 2 | `1` (201) |
| TNS | 2 | `DATO-L`, `DATI-L` | L | 4 | `11` (175) |
| ALG | 2 | `RALEG-1-L`, `RALEG-0-L` | L | 4 | `11` (177) |
| BRG | 2 | `BMODE-0-H`, `BMODE-1-H` | H | 4 | `00` (97) |
| BUT | 4 | `BUT-1,0,2,3-L` | L | 16 | `1111` (141) |

**Polarity comes free with the signal names** — `-L` asserted low, `-H` asserted high — and it
retro-explains the statistics. `AUX-CONTROL-L`, `LOAD-PSW-L`, `ENAB-IN-PAUSE-L`, `BTOP-H` and
`ALLOW-BYTE-L` sit at their inactive value in 94–97% of microwords, `BUT` is `1111` (no branch)
in 141 of 214, and `TNS` is `11` (no bus cycle) in 175. Nothing has to be inferred about
defaults; they are what the polarity says they are.

One listing label is DEC's own mnemonic rather than a signal name, verified by eye against the
hi-res scan: **`BRG` is `BMODE-0/1-H`** (bits 4–5). `RALEG` selects the ALU's A leg; `BMODE` is
the mode of the B register, the 74194s whose output feeds the B leg (EK-KD11B-MM-001 §4.3.6):
`B MODE 00` (bit 05) drives S0 and `B MODE 01` (bit 04) drives S1.

### `FSH` is the shifter, not a spare

Bit 25 was first transcribed against a bit map that called it `SPARE-L`, which sat badly with the
data: it is 0 in 35 of 214 microwords, and a genuinely unused bit should not vary like that. The
M7261 schematics — 1973 and 1976 alike — call it **`F-SHIFT-L`**, field **`FSH`**, matching the
listing's own heading exactly. `F` is the standard 74181 ALU-output name, so this is the shifter
on the ALU result.

The transcription confirms it independently, and this is the sharpest semantic check in the whole
exercise. Those 35 microwords are not scattered. They are **five straight-line chains of exactly
seven consecutive shift steps**, each following its own next-address links and each stopping on
the eighth:

| chain | steps | ALU code throughout | BRG |
| --- | --- | --- | --- |
| `DO-1` → `DO-7`, then `DO-8` | 7 | `01` `AL` | `10` `SRIGHT` |
| `DO-11` → `DO-17`, then `DO-18` | 7 | `01` `AL` | `01` `SLEFT` |
| `SB1-1` → `SB1-7`, then `SB1-8` | 7 | `34` `ASR` | `01` `SLEFT` |
| `SB2-1` → `SB2-7`, then `SB2-8` | 7 | `34` `ASR` | `01` `SLEFT` |
| `SBO-1` → `SBO-7`, then `SBO-8` | 7 | `01` `AL` | `10` `SRIGHT` |

Across all 214 microwords `F-SHIFT-L` is asserted with only **two** of the twelve ALU codes —
`01` (`AL`) and `34` (`ASR`) — and never with `BL`, `A plus B`, `A − B − 1`, `not A` or any
other. Each chain holds one ALU code and one B register mode for all seven steps. A spare
bit cannot produce that; a shifter enable produces exactly that.

It also explains something the ALU decode left hanging: the operation table lists `ROL` and `ROR`
as codes, but neither appears in any microword. The rotates are not ALU functions here — the ALU
passes a leg through and `F-SHIFT` does the shifting.

## 5. `NXT` is stored active low

**The effective next microaddress is `NXT XOR 0377`, not `NXT`.**

The schematics say so outright — the signals are `MPC-0-L` … `MPC-7-L` — but this was established
here by test before that was known, and the test is worth keeping because it is the one a loader
can run:

- as printed, 83.2% of the 214 next-addresses land on a listed address. That is *no better than
  chance*: 214 of 256 locations are listed, so 83.6% is what a random address would score;
- complemented, **99.5%** land on a listed address — 213 of 214;
- and the chain reads correctly: `B-1 @015 → 147 = B-2 → 146 = B-3 → 040 = BG-1`. Sequentially
  named microwords forming a next-address chain does not happen by accident.

This is exactly the class of silent error that a PROM-sourced transcription cannot catch. Taken
as printed it produces 214 plausible microwords, a plausible-looking control graph, and a wrong
machine.

The single microword whose next-address does not resolve is **`A145 @145 → 377`**, whose 40 bits
are almost entirely zero — a filler or diagnostic entry. `RS-1` sits at address **000** and is
presumably the reset entry point.

## 6. What the fields mean

**The `ALU` field decodes completely.** All 12 distinct ALU codes in the transcription appear in
the operation table in `EK-KD11B-MM-001`, covering **214 of 214 microwords**, with no complement
and no reordering — the printed 5 bits are the code:

| code | operation | microwords | code | operation | microwords |
| --- | --- | --- | --- | --- | --- |
| `00001` | `AL` | 105 | `00111` | `0` | 2 |
| `01011` | `BL` | 48 | `00000` | `AA` | 1 |
| `01100` | `A plus B` | 21 | `11000` | `ASL` | 1 |
| `11100` | `ASR` | 16 | `00101` | `A * not B` | 1 |
| `10010` | `A − B − 1` | 9 | `00011` | `AB` | 1 |
| `11111` | `not A` | 8 | `01001` | `A or B` | 1 |

Twelve of twelve codes landing in a table of seventeen, across every microword, is not something
a misaligned column produces. It validates the ALU columns, the bit order and the fifth ALU bit
in one go.

**Trap 1 — the scratchpad address is scattered and out of order.** `ROM-SPA-0..3` are printed as
four separate, non-adjacent single-bit columns: `SP0` at listing column 21, `SP1` at 17, `SP2` at
27, `SP3` at 18. Assembled, they read as sensible register numbers — 0 in 118 microwords, then
**7 (the PC) in 28 and 6 (the SP) in 22**, which is exactly what a microprogram's register usage
should look like. The `.tsv` files carry the assembled value as `SPA`. A field table that treats
the four columns as independent flags will show nonsense.

**Not a trap — `BUT` and `BRG` read as printed.** The schematic signal names put `BUT-1-L,
BUT-0-L, BUT-2-L, BUT-3-L` on CS bits 03..00, and an earlier version of this file took that to mean
the printed nibble had to be unscrambled into signal order. It does not: the field value is the
printed nibble, bit 03 leftmost, and the same goes for `BRG`. See *Correction, October 2026* below.
The warning that came with the old claim still applies, the other way round: all sixteen
microtests are defined, so the wrong decoding gave a *plausible* wrong name for every microword,
and the mislabelled branch structure raised no error.

### Symbolic values

`kd11b-fieldvalues.tsv` carries the value names for every field, keyed by the **printed** bit
pattern. The `.tsv` listings carry the decoded names as columns.

**`BUT` — the branch microtest.** All sixteen are used:

| value | name | microwords | | value | name | microwords |
| --- | --- | --- | --- | --- | --- | --- |
| `17` | `NON` | 141 | | `12` | `UNARY` | 5 |
| `15` | `CONST` | 17 | | `00` | `IR-CLK` | 4 |
| `14` | `SERVICE` | 15 | | `06` | `SWITCHES` | 4 |
| `04` | `ENOFLO` | 7 | | `03` | `BYTE` | 3 |
| `02` | `NON-MOD` | 5 | | `11` | `DEST` | 3 |
| `13` | `JMP/JSR` | 4 | | `05` | `MOV` | 2 |
| `01` | `INTR` | 1 | | `10` | `SSYNC` | 1 |
| `16` | `INIT` | 1 | | `07` | `IR-DECODE` | 1 |

`NON` — no branch — in 141 of 214, which is the shape a microtest field should have. The
microtests land where the microprogram says they should: `IR-DECODE` on `F-5`, the end of the
fetch; `IR-CLK` on `F-4`, which loads the IR; `CONST` (the constants ROM on the A leg) on the
trap and interrupt entries `BT-1`, `IT-1`, `ET-1`, `ERT-1`, `PF-1`, `LC-1`, `T-1`, which fetch
their vectors from it; `SERVICE` on the end-of-instruction steps; `SWITCHES` on the console steps
and `H-2`; `SSYNC` on `INT-1`; `INIT` on `RST-1`, the RESET instruction.

**`BRG` — the B register.** `HOLD` 97, `LOAD` 76, `SLEFT` 25, `SRIGHT` 16. Printed `10` is shift
right and `01` shift left, from the hardware: the 74194 shifts right on S1 = L, S0 = H and left on
S1 = H, S0 = L, S0 is bit 05 and S1 bit 04, and the listing prints bit 05 first. The five
`F-SHIFT` chains then read:

| chain | ALU | BRG |
| --- | --- | --- |
| `DO-1` … `DO-7`, `SBO-1` … `SBO-7` | `AL` (A leg through) | `SRIGHT` |
| `DO-11` … `DO-17` | `AL` (A leg through) | `SLEFT` |
| `SB1-1` … `SB1-7`, `SB2-1` … `SB2-7` | `ASR` | `SLEFT` |

`DO-1` is where the manual says an odd destination byte goes "to get the byte operand into the
right half of the B register", and its BISB example shifts an odd source byte right eight places
(EK-KD11B-MM-001 figure 4-10): `SRIGHT` in `DO-1` and `SBO-1`. `B-1`, which doubles the branch
offset, is `SLEFT` with ALU code `30` (`ASL`).

What does not fit is the name of ALU code `34`. The `SB1`/`SB2` chains shift left, yet `34` is
called `ASR` here. Table 2-1 says the four shift codes `ASL`, `ROL`, `ASR`, `ROR` "control the
serial shift inputs to the B register", so the ALU code chooses what shifts in, not the direction.
The code-to-name assignment for those four (`30`, `32`, `34`, `36`) comes from the notes, not
from the manual, and `36` is also `A minus 1` in the same table. Treat the names of `32`, `34` and
`36` as unverified.

### Correction, October 2026

The first version of this file decoded `BUT` by unscrambling the printed nibble into signal order
(`BUT-3..BUT-0`), and `BRG` as `(BMODE-1 << 1) | BMODE-0`. Both were wrong. They had been "checked"
against the data, but the checks only showed that the result was plausible: with all sixteen
microtests defined and only one shift direction to choose, either reading looks plausible.

The microprogram flow listing in EK-KD11B-MM-001 chapter 2 decides it. It gives the action and
branch test of the steps it walks through. For the 13 that name a `BUT`, the printed nibble read
straight matches all 13; the old unscrambling matched 4:

| step | listing says | straight | old |
| --- | --- | --- | --- |
| `F-4` | `B, IR ← UNIBUS DATA` | `IR-CLK` | `IR-CLK` |
| `F-5` | `B ← B SEX; BUT` (IR decode) | `IR-DECODE` | `CONST` |
| `S0-2` | `BUT DESTINATION` | `DEST` | `UNARY` |
| `S1-2` | `BUT BYTE` | `BYTE` | `SERVICE` |
| `B2-2B` | `BUT SERVICE` | `SERVICE` | `BYTE` |
| `BG-1` | `BUT INTERRUPT` | `INTR` | `SSYNC` |
| `INT-1` | `SET SLAVE SYNC` | `SSYNC` | `NON-MOD` |
| `ET-3` | `ENAB OVER` | `ENOFLO` | `INTR` |
| `H-2` | `BUT SWITCH` | `SWITCHES` | `MOV` |

(plus `F-1`, `F-2`, `F-3` and `S0-1`, which both readings or only the straight one get right.)
Table 5-4 says the same: `BUT IR` is asserted "at F-5". For `BRG`, the flow listing's `B ←` steps
are all `LOAD` and the others `HOLD` under both readings, since `11` and `00` read the same either
way; the shift direction comes from the 74194 wiring in §4.3.6 as described above.

`ocr/values.py` has the corrected `but()` and `brg()`. The pipeline's intermediate files are gone,
so the `BUTNAME` and `BRGNAME` columns of the two `.tsv` listings were recomputed from their
printed `BUT` and `BRG` columns (69 and 41 rows changed in each), and `kd11b-fieldvalues.tsv` was
regenerated with `ocr/fieldvalues.py`. No bit changed, so the PROM images in `proms/` are
unaffected.

**The rest.**

| field | values | note |
| --- | --- | --- |
| `TNS` | `NONE` 175, `DATI` 31, `DATO` 7 | reads outnumbering writes 4:1 is what a CPU should look like |
| `ALG` | `SP` 177, `NULL` 31, `PSW` 5, `SPR` 1 | the A leg is the scratchpad in most microwords |
| `SPAMUX` | `ROM` 170, `IRS` 16, `IRD` 14, `BA` 14 | selects where the scratchpad address comes from |
| `SPF` | `READ` 157, `WRITE` 57 | |
| `ABT` | `NO` 201, `YES` 13 | byte operations enabled |
| `BTP`/`BBT` | `BREG` 182, `SEX` 6 | B-leg top and bottom source |
| `CKO` | `OFF` 178, `ON` 36 | `CKOFF-L`, the processor clock stop — see below |
| `AUX` | 9 microwords assert it | selects the ALU control source — see below |

`SPAMUX` gives a clean independent check on the scattered `SPA` field: **all 96 microwords with a
non-zero ROM scratchpad address have the mux set to `ROM`**, and none of the other 118 do. The two
decodes were derived separately and agree completely.

### `CKO` and `AUX`, the two the revision changed

**`CKO` is `CKOFF-L`, the processor clock stop.** In the schematic it sits among the `MSYN`/`SSYN`
bus signals, which stop the clock while a peripheral takes its time answering. That matches what
the data does *approximately* but not exactly, and the shortfall is worth writing down rather than
smoothing over. Of the 36 microwords with `CKO=0`, 22 also start a bus cycle (14 `DATI`, 7 `DATO`,
and the `A145` filler); the other 14 do not. Conversely 17 microwords start a `DATI` with
`CKO=1`. So the field is not simply "there is a bus cycle here".

Two things make that hard to push further from the listing alone. The 14 non-bus `CKO=0`
microwords are systematically the `-3` member of a routine whose `-1` member started the cycle
(`D2-1`/`D2-3`, `S3-1`/`S3-3`, `R2-1`/`R2-3` and so on), which reads like *start the cycle in one
microword, wait for `SSYN` in a later one*. But the microwords that start cycles mostly carry a
microtest, so their printed next-address is a branch base rather than the actual successor, and
the chain cannot be followed to confirm it. Also note the value names as given — `OFF` = 1, `ON` =
0 — would mean the clock is off in 178 of 214 microwords, so the field is more likely to *enable*
a clock stop than to command one. Left as recorded, not resolved.

**`AUX` is `AUX-CONTROL-L`, and it is not a simple control line at all.** It selects whether `ALU
S0..S3`, `ALU MODE`, `CIN`, `CLK` and `DISAB VBIT ROM` come from instruction-register bits 15..12
(`AUX=0`, PROM E053) or bits 10..6 (`AUX=1`, PROM E054) — the two opcode fields of the
double-operand and single-operand instruction formats. So where `AUX` is involved the ALU
operation is decoded from the *instruction*, not taken from the microword, which is how one
microword executes `MOV`, `CMP`, `BIT`, `BIC`, `BIS`, `ADD` and `SUB` alike.

That has a consequence for reading the listing: **in a microword that takes its ALU control from
the IR, the printed `ALU` field may be a don't-care.** It should not be shown as though it were
what the machine does.

### The revision changed which microwords use the IR-decoded ALU control

Knowing what the two fields are makes the E→F difference legible, and it is not a bug fix:

| microwords | rev E (AUX, CKO) | rev F (AUX, CKO) | change |
| --- | --- | --- | --- |
| `D0-3`, `D0-3A`, `D1-4`, `DB0-2`, `DO-10` — all `not_A` + `ENOFLO` | (0, 1) | (1, 1) | `AUX` dropped |
| `MB-1` — `not_A` | (0, 1) | (1, 1) | `AUX` dropped |
| `SB1-8`, `SB2-8` — the shift-chain terminators, `ASR` | (1, 1) | (0, 1) | `AUX` added |
| `MB-0`, `U1-1` … `U5-1` — `BL` | (1, 0) | (0, 1) | **`AUX` and `CKO` swapped together** |

Rev E asserts `AUX` in six microwords, all of them `not_A`; rev F asserts it in nine, none of
which are the same ones. **The set moved wholesale.** And the last six changed `AUX` and `CKO`
*together* — two bits that live in two different PROMs (`23A15A2`→`23A20A2` and
`23A14A2`→`23A19A2`). A coordinated change across two chips is a design revision, not a chip
respin, which is consistent with both PROM part numbers changing rather than one.

## 7. The two drawing sets are different microcode revisions

The 1973 set describes **M7261 revision E** and the 1976 set **revision F** (chip numbers on both
schematics matched against two physical rev E boards).

`kd11b-revision-diff.txt` lists **20 bits in 14 microwords**, confined to exactly two fields:
**`AUX` (14 bits) and `CKO` (6)**. The clearest single case is `U1-1` … `U5-1`, five consecutive
microwords where 1973 has `AUX=1, CKO=0` and 1976 has `AUX=0, CKO=1`, with `URTR` immediately
after identical in both — crisp in all three scans.

Three transcriptions back this: the two 1973 scans agree with each other and disagree with 1976
at every one of those positions. The signature is what makes it convincing on its own — the
differences fall in two of twenty-three fields and nowhere else, whereas OCR error scatters.

**The schematics then confirm it independently and exactly.** Of the ten control-store PROMs,
**two** change part number between rev E and rev F:

| bits | fields in that slice | rev E | rev F |
| --- | --- | --- | --- |
| 8–11 | TNS, ABT, **CKO** | `23A14A2` | `23A19A2` |
| 24–27 | **AUX**, FSH, CRI, ALU-MODE | `23A15A2` | `23A20A2` |

`CKO` is bit 11 and `AUX` is bit 24. **The two PROMs that change are precisely the two that hold
the two fields where the listings differ**, and the transcription finds no difference in any of
the other eight PROMs. OCR of printed bits and part numbers on a schematic are about as
independent as two sources get. This also settles the `!! check 1` query against the 8–11 slice
in `pdp-1105-microcode.txt`: that PROM does genuinely differ.

**So the two sets are not interchangeable, and the machine does not have to be running to decide
which applies: read the part numbers off the two PROMs.** `23A14A2` + `23A15A2` is rev E and
takes the 1973 listing; `23A19A2` + `23A20A2` is rev F and takes the 1976 one. All ten
control-store PROMs are named in `kd11b-fields.tsv`, at E092–E107 on a rev E board and E102–E116
on a rev F one; everything else on M7260/M7261 is random-logic replacement and is not microcode.

## 8. Files

| file | what it is |
| --- | --- |
| `kd11b-microcode-1973.txt` / `.tsv` | the October 1973 listing (rev E), 214 microwords |
| `kd11b-microcode-1976.txt` / `.tsv` | the July 1976 listing (rev F), 214 microwords |
| `kd11b-fields.tsv` | the field table: listing label, column, schematic bit, signal, polarity, PROM per revision |
| `kd11b-fieldvalues.tsv` | symbolic value names per field, keyed by the **printed** bit pattern |
| `kd11b-revision-diff.txt` | the 20 bits where the two drawing sets genuinely differ |
| `kd11b-corrections.txt` | the 9 bits corrected by hand after looking at all three scans, with reasons |
| `../pdp-1105-microcode.txt` | the schematic bit map and PROM assignments this was checked against |
| `proms/` | the ten 256x4 PROM images per revision, assembled from the listing, with their own README |
| `../ocr/` | the pipeline that produced all of it |

`.txt` mirrors the original column layout. `.tsv` is the machine-readable form, one row per
microword, carrying the 40 bits both split by field and as a single string, plus decoded columns
so nothing downstream has to remember the encoding: `NXTADDR` (complemented), `ALUCODE`/`ALUOP`,
`SPA` (assembled from its four scattered columns), and symbolic names for `BUT`, `BRG`, `TNS`,
`ALG`, `SPAMUX`, `SPF`, `ABT`, `FSH` and the B leg.

## 9. How much of this is checked

| claim | how it is held down |
| --- | --- |
| 214 microwords, 40 data rows per page | row grid fitted independently on all 18 pages; all three scans agree exactly |
| the column layout | read off the dash rule, identical on all 18 pages; and every one of the 40 columns matches the schematic bit map |
| all 214 addresses distinct and < 0400 | enforced by the assignment solver and verified afterwards |
| the tags | read by eye, and the 214 names sort **exactly** in ASCII order — a misread character almost always breaks the sort |
| LOC digits | assignment solution, then every disagreement with the by-eye reading adjudicated against zoomed crops of both drawing sets |
| the 8560 bits | classified independently per scan; `73l` and `76` agree on 99.66%, and all 29 disagreements were resolved by eye against all three images |
| NXT polarity | the coverage test (83.2% vs 99.5%) and the `B-1 → B-2 → B-3` chain, then independently by the signal name `MPC-n-L` |
| the ALU field | all 12 codes decode to named operations from the manual's table, covering 214/214 microwords |
| field polarity and defaults | the `-L`/`-H` suffixes in the schematic signal names |
| `FSH` = `F-SHIFT-L` | named so on both schematics, and asserted only in five chains of seven consecutive shift steps, only ever with the `AL` and `ASR` ALU codes |
| the `BRG` bit order | the 74194 mode wiring in EK-KD11B-MM-001 §4.3.6 (bit 05 = S0, bit 04 = S1), consistent with the manual's odd-byte steps shifting right and `B-1` shifting left (corrected October 2026) |
| the `SPA` decode | all 96 microwords with a non-zero ROM scratchpad address have `SPAMUX` = `ROM`; the two decodes were derived separately |
| the `BUT` decode | read as printed; matches the manual's microprogram flow listing on all 13 steps that name a `BUT` (corrected October 2026) |
| the revision split | three transcriptions, plus the two PROMs whose part numbers change being exactly the two holding `AUX` and `CKO` |

**Not checked against hardware.** Nothing here has been compared against a running machine. What
that would add is validation of the *meanings* — that microword N really does assert what the
decode says. The revision question specifically does **not** need it any more.

## 10. Known soft spots and what is still open

- **Faded slashed zeros** are the residual failure mode for the 1973 revision. Both 1973 scans
  read a dropped-out `Ø` as `1` and agree with each other, so only the 1976 scan can catch it —
  and only where the two revisions do not genuinely differ. If a 1973-revision bit ever looks
  wrong, suspect a faded zero first.
- The two 1973 scans still differ at **24 positions** after correction. All 24 are places where
  the low-resolution `73` scan is wrong and `73l` agrees with `76`. They are not open questions,
  but they are the measure of how bad the 815 px scan is — and of how much a better scan is worth.
- **Four value names are taken on trust**, because the notes give them without the data being
  able to check them: `ALG`'s `SPR` (1 microword) and `PSW` (5), and `SPAMUX`'s `IRS`/`IRD` — see
  below. Everything else in `kd11b-fieldvalues.tsv` is either corroborated by the data or is the
  overwhelming default.
- **What the five seven-step shift chains are for** is not established. Seven shifts ending on an
  eighth step looks like a byte-wide operation, and the `SBO`/`SB1`/`SB2`/`DO` naming suggests
  shift-out and shift-in routines, but that is a guess and is not written down here as anything
  more.
- **`BTP=1, BBT=0` occurs in 26 microwords and the schematic notes do not name it.** They name
  `BREG` (1,1), `SEX` (0,1) and `+1` (0,0); the fourth combination is used more often than two of
  the named ones. If `BTOP` and `BBOT` independently select the top and bottom halves of the B leg
  then it reads as "top from B register, bottom `+1`", but that is inference. Worth another look
  at the schematic.
- **`IRS` versus `IRD` in `SPAMUX` is not confirmed.** The data pins `ROM` and `BA` — they are the
  two values invariant under swapping the mux bits — but `IRS` (16 microwords) and `IRD` (14) are
  symmetric, so the transcription cannot tell which is which. The value names are taken from the
  notes as given.
- **Five ALU codes in the manual's table never appear**: `A xor B`, `not B`, `-1`, `A - 1` and
  `ROL`. Three of those are now explained. **`A xor B` cannot appear because the PDP-11/05 has no
  `XOR` instruction** — it arrived with the 11/45 — so the code exists in the 74181 but the
  microcode has no use for it. `ROL` and `ROR` go through `F-SHIFT` rather than the ALU. That
  leaves `not B`, `-1` and `A - 1`, which are plausibly supplied by the `AUX` IR-decode PROMs
  rather than by any microword's `ALU` field, since those are exactly the operations a
  single-operand instruction needs.
- **`CKO`'s exact condition** is not pinned down — see §6. It is the clock stop, but the listing
  alone does not say precisely when it is asserted, and the value-name polarity in the notes reads
  backwards against the data. It is the last of the 23 fields without a settled meaning.
- **Why the revision moved `AUX` between microwords** is not known. `AUX` itself is understood
  now; what the E→F change was *for* is not. It took IR-decoded ALU control away from the six
  `not_A` microwords and gave it to the shift terminators and the `U` group — a redesign of
  something, and the answer is probably a fixed bug or a changed instruction timing.
- `ERT-1 @010` was the one genuine conflict in the by-eye reading — it looked like `012`, which
  `SB2-2` also holds. The third digit is a slashed zero on 1976 page 3. Both the zoomed crop and
  the assignment solver agree on `010`.
- The **42 unlisted control-store locations** are not accounted for. They may be unused, or used
  and simply not printed. A `BUT` overlay can steer a branch into an address the listing never
  names, so a loader must treat an unresolvable next address as a diagnostic, not an error.
- **The printed next-address is only the whole story where `BUT` is `NON`.** In the other 73
  microwords the microtest ORs bits into the address, so the printed value is a branch base and
  the real successor depends on machine state. Anything that walks the control graph — a
  predecessor index, a "next microword" button — has to say so rather than presenting the base as
  *the* successor. This is also why the `CKO` chain above could not be followed.
