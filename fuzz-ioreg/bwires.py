"""GW5A: pips into the IO tile of the pin (the IOBB fuse cell for B pins), vendor vs open.
usage: python3 bwires.py FAMILY DIR PORT..."""
import re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
def dsts(tb, rc):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    return {dst for dst, srcs in tile.pips.items() for src, bits in srcs.items() if bits and bits <= on}
for port in sys.argv[3:]:
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', cst[port]).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    off = (db[rc].bels['IOBB'].fuse_cell_offset or (0, 0)) if ab == 'B' else (0, 0)
    brc = (rc[0] + off[0], rc[1] + off[1])
    io = {'A0', 'A1', 'B0', 'B1', 'C0', 'C1', 'C2', 'C3', 'D0', 'D1', 'D2', 'D5', 'D6', 'D7', 'CLK0', 'CLK1', 'LSR0', 'LSR1', 'SEL1', 'CE0', 'CE1'}
    v, o = dsts(tv, brc) & io, dsts(to, brc) & io
    print(f'{port:10} {cst[port]:7} R{brc[0]}C{brc[1]} vendor-only {sorted(v - o)} open-only {sorted(o - v)} both {sorted(v & o)}')
