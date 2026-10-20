"""Where is the PLL, and which of its outputs reach the clock network?

For each bitstream: the tiles with a shortval PLL table that have any PLL
fuse set (the PLL site), and every clock mux whose selected source is a PLL
output (the largest completely set fuse set wins, as in gowin_unpack).

usage: python3 sitemap.py DEVICE file.fs [file.fs ...]
"""
import sys

from apycula import bslib, chipdb

dev_name = sys.argv[1]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")

pll_tiles = {}
clock_pips = []
for r in range(db.rows):
    for c in range(db.cols):
        td = db[r, c]
        table = db.shortval.get(td.ttyp, {}).get('PLL')
        if table:
            pll_tiles[(r, c)] = set().union(*table.values())
        for dest, srcs in td.clock_pips.items():
            # keep the whole mux: the selected source is the largest
            # fuse set that is completely set
            if any('PLL' in src for src in srcs):
                clock_pips.append(((r, c), dest, {s: fs for s, fs in srcs.items() if fs}))

for fname in sys.argv[2:]:
    tiles = chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)
    site = sorted(rc for rc, fs in pll_tiles.items() if any(tiles[rc][f[0]][f[1]] for f in fs))
    used = set()
    for rc, dest, srcs in clock_pips:
        on = [(len(fs), src) for src, fs in srcs.items() if all(tiles[rc][f[0]][f[1]] for f in fs)]
        if on:
            src = max(on)[1]
            if 'PLL' in src:
                used.add((src, dest, rc))
    used = sorted(used)
    print(f"{fname.rsplit('/', 1)[-1]}: PLL tiles with fuses {[f'R{r}C{c}' for r, c in site]}")
    by_src = {}
    for src, dest, rc in used:
        by_src.setdefault(src, []).append(f"{dest}@R{rc[0]}C{rc[1]}")
    for src, dests in sorted(by_src.items()):
        print(f"    {src} -> {', '.join(dests[:4])}{' ...' if len(dests) > 4 else ''}")
