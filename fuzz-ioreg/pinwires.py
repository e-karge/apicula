"""Per pin: the destination wires (bel port wires of the IO tile) that only
the vendor or only the open toolchain drives.
usage: python3 pinwires.py FAMILY DIR [PREFIX]"""
import re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
prefix = sys.argv[3] if len(sys.argv) > 3 else ''
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
def dsts(tb, rc):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    return {dst for dst, srcs in tile.pips.items() for src, bits in srcs.items() if bits and bits <= on}
for port, pin in cst.items():
    if not port.startswith(prefix):
        continue
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', pin).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    names = {}
    for n, b in db[rc].bels.items():
        if n in (f'IOLOGIC{ab}', f'IOB{ab}'):
            for p, w in b.portmap.items():
                if isinstance(w, str):
                    names.setdefault(w, []).append(f'{n[:-1] if n.startswith("IOB") else "L"}.{p}')
    v, o = dsts(tv, rc) & set(names), dsts(to, rc) & set(names)
    fmt = lambda s: ' '.join(f'{w}({",".join(names[w][:2])})' for w in sorted(s))
    print(f'{port:10} {pin:7} vendor-only: {fmt(v - o):40} open-only: {fmt(o - v):40} both: {fmt(v & o)}')
