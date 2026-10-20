"""Which value of given PLL attributes a bitstream has: every value whose
fuses (in the PLL tables of the 4 cells from the anchor) are all set, the
one with the most fuses first.

usage: python3 pllattrs.py ROW,COL ATTR[,ATTR...] a.fs ...
"""
import sys
import apycula
from apycula import attrids, bslib, chipdb

rc = tuple(int(x) for x in sys.argv[1].split(','))
attrs = sys.argv[2].split(',')
db = chipdb.load_chipdb(apycula.__path__[0] + '/GW5AST-138C.msgpack.xz')
table = db.logicinfo['PLL']
for fname in sys.argv[3:]:
    tiles = chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)
    out = []
    for attr in attrs:
        aid = attrids.pll_attrids[attr]
        hits = []
        for (a, val), code in table.items():
            if a != aid:
                continue
            bits = {}
            for col in range(rc[1], rc[1] + 4):
                ttyp = db[rc[0], col].ttyp
                if 'PLL' in db.shortval.get(ttyp, {}):
                    b = chipdb.get_shortval_fuses(db, ttyp, {code}, 'PLL')
                    if b:
                        bits[col] = b
            n = sum(len(b) for b in bits.values())
            if n and all(tiles[rc[0], c][r][cc] for c, b in bits.items() for r, cc in b):
                hits.append((n, val))
        hits.sort(reverse=True)
        out.append(f"{attr}={[v for _, v in hits[:3]]}")
    print(fname.rsplit('/', 1)[-1], ' '.join(out))
