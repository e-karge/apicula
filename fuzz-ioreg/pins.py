"""Vendor pin report (top.pin.html) -> cst with the same IO locations and types.
usage: python3 pins.py top.pin.html > top.cst"""
import re, sys
html = open(sys.argv[1]).read()
seen = set()
for row in re.findall(r'<tr>\s*<td class="label">(.*?)</tr>', html, re.S):
    cells = re.findall(r'<td[^>]*>(.*?)</td>', '<td>' + row)
    if len(cells) < 7:
        continue
    name, loc, iotype = cells[0], cells[5], cells[6]
    m = re.fullmatch(r'(IO[TBLR]\d+)\[([A-Z])\]', loc)
    if not m or name in seen:
        continue
    seen.add(name)
    print(f'IO_LOC "{name}" {m[1]}{m[2]};')
    print(f'IO_PORT "{name}" IO_TYPE={iotype};')
