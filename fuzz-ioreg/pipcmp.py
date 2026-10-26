"""Pips set in the IO tiles of the given pins, vendor vs open, for the
destinations that are IOLOGIC/IOB bel ports (CLK, CE, LSR, D, TX ...).
usage: python3 pipcmp.py FAMILY DIR PORT..."""
import re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
cst = dict(re.findall(r'IO_LOC "(\w+)" (\w+);', open(f'{d}/top.cst').read()))
def pips(tb, rc):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    res = set()
    for dst, srcs in tile.pips.items():
        for src, bits in srcs.items():
            if bits and bits <= on:
                res.add((dst, src))
    return res
for port in sys.argv[3:]:
    side, num, ab = re.fullmatch(r'IO([TBLR])(\d+)([A-Z])', cst[port]).groups()
    num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    tile = db[rc]
    ports = {}
    for n, b in tile.bels.items():
        if n.startswith('IOLOGIC' + ab) or n == 'IOB' + ab:
            for p, w in b.portmap.items():
                if isinstance(w, str):
                    ports.setdefault(w, set()).add(f'{n}.{p}')
    v, o = pips(tv, rc), pips(to, rc)
    print(f'{port} {cst[port]} R{rc[0]}C{rc[1]}')
    for dst, src in sorted(v | o):
        if dst in ports:
            tag = 'both  ' if (dst, src) in v and (dst, src) in o else ('vendor' if (dst, src) in v else 'open  ')
            print(f'    {tag} {dst:8} <- {src:10} {sorted(ports[dst])[:3]}')
