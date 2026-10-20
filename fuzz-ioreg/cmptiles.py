"""Decoded IOLOGIC entries per tile and table, vendor vs open, for all tiles.
usage: python3 cmptiles.py FAMILY DIR"""
import sys
from apycula import bslib, chipdb, attrids
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
li = {code: av for av, code in db.logicinfo['IOLOGIC'].items()}
ra = {v: k for k, v in attrids.iologic_attrids.items()}
rv = {v: k for k, v in attrids.iologic_attrvals.items()}
dec = lambda c: ('!' if c < 0 else '') + '%s=%s' % (ra.get(li[abs(c)][0]), rv.get(li[abs(c)][1]))
def ents(fs):
    tb = chipdb.tile_bitmap(db, bslib.read_bitstream(fs)[0], empty=True)
    out = {}
    for rc, t in tb.items():
        on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
        for table, tab in db.shortval.get(db[rc].ttyp, {}).items():
            if not table.startswith('IOLOGIC'):
                continue
            hits = [(k, f) for k, f in tab.items() if f and f <= on]
            hits = [(k, f) for k, f in hits if not any(f < g for _, g in hits)]
            s = {dec(c) for k, _ in hits for c in k if c}
            if s:
                out[rc, table] = s
    return out
v, o = ents(f'{d}/vendor.fs'), ents(f'{d}/open.fs')
for key in sorted(set(v) | set(o)):
    a, b = v.get(key, set()), o.get(key, set())
    print(f'R{key[0][0]}C{key[0][1]} {key[1]}: {"same" if a == b else ""}')
    if a != b:
        print(f'    vendor only: {sorted(a - b)}\n    open only:   {sorted(b - a)}')
