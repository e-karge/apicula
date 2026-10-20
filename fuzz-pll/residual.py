"""Fuses of a tile that no decoded (active) pip accounts for.

usage: python3 residual.py DEVICE ROW,COL a.fs ...
"""
import sys
from apycula import bslib, chipdb, gowin_unpack, wirenames

dev_name, rcarg = sys.argv[1:3]
rc = tuple(int(x) for x in rcarg.split(','))
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")
wirenames.select_wires(dev_name)
gowin_unpack._device = dev_name
tile = db[rc]
for fname in sys.argv[3:]:
    bm = chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)[rc]
    _, p, cp = gowin_unpack.parse_tile_(db, rc[0], rc[1], bm)
    used = set()
    for tab, act in ((tile.pips, p), (tile.clock_pips, cp)):
        for d, s in act.items():
            used |= set(tab[d][s])
    on = {(r, c) for r in range(len(bm)) for c in range(len(bm[r])) if bm[r][c]}
    print(fname.rsplit('/', 1)[-1], sorted(cp.items()), 'residual', sorted(on - used))
