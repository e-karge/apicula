"""Input register pins: which IOLOGIC output wires are used as pip sources in
the IO tile (A) or the B fuse tile (B), vendor vs open.
usage: python3 srcwires.py FAMILY DIR PORT..."""
import re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
def srcs(tb, rc):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    return {src for dst, ss in tile.pips.items() for src, bits in ss.items() if bits and bits <= on}
for port in sys.argv[3:]:
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', cst[port]).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    off = (getattr(db[rc].bels.get('IOBB'), 'fuse_cell_offset', None) or (0, 0)) if ab == 'B' and family.startswith('GW5') else (0, 0)
    brc = (rc[0] + off[0], rc[1] + off[1])
    if f'IOLOGIC{ab}' not in db[rc].bels:
        continue
    pm = db[rc].bels[f'IOLOGIC{ab}'].portmap
    outs = {w.removeprefix('IOLOGIC'): p for p, w in pm.items() if p.startswith('Q') and isinstance(w, str)}
    v, o = srcs(tv, brc) & set(outs), srcs(to, brc) & set(outs)
    print(f'{port:9} {cst[port]:7} R{brc[0]}C{brc[1]} vendor {sorted((w, outs[w]) for w in v)} open {sorted((w, outs[w]) for w in o)}')
