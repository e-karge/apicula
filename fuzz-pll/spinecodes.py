"""Decode the 7-bit source codes of the spine muxes in the GW5AST-138C
clock mux tiles (R54C88 bottom, R54C93 top) of vendor bitstreams.

The legacy table names give the bit positions: BRPLL0CLK0 is code 1,
BRPLL0CLK1 code 2, so the field runs from the LSB in that direction.

usage: python3 spinecodes.py a.fs ...
"""
import sys
import apycula
from apycula import bslib, chipdb

db = chipdb.load_chipdb(apycula.__path__[0] + '/GW5AST-138C.msgpack.xz')


def fields(rc):
    t = db[rc]
    res = {}
    for sp, srcs in t.clock_pips.items():
        if 'PLLCLK17' in srcs:
            # the chipdb has the codes as PLLCLKn since the fix of the PLL
            # outputs: 17 and 18 (in both MUXes) differ in bits 0 and 1
            (r, lsb), = set(srcs['PLLCLK17']) - set(srcs['PLLCLK18'])
            (_, b1), = set(srcs['PLLCLK18']) - set(srcs['PLLCLK17'])
        elif 'BRPLL0CLK0' in srcs:
            (r, lsb), = srcs['BRPLL0CLK0']
            (_, b1), = srcs['BRPLL0CLK1']
        else:
            continue
        step = b1 - lsb
        res[sp] = [(r, lsb + k * step) for k in range(7)]
    return res


def code(bits, field):
    return sum(1 << k for k, rc in enumerate(field) if rc in bits)


FIELDS = {rc: fields(rc) for rc in ((54, 88), (54, 93))}
# legacy names by code (same in all spines)
LEGACY = {}
for rc, fl in FIELDS.items():
    for sp, field in fl.items():
        for src, bits in db[rc].clock_pips[sp].items():
            LEGACY.setdefault(code(set(bits), field), set()).add(src)

if __name__ == '__main__':
    for fname in sys.argv[1:]:
        tiles = chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)
        out = []
        for rc, fl in FIELDS.items():
            bm = tiles[rc]
            for sp, field in fl.items():
                v = code({(r, c) for r, c in field if bm[r][c]}, field)
                if v:
                    out.append(f"C{rc[1]}:{sp}={v}:{'/'.join(sorted(LEGACY.get(v, {'?'})))}")
        print(fname.rsplit('/', 1)[-1], ' '.join(out))
