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
    loc = re.compile(r'[A-D][0-7]|CLK\d|LSR\d|SEL\d|CE\d')
    v, o = {w for w in dsts(tv, brc) if loc.fullmatch(w)}, {w for w in dsts(to, brc) if loc.fullmatch(w)}
    print(f'{port:10} {cst[port]:7} R{brc[0]}C{brc[1]} vendor-only {sorted(v - o)} open-only {sorted(o - v)} both {sorted(v & o)}')
