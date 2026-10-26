# GW5A registers in IO blocks: notes for the follow-up

`iob-regs-with-gw5a.patch` is the gowin_pack change including the GW5A parts (against
gowin_pack-iologico-empty 68be7e1). With it the IOLOGIC table bits match the vendor on the
GW5A-25A and the GW5AST-138C (right, bottom and left side):

- the IOLOGIC B fuses are in the cell with the IOB B fuses (`get_iob_fuse_cell_offset`)
- negative edge registers in an IOBUF with an input register: the vendor inverts only the
  input clock (`CLKIMUX_CLK=INV`, no `CLKOMUX_CLK`, no `*_OUTREGMODE`), on 25A and 138C
- SRMODE without set/reset is a don't care (the vendor sets it depending on the design)

But it fails on the hardware (Tang Mega 138K DDR3 with DDR3_IOBFF: calibration fails, reads 0),
because the routing into the register differs (`pipcmp.py`, `pinwires.py`, `bwires.py`):

| register input | vendor | nextpnr (chipdb portmap) |
|---|---|---|
| OREG D, A | `D1` = IOLOGICA.D7 | `A0` = IOLOGICA.D0 |
| OREG D, B | `C2` = IOLOGICB.D7 (B fuse cell) | `D1` = IOLOGICB.D0 = IOBB.I |
| TREG D | the IOB OE wire: 138C `B0`/`D5` (= TX0), 25A `C1` (= TX3) | TX0 |
| CE | `CE0` (A cell / B fuse cell) | 138C `SEL1`, 25A `D6` (IOLOGIC CE) |
| CLK, SET/RESET | `CLK0`, `LSR0` | same |

The vendor also routes LSR0 for registers without set/reset (presumably to a constant).

Needed:
- chipdb: IOLOGIC bel pins for the register inputs on GW5A (D7 wire, IOB OE wire, CE0 with an
  alias into the B fuse cell); don't change D0/TX/CE, the other IOLOGIC primitives use them
- nextpnr pack_io_regs: on GW5A connect D/OEN/CE of the packed registers to those pins
- then apply the GW5A parts of the patch and remove the error

Other findings:
- nextpnr doesn't pack OREG/TREG of an IOBUF whose input isn't registered (the input part of
  pack_io_regs `continue`s); the vendor does
- 138C: 14 IOLOGIC bels have no CLK in the chipdb (e.g. R54C0, R72C0); nextpnr packs registers
  there and fails with "invalid sink port ...CLK"
- corner IOs without IOLOGIC bel in nextpnr: 138C IOR109A, 25A IOT1A/B
- 138C: the vendor doesn't pack at IOB171A/B, IOB175B, IOB179A (configuration pins)
