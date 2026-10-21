#!/bin/sh
# vbuild.sh NAME PART VENDOR_DEVICE [VERILOG]: vendor build in $OUT/NAME;
# $VCST: constraints
OUT=${OUT:-$HOME/opt/claude-scratch/iodelay}
name=$1 part=$2 vdev=$3 src=$(readlink -f ${4:-top.v})
here=$(dirname $(readlink -f $0))
G=$HOME/opt/gowin/1.9.10.03; R=$HOME/opt/gowin/sysroot-amd64
d=$OUT/$name; mkdir -p $d/v; cd $d || exit 1
cat > v/r.tcl <<EOT
set_option -verilog_std sysv2017
add_file -type verilog $src
$([ -n "$VCST" ] && echo "add_file -type cst $(readlink -f $VCST)")
set_device -name $vdev $part
set_option -output_base_name top
run all
EOT
(cd v && rm -rf impl && timeout 3000 qemu-x86_64 -L $R -E LD_LIBRARY_PATH=$G/IDE/lib -E LD_PRELOAD=$G/Programmer/bin/libfontconfig.so.1 $G/IDE/bin/gw_sh r.tcl > gw.log 2>&1)
[ -f v/impl/pnr/top.fs ] || { echo "$name: vendor failed: $(grep -m1 ERROR v/gw.log)"; exit 1; }
rm -f vendor.fs; cp v/impl/pnr/top.fs vendor.fs
python3 $here/pins.py v/impl/pnr/top.pin.html > top.cst
echo "$name: vendor ok, $(grep -c IO_LOC top.cst) pins"
