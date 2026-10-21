"""The vendor's pin assignment with the IOs that nextpnr can't use with IO logic
(no IOLOGIC bel, or one without CLK) moved to free IOs on the same sides.
usage: python3 fixpins.py FAMILY PACKAGE top.cst > fixed.cst"""
import re, sys
from apycula import chipdb
family, pkg, src = sys.argv[1:4]
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{family}.msgpack.xz")
pins = next(v[pkg] for v in db.pinout.values() if pkg in v)
def ok(name):
    m = re.fullmatch(r'IO([TBLR])(\d+)([AB])', name)
    if not m: return False
    side, num, ab = m.groups(); num = int(num) - 1
    rc = {'T': (0, num), 'B': (db.rows - 1, num), 'L': (num, 0), 'R': (num, db.cols - 1)}[side]
    b = db[rc].bels.get(f'IOLOGIC{ab}')
    return b is not None and 'CLK' in b.portmap
cst = re.findall(r'IO_LOC "(\w+)" (\w+);\nIO_PORT "\w+" IO_TYPE=(\w+);', open(src).read())
used = {p for _, p, _ in cst}
free = sorted(iob for iob, cfgs in pins.values() if not cfgs and iob[2] in 'RB' and iob not in used and ok(iob))
for port, pin, iot in cst:
    if port != 'clk' and not ok(pin):
        pin = free.pop(0)
        print(f'// moved {port}', file=sys.stderr)
    print(f'IO_LOC "{port}" {pin};\nIO_PORT "{port}" IO_TYPE={iot};')
