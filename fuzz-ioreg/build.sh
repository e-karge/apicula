#!/bin/sh
# build.sh NAME FAMILY PART VENDOR_DEVICE [VERILOG]: vendor (registers in IOBs)
# and open toolchain builds of VERILOG (default top.v) in $OUT/NAME;
# $VCST: constraints for the vendor build
OUT=${OUT:-$HOME/opt/claude-scratch/ioreg}
name=$1 family=$2 part=$3 vdev=$4 src=$(readlink -f ${5:-top.v})
here=$(dirname $(readlink -f $0)); A=$(dirname $here)
B=$HOME/opt/claude-scratch/nextpnr-gw5a-build
G=$HOME/opt/gowin/1.9.10.03; R=$HOME/opt/gowin/sysroot-amd64
d=$OUT/$name; mkdir -p $d/v; cd $d || exit 1
if [ ! -f vendor.fs ] || [ $src -nt vendor.fs ] || [ -n "$VCST" -a "$VCST" -nt vendor.fs ]; then
    cat > v/r.tcl <<EOT
set_option -verilog_std sysv2017
add_file -type verilog $src
$([ -n "$VCST" ] && echo "add_file -type cst $(readlink -f $VCST)")
set_device -name $vdev $part
set_option -output_base_name top
set_option -ireg_in_iob 1
set_option -oreg_in_iob 1
set_option -ioreg_in_iob 1
catch {set_option -use_sspi_as_gpio 1}
catch {set_option -use_mspi_as_gpio 1}
catch {set_option -use_ready_as_gpio 1}
catch {set_option -use_done_as_gpio 1}
catch {set_option -use_reconfign_as_gpio 1}
catch {set_option -use_i2c_as_gpio 1}
catch {set_option -use_cpu_as_gpio 1}
run all
EOT
    (cd v && rm -rf impl && timeout 3000 qemu-x86_64 -L $R -E LD_LIBRARY_PATH=$G/IDE/lib -E LD_PRELOAD=$G/Programmer/bin/libfontconfig.so.1 $G/IDE/bin/gw_sh r.tcl > gw.log 2>&1)
    [ -f v/impl/pnr/top.fs ] || { echo "$name: vendor failed: $(grep -m1 ERROR v/gw.log)"; exit 1; }
    rm -f vendor.fs; cp v/impl/pnr/top.fs vendor.fs
fi
python3 $here/pins.py v/impl/pnr/top.pin.html > top.cst
$HOME/.local/bin/yosys -q -p "read_verilog $src; synth_gowin -json synth.json" > ys.log 2>&1 || { echo "$name: synth failed"; exit 1; }
$B/nextpnr-himbaechel --chipdb $OUT/chipdb-$family.bin --json synth.json --write pnr.json --device $part \
    --timing-allow-fail --vopt family=$family --vopt cst=top.cst --vopt ireg_in_iob --vopt oreg_in_iob --vopt ioreg_in_iob > pnr.log 2>&1 \
    || { echo "$name: pnr failed: $(grep -m1 ERROR pnr.log)"; exit 1; }
PYTHONPATH=$A python3 -m apycula.gowin_pack -d $family -o open.fs pnr.json > pack.log 2>&1 || { echo "$name: pack failed: $(tail -1 pack.log)"; exit 1; }
echo "$name: vendor $(grep -o 'I/O Register as FF *| *[0-9]*' v/impl/pnr/top.rpt.txt | tr -s ' '), open $(grep -E 'IOLOGIC[IO]:' pnr.log | tr -s ' ' | sed 's/Info: //' | tr '\n' ' ')"
