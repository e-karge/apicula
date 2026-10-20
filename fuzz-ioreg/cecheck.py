"""For the registers with CE: the CE/LSR-type wires in the IO tile that only the
vendor or only the open toolchain drives, per A/B side.
usage: python3 cecheck.py FAMILY DIR"""
import re, sys
from collections import Counter
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
cst = re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read())
def dsts(tb, rc):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    return {dst for dst, srcs in tile.pips.items() for src, bits in srcs.items() if bits and bits <= on}
res = Counter()
for port, pin in cst:
    typ = port.split('_', 1)[-1]
    if not (typ.endswith('e') and typ.startswith('dff')):
        continue
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', pin).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    v, o = dsts(tv, rc), dsts(to, rc)
    ce = lambda s: tuple(sorted(w for w in s if re.fullmatch(r'CE\d|LSR2|SEL\d', w)))
    bel = db[rc].bels.get(f'IOLOGIC{ab}')
    if bel is None:
        continue
    pm = bel.portmap.get('CE')
    res[(ab, 'vendor', ce(v - o), 'open', ce(o - v), 'portmap CE', pm)] += 1
for k, n in sorted(res.items()):
    print(n, k)
