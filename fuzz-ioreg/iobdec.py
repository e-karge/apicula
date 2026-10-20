"""IOB table entries (decoded) set only by the vendor or only by the open
toolchain, for the IO tile of each given pin (B pins: the B fuse cell).
usage: python3 iobdec.py FAMILY DIR PORT..."""
import re, sys
from apycula import bslib, chipdb, attrids
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
li = {code: av for av, code in db.logicinfo['IOB'].items()}
ra = {v: k for k, v in attrids.iob_attrids.items()}
rv = {v: k for k, v in attrids.iob_attrvals.items()}
def dec(c):
    a, v = li.get(abs(c), ('?', '?'))
    return ('!' if c < 0 else '') + f'{ra.get(a, a)}={rv.get(v, v)}'
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
def ents(tb, rc, table):
    t = tb[rc]; on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    out = set()
    for kind in ('shortval', 'longval'):
        tab = getattr(db, kind).get(db[rc].ttyp, {}).get(table, {})
        hits = [(k, f) for k, f in tab.items() if f and f <= on]
        hits = [(k, f) for k, f in hits if not any(f < g for _, g in hits)]
        out |= {tuple(dec(c) for c in k if c) for k, _ in hits}
    return out
for port in sys.argv[3:]:
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', cst[port]).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    if family.startswith('GW5') and ab == 'B':
        off = db[rc].bels['IOBB'].fuse_cell_offset or (0, 0); rc = (rc[0] + off[0], rc[1] + off[1])
    v, o = ents(tv, rc, f'IOB{ab}'), ents(to, rc, f'IOB{ab}')
    print(f'{port} {cst[port]} R{rc[0]}C{rc[1]}\n   vendor only: {sorted(v - o)}\n   open only:   {sorted(o - v)}')
