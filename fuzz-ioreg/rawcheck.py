"""Raw differences between vendor.fs and open.fs in the bits of the IOLOGIC
shortval tables (routing and IOB bits are left out).
usage: python3 rawcheck.py FAMILY DIR"""
import sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
iol_bits = {}
for ttyp, tabs in db.shortval.items():
    bits = set()
    for t, tab in tabs.items():
        if t.startswith('IOLOGIC'):
            for f in tab.values():
                bits |= f
    iol_bits[ttyp] = bits
n = 0
for rc in sorted(tv):
    bits = iol_bits.get(db[rc].ttyp, set())
    a, b = tv[rc], to[rc]
    diff = sorted((r, c, 'v' if a[r][c] else 'o') for r, c in bits if a[r][c] != b[r][c])
    if diff:
        n += 1
        print(f'R{rc[0]}C{rc[1]}: {diff}')
print(f'{n} tiles differ')
