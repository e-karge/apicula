"""Explain the bank fuses of a bitstream with bank table entries.

For one bank, take the fuses that belong to its BANK table and list the
smallest combinations of single entries (attribute=value sets) whose fuses
are all set and that together cover every set fuse.

usage: python3 bankfit.py DEVICE BANK file.fs [file.fs ...]
"""
import sys

from apycula import attrids, bslib, chipdb

dev_name, bank = sys.argv[1], int(sys.argv[2])
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")
attr_names = {v: k for k, v in attrids.iob_attrids.items()}
val_names = {v: k for k, v in attrids.iob_attrvals.items()}
rev_iob = {code: av for av, code in db.logicinfo['IOB'].items()}


def key_name(key):
    parts = []
    for code in key:
        if code == 0:
            break
        attr, val = rev_iob.get(abs(code), (None, None))
        name = f"{attr_names.get(attr, attr)}={val_names.get(val, val)}"
        parts.append(name if code > 0 else '!' + name)
    return ' & '.join(parts)


# the tile with this bank's table
loc = None
for rc, td in ((rc, db[rc]) for rc in ((r, c) for r in range(db.rows) for c in range(db.cols))):
    if f'BANK{bank}' in td.bels:
        loc = rc
        break
ttyp = db[loc].ttyp
entries = {k[1:]: fs for k, fs in db.longval[ttyp]['BANK'].items() if k[0] == bank and fs}
all_fuses = set().union(*entries.values())

for fname in sys.argv[3:]:
    tile = chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)[loc]
    on = {f for f in all_fuses if tile[f[0]][f[1]]}
    # entries whose fuses are all set
    fits = {k: fs for k, fs in entries.items() if fs <= on}
    # entries not contained in a larger fitting entry
    maximal = {k: fs for k, fs in fits.items() if not any(fs < o for o in fits.values())}
    covered = set().union(*maximal.values()) if maximal else set()
    print(f"{fname.rsplit('/', 1)[-1]}: bank {bank} at R{loc[0]}C{loc[1]}, set: {sorted(on)}")
    for k, fs in sorted(maximal.items(), key=lambda kv: key_name(kv[0])):
        print(f"    {key_name(k)} -> {sorted(fs)}")
    if on - covered:
        print(f"    unexplained: {sorted(on - covered)}")
