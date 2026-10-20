"""Register pins: local wires in the IO tile (the IOLOGIC/IOB bel port wires)
driven only by the vendor or only by the open toolchain, summed up.
usage: python3 localwires.py FAMILY DIR"""
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
seen = Counter()
for port, pin in cst:
    if port in {'clk', 'ce', 'rst', 'x', 'b_oen', 'b_out', 'b_sr'}:
        continue
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', pin).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    names = {}
    for n in (f'IOLOGIC{ab}', f'IOB{ab}'):
        for p, w in getattr(db[rc].bels.get(n), 'portmap', {}).items():
            if isinstance(w, str):
                names.setdefault(w, set()).add(p)
    v, o = dsts(tv, rc) & set(names), dsts(to, rc) & set(names)
    for w in v ^ o:
        seen[(ab, 'vendor' if w in v else 'open', w, tuple(sorted(names[w]))[:3])] += 1
for k, n in sorted(seen.items()):
    print(n, k)
print('no differences' if not seen else '')
