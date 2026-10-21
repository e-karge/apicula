"""Vendor bitstream: the pips set in the IO tile of a pin (B pins: also the
IOB B fuse cell), minimal decode, local wires only, with the bel ports they are.
usage: python3 vpips.py FAMILY DIR PORT..."""
import re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tb = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
loc = re.compile(r'[A-D][0-7]|CE\d|LSR\d|CLK\d|SEL\d|F\d|Q\d|OF\d|X0\d')
def pips(rc):
    t = tb[rc]; on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    res = []
    for dst, srcs in db[rc].pips.items():
        cand = {s: b for s, b in srcs.items() if b and b <= on}
        cand = {s: b for s, b in cand.items() if not any(b < o for o in cand.values())}
        res += [(dst, s) for s in cand]
    return res
for port in sys.argv[3:]:
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', cst[port]).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    rcs = [rc]
    if ab == 'B':
        off = db[rc].bels['IOBB'].fuse_cell_offset or (0, 0); rcs.append((rc[0] + off[0], rc[1] + off[1]))
    names = {}
    for b in (f'IOLOGIC{ab}', f'IOB{ab}'):
        for p, w in getattr(db[rc].bels.get(b), 'portmap', {}).items():
            if isinstance(w, str):
                names.setdefault(w.removeprefix('IOLOGIC').removeprefix('IOBB_'), []).append(f'{b[:-1] if b.startswith("IOB") else "L"}.{p}')
    for r in rcs:
        ps = [(dst, src) for dst, src in pips(r) if loc.fullmatch(dst) or loc.fullmatch(src)]
        print(f'{port} {cst[port]} R{r[0]}C{r[1]}:')
        for dst, src in sorted(ps):
            tag = ' '.join(x for x in (f'dst={names[dst][:3]}' if dst in names else '', f'src={names[src][:3]}' if src in names else '') if x)
            print(f'    {dst:6} <- {src:8} {tag}')
