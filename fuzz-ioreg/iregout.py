"""Input registers: the wire nextpnr routes the register output (Q4) from,
and the pips from the IOLOGIC output wires that are set in the vendor and
the open bitstream in that tile.
usage: python3 iregout.py FAMILY DIR"""
import json, re, sys
from apycula import bslib, chipdb
family, d = sys.argv[1:3]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
tv = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/vendor.fs')[0], empty=True)
to = chipdb.tile_bitmap(db, bslib.read_bitstream(f'{d}/open.fs')[0], empty=True)
m = json.load(open(f'{d}/pnr.json'))['modules']['top']
bitnet = {b: n for n, net in m['netnames'].items() for b in net['bits']}
def pips(tb, rc, src):
    t = tb[rc]; tile = db[rc]
    on = {(r, c) for r in range(len(t)) for c in range(len(t[r])) if t[r][c]}
    return sorted(dst for dst, ss in tile.pips.items() for s, bits in ss.items() if s == src and bits and bits <= on)
for n, c in m['cells'].items():
    if c['type'] != 'IOLOGICI_EMPTY' or 'HAS_REG' not in c['attributes']:
        continue
    x, y, ab = re.fullmatch(r'X(\d+)Y(\d+)/IOLOGIC([AB])I', c['attributes']['NEXTPNR_BEL']).groups()
    rc = (int(y), int(x))
    net = bitnet[c['connections'].get('IREG_Q', c['connections'].get('Q4'))[0]]
    routing = m['netnames'][net]['attributes'].get('ROUTING', '').split(';')
    first = [routing[i] for i in range(0, len(routing) - 2, 3) if routing[i + 2] == '1' or routing[i + 1] == ''][:1]
    if family.startswith('GW5') and ab == 'B':
        off = db[rc].bels['IOBB'].fuse_cell_offset or (0, 0)
        rc = (rc[0] + off[0], rc[1] + off[1])
    pm = db[(int(y), int(x))].bels[f'IOLOGIC{ab}'].portmap
    q4 = pm['Q4']
    outs = sorted({w.removeprefix('IOLOGIC') for p, w in pm.items() if p.startswith('Q') and isinstance(w, str)})
    print(f'{n[:22]:22} {c["attributes"]["NEXTPNR_BEL"]:18} {c["attributes"]["IREG_TYPE"]:7} Q4={q4:5} '
          + ' '.join(f'{w}: v{pips(tv, rc, w)} o{pips(to, rc, w)}' for w in outs if pips(tv, rc, w) or pips(to, rc, w)))
