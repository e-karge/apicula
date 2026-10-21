"""Vendor bitstream: per pin the decoded IOLOGIC entries (A: the IO tile,
B: the IOB B fuse cell) and the set bits of the IOLOGIC tables.
usage: python3 vdec.py FAMILY DIR [PORT...]"""
import re, sys
from apycula import bslib, chipdb, attrids
family, d = sys.argv[1:3]
only = sys.argv[3:]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tb = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
li = {code: av for av, code in db.logicinfo['IOLOGIC'].items()}
ra = {v: k for k, v in attrids.iologic_attrids.items()}
rv = {v: k for k, v in attrids.iologic_attrvals.items()}
def dec(c):
    a, v = li.get(abs(c), ('?', '?'))
    return ('!' if c < 0 else '') + f'{ra.get(a, a)}={rv.get(v, v)}'
cst = re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read())
for port, pin in cst:
    if only and port not in only:
        continue
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', pin).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    if family.startswith('GW5') and ab == 'B':
        off = db[rc].bels['IOBB'].fuse_cell_offset or (0, 0); rc = (rc[0] + off[0], rc[1] + off[1])
    t = tb[rc]; on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    tab = db.shortval.get(db[rc].ttyp, {}).get(f'IOLOGIC{ab}', {})
    hits = [(k, f) for k, f in tab.items() if f and f <= on]
    hits = [(k, f) for k, f in hits if not any(f < g for _, g in hits)]
    allbits = set().union(*tab.values()) if tab else set()
    names = sorted({' & '.join(dec(c) for c in k if c) for k, _ in hits})
    print(f'{port:8} {pin:7} R{rc[0]}C{rc[1]} bits {sorted(on & allbits)}')
    for n in names:
        print(f'      {n}')
