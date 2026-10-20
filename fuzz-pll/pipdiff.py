"""Compare the decoded pips of two Gowin bitstreams tile by tile.

Each differing tile is decoded with gowin_unpack's tile parser (which picks
the active source of every mux), and the pips and clock pips that exist in
only one of the bitstreams are printed as dest <- src.

usage: python3 pipdiff.py DEVICE a.fs b.fs [ROW,COL ...]
       (with ROW,COL: only these tiles)
"""
import sys

import numpy

from apycula import bslib, chipdb, gowin_unpack, wirenames

dev_name, fs_a, fs_b = sys.argv[1:4]
only = {tuple(int(x) for x in arg.split(',')) for arg in sys.argv[4:]}
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")
wirenames.select_wires(dev_name)
gowin_unpack._device = dev_name


def tiles(fname):
    return chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)


def pips(rc, tile):
    _, p, cp = gowin_unpack.parse_tile_(db, rc[0], rc[1], tile)
    flat = {(d, s) for d, s in p.items()} | {(d, s, 'clk') for d, s in cp.items()}
    return flat


ta, tb = tiles(fs_a), tiles(fs_b)
for rc in sorted(ta):
    if only and rc not in only:
        continue
    if numpy.array_equal(ta[rc], tb[rc]):
        continue
    try:
        pa, pb = pips(rc, ta[rc]), pips(rc, tb[rc])
    except Exception as e:
        print(f"R{rc[0]}C{rc[1]} ttyp {db[rc].ttyp}: parse failed: {type(e).__name__} {e}")
        continue
    if pa == pb:
        continue
    print(f"R{rc[0]}C{rc[1]} ttyp {db[rc].ttyp} bels {sorted(db[rc].bels)[:6]}")
    for label, ps in (('only in a', pa - pb), ('only in b', pb - pa)):
        for p in sorted(ps):
            print(f"  {label} {p[0]} <- {p[1]}{' (clock)' if len(p) == 3 else ''}")
