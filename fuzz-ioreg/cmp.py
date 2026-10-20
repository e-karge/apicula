"""Per pin: the IOLOGIC table entries set by the vendor and by the open
toolchain, decoded via logicinfo, and their difference.

usage: python3 cmp.py FAMILY DIR [-v]   (DIR from build.sh: top.cst, vendor.fs, open.fs)
SRMODE is ignored for the registers without set/reset.
"""
import re, sys
from apycula import bslib, chipdb, attrids

family, d = sys.argv[1:3]
verbose = '-v' in sys.argv
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
gw5 = family.startswith('GW5')
li = {code: av for av, code in db.logicinfo['IOLOGIC'].items()}
ra = {v: k for k, v in attrids.iologic_attrids.items()}
rv = {v: k for k, v in attrids.iologic_attrvals.items()}

def dec(code):
    a, v = li.get(abs(code), ('?', '?'))
    return ('!' if code < 0 else '') + f"{ra.get(a, a)}={rv.get(v, v)}"

def entries(fs):
    tb = chipdb.tile_bitmap(db, bslib.read_bitstream(fs)[0], empty=True)
    cache = {}
    def get(rc, table):
        if (rc, table) not in cache:
            t = tb[rc]
            on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
            tab = db.shortval.get(db[rc].ttyp, {}).get(table, {})
            hits = [(k, f) for k, f in tab.items() if f and f <= on]
            hits = [(k, f) for k, f in hits if not any(f < g for _, g in hits)]
            cache[rc, table] = {dec(c) for k, _ in hits for c in k if c}
        return cache[rc, table]
    return get

def loc(name):
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', name).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    if gw5 and ab == 'B':
        rc = (rc[0], rc[1] + 1) if side in 'TB' else (rc[0] + 1, rc[1])
    return rc, f'IOLOGIC{ab}'

ven, opn = entries(f'{d}/vendor.fs'), entries(f'{d}/open.fs')
pins = re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read())
bad = 0
for port, name in pins:
    rc, table = loc(name)
    v, o = ven(rc, table), opn(rc, table)
    # no set/reset: the LSR is 0, SRMODE doesn't matter
    typ = port.split('_', 1)[-1].upper()
    if not any(sr in typ.replace('DFF', '', 1).replace('N', '', 1) for sr in 'SRPC') or port in {'b_oen', 'b_out'}:
        v, o = v - {'SRMODE=LSR_OVER_CE'}, o - {'SRMODE=LSR_OVER_CE'}
    if v == o and not verbose:
        continue
    bad += v != o
    print(f'{port:10} {name:8} R{rc[0]}C{rc[1]} {"same" if v == o else ""}')
    if v != o:
        print(f'    vendor only: {sorted(v - o)}')
        print(f'    open only:   {sorted(o - v)}')
    if verbose:
        print(f'    both:        {sorted(v & o)}')
print(f'{bad} of {len(pins)} pins differ')
