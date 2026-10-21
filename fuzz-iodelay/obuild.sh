#!/bin/sh
# obuild.sh NAME FAMILY PART [VERILOG]: open toolchain build of VERILOG
# (default top.v) with the pins of the vendor build in $OUT/NAME
OUT=${OUT:-$HOME/opt/claude-scratch/iodelay}
name=$1 family=$2 part=$3 src=$(readlink -f ${4:-top.v})
here=$(dirname $(readlink -f $0)); A=$(dirname $here)
NP=$HOME/src/claude/nextpnr-gw5a-iodelay; B=${NEXTPNR_BUILD:-$HOME/opt/claude-scratch/nextpnr-iodelay-build}
db=$OUT/chipdb-$family.bin
if [ ! -f $db ] || [ $A/apycula/$family.msgpack.xz -nt $db ]; then
    (cd $OUT && PYTHONPATH=$A python3 $NP/himbaechel/uarch/gowin/gowin_arch_gen.py -d $family -o $OUT/$family.bba > $OUT/$family.gen.log 2>&1 \
        && $B/bba/bbasm --le $OUT/$family.bba $db && rm $OUT/$family.bba) || { echo "chipdb failed"; exit 1; }
fi
d=$OUT/$name; cd $d || exit 1
$HOME/.local/bin/yosys -q -p "read_verilog $src; synth_gowin -family gw5a -json synth.json" > ys.log 2>&1 || { echo "$name: synth failed"; exit 1; }
$B/nextpnr-himbaechel --chipdb $db --json synth.json --write pnr.json --device $part --timing-allow-fail \
    --vopt family=$family --vopt cst=top.cst > pnr.log 2>&1 || { echo "$name: pnr failed: $(grep -m1 ERROR pnr.log)"; exit 1; }
PYTHONPATH=$A python3 -m apycula.gowin_pack -d $family -o open.fs pnr.json > pack.log 2>&1 || { echo "$name: pack failed: $(tail -1 pack.log)"; exit 1; }
echo "$name: open ok"
