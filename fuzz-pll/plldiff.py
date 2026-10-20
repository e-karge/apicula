"""Compare two Gowin bitstreams tile by tile, with PLL tables decoded.

For every tile that differs, print its position and type and the fuses that
are only set in one of the bitstreams. In tiles with a shortval PLL table,
also name the PLL table entries (attribute=value) whose fuse sets contain the
fuse.

usage: python3 plldiff.py DEVICE a.fs b.fs [--fabric]
       (--fabric: also list tiles without a PLL table, by count only)
"""
import sys

from apycula import attrids, bslib, chipdb

dev_name, fs_a, fs_b = sys.argv[1:4]
show_fabric = '--fabric' in sys.argv
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")

attr_names = {v: k for k, v in attrids.pll_attrids.items()}
val_names = {v: k for k, v in attrids.pll_attrvals.items()}
rev_pll = {code: av for av, code in db.logicinfo['PLL'].items()}


def key_name(key):
    parts = []
    for code in key:
        if code == 0:
            break
        attr, val = rev_pll.get(abs(code), (None, None))
        name = f"{attr_names.get(attr, attr)}={val_names.get(val, val)}"
        parts.append(name if code > 0 else '!' + name)
    return ' & '.join(parts)


def tiles(fname):
    return chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)


def set_fuses(tile):
    return {(r, c) for r, row in enumerate(tile) for c, bit in enumerate(row) if bit}


ta, tb = tiles(fs_a), tiles(fs_b)
fabric = 0
for rc in sorted(ta):
    fa, fb = set_fuses(ta[rc]), set_fuses(tb[rc])
    if fa == fb:
        continue
    ttyp = db[rc].ttyp
    table = db.shortval.get(ttyp, {}).get('PLL')
    if table is None:
        fabric += 1
        if show_fabric:
            print(f"R{rc[0]}C{rc[1]} ttyp {ttyp}: {len(fa - fb)} only in a, {len(fb - fa)} only in b")
        continue
    print(f"R{rc[0]}C{rc[1]} ttyp {ttyp} (PLL table, {len(table)} entries)")
    for label, fuses in (('only in a', fa - fb), ('only in b', fb - fa)):
        for fuse in sorted(fuses):
            owners = [key_name(key) for key, fs in table.items() if fuse in fs]
            print(f"  {label} {fuse}" + (''.join(f"\n      {o}" for o in owners[:4]) + (f"\n      ... {len(owners) - 4} more" if len(owners) > 4 else '') if owners else '  (no PLL table entry)'))
print(f"{fabric} other tiles differ")
