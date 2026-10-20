"""Trace the PLL input ports of a bitstream back to their drivers.

For every filled PllIn slot of the vendor .dat (wire PllIn[i] at
(row, col + PllInDlt[i]) of the PLL anchor tile), follow the decoded pips
backwards (inter-tile wires to their root tile) until VCC, VSS or a logic
output, and print slot: value.

usage: GOWINHOME=... python3 consttrace.py DEVICE file.fs ROW COL [DIR]
       (ROW, COL: the PLL anchor tile, 0-based, e.g. 108 146 for PLL_B[2];
        DIR: +1 (default) or -1, the direction of the PllInDlt column offsets)
"""
import os
import re
import sys
from pathlib import Path

from apycula import bslib, chipdb, dat_parser, gowin_unpack, wirenames

dev_name, fname, arow, acol = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
direction = int(sys.argv[5]) if len(sys.argv) > 5 else 1
db = chipdb.load_chipdb(f"{chipdb.__file__.rsplit('/', 1)[0]}/{dev_name}.msgpack.xz")
wirenames.select_wires(dev_name)
gowin_unpack._device = dev_name
dat = dat_parser.Datfile(Path(f"{os.environ['GOWINHOME']}/IDE/share/device/{dev_name}/{dev_name}.dat"))
tiles = chipdb.tile_bitmap(db, bslib.read_bitstream(fname)[0], empty=True)

_pips = {}


def pips(rc):
    if rc not in _pips:
        _, p, cp = gowin_unpack.parse_tile_(db, rc[0], rc[1], tiles[rc])
        _pips[rc] = dict(p)
    return _pips[rc]


def trace(row, col, wire, depth=0):
    """ Driver of wire at (row, col): 'VCC', 'VSS', 'logic:...' or '?' """
    if depth > 30:
        return '?loop'
    if wire in {'VCC', 'VSS'}:
        return wire
    if re.fullmatch(r"([NESW])([128]\d)(\d)", wire):
        # inter-tile wire: the driver sits in the root tile, segment 0
        root = chipdb.wire2global(row + 1, col + 1, db, wire)
        m = re.fullmatch(r"R(\d+)C(\d+)_(\w+)", root)
        row, col, wire = int(m.group(1)) - 1, int(m.group(2)) - 1, m.group(3) + '0'
    src = pips((row, col)).get(wire)
    if src is None:
        return f'?none:R{row}C{col}_{wire}'
    if src in {'VCC', 'VSS'}:
        return src
    if re.fullmatch(r"[FQ]\d|OF\d", src):
        return f'logic:R{row}C{col}_{src}'
    return trace(row, col, src, depth + 1)


st = dat.gw5aStuff
for i, w in enumerate(st['PllIn']):
    if w == -1:
        continue
    col = acol + direction * st['PllInDlt'][i]
    wire = wirenames.wirenames[w]
    v = trace(arow, col, wire)
    print(f"{i} {wire}@{st['PllInDlt'][i]} {v}")
