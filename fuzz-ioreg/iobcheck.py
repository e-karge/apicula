"""Bits of the IOB tables (shortval/longval IOBA/IOBB) that differ between
vendor.fs and open.fs, per tile.
usage: python3 iobcheck.py FAMILY DIR"""
import sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
n = 0
for rc in sorted(tv):
    bits = set()
    for kind in ('shortval', 'longval'):
        for t, tab in getattr(db, kind).get(db[rc].ttyp, {}).items():
            if t.startswith('IOB'):
                for f in tab.values():
                    bits |= f
    a, b = tv[rc], to[rc]
    diff = sorted((r, c, 'v' if a[r][c] else 'o') for r, c in bits if a[r][c] != b[r][c])
    if diff:
        n += 1
        print(f'R{rc[0]}C{rc[1]}: {diff}')
print(f'{n} tiles differ')
