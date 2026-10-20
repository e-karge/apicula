"""Raw fuse differences of selected tiles, each bit annotated with the
pips/clock pips whose fuse set contains it.

usage: python3 rawdiff.py DEVICE a.fs b.fs ROW,COL ...
"""
import sys
from apycula import bslib, chipdb

dev_name, fs_a, fs_b = sys.argv[1:4]
rcs = [tuple(int(x) for x in a.split(',')) for a in sys.argv[4:]]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")
ta = chipdb.tile_bitmap(db, bslib.read_bitstream(fs_a)[0], empty=True)
tb = chipdb.tile_bitmap(db, bslib.read_bitstream(fs_b)[0], empty=True)
for rc in rcs:
    tile = db[rc]
    owners = {}
    for kind, tab in (('pip', tile.pips), ('clk', tile.clock_pips)):
        for dst, srcs in tab.items():
            for src, bits in srcs.items():
                for b in bits:
                    owners.setdefault(b, []).append(f"{kind} {dst}<-{src}")
    a, b = ta[rc], tb[rc]
    print(f"R{rc[0]}C{rc[1]} ttyp {tile.ttyp}")
    for r in range(len(a)):
        for c in range(len(a[r])):
            if a[r][c] != b[r][c]:
                who = owners.get((r, c), [])
                print(f"  ({r},{c}) {'a' if a[r][c] else 'b'}  {'; '.join(who[:4])}{' ...' if len(who) > 4 else ''}")
