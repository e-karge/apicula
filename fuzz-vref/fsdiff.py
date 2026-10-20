"""Compare two Gowin bitstreams tile by tile.

For every tile that differs, print the fuses (row, col within the tile) that
are only set in one of them. In IO tiles, also print the IOB table entries
(longval IOBA/IOBB and bank tables) whose fuse sets contain each fuse, decoded
to attribute=value names, so known fuses can be told apart from unknown ones.

usage: python3 fsdiff.py DEVICE a.fs b.fs [--all]
       (--all: also print fabric tiles, which differ with placement)
"""
import sys

from apycula import attrids, bslib, chipdb

dev_name, fs_a, fs_b = sys.argv[1:4]
show_all = '--all' in sys.argv
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")

attr_names = {v: k for k, v in attrids.iob_attrids.items()}
val_names = {v: k for k, v in attrids.iob_attrvals.items()}
rev_iob = {code: av for av, code in db.logicinfo['IOB'].items()}


def key_name(key):
    """ Decode a longval key (logicinfo codes, negative = must be unset). """
    parts = []
    for code in key:
        if code == 0:
            break
        attr, val = rev_iob.get(abs(code), (None, None))
        name = f"{attr_names.get(attr, attr)}={val_names.get(val, val)}"
        parts.append(name if code > 0 else '!' + name)
    return ' & '.join(parts)


def tiles(fname):
    bitmap = bslib.read_bitstream(fname)[0]
    return chipdb.tile_bitmap(db, bitmap, empty=True)


def set_fuses(tile):
    return {(r, c) for r, row in enumerate(tile) for c, bit in enumerate(row) if bit}


ta, tb = tiles(fs_a), tiles(fs_b)
for rc in sorted(ta):
    fa, fb = set_fuses(ta[rc]), set_fuses(tb[rc])
    if fa == fb:
        continue
    ttyp = db[rc].ttyp
    tables = {name: tbl for name, tbl in db.longval.get(ttyp, {}).items()
              if name.startswith('IOB') or name.startswith('BANK')}
    if not tables and not show_all:
        continue
    print(f"R{rc[0]}C{rc[1]} ttyp {ttyp} bels {sorted(db[rc].bels)}")
    for label, fuses in (('only in a', fa - fb), ('only in b', fb - fa)):
        for fuse in sorted(fuses):
            owners = [f"{name}: {key_name(key[1:] if name.startswith('BANK') else key)}"
                      for name, tbl in tables.items() for key, fs in tbl.items() if fuse in fs]
            print(f"  {label} {fuse}" + (''.join(f"\n      {o}" for o in owners[:6]) if owners else '  (no table entry)'))
