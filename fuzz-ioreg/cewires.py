"""All pip destinations in the IO tile of the pins, vendor vs open (any wire).
usage: python3 cewires.py FAMILY DIR PORT..."""
import re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
def pips(tb, rc):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    return {(dst, src) for dst, srcs in tile.pips.items() for src, bits in srcs.items() if bits and bits <= on}
for port in sys.argv[3:]:
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', cst[port]).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    v, o = pips(tv, rc), pips(to, rc)
    vd, od = {x for x, _ in v}, {x for x, _ in o}
    # only the local wires (no long/segment wires)
    loc = lambda s: sorted(w for w in s if re.fullmatch(r'[A-D][0-7]|CE\d|LSR\d|CLK\d|SEL\d', w))
    print(f'{port:9} {cst[port]:7} vendor-only {loc(vd - od)} open-only {loc(od - vd)}')
