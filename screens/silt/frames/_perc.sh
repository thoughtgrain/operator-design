set -e
cd /home/claude/operator-design/screens/silt/frames
rm -rf _p && mkdir _p
i=1; for c in settle layers stir grain; do for v in 0 50 100; do cp $c-$v.svg _p/c$i-$(printf %03d $v).svg; done; i=$((i+1)); done
cp rest.svg playing.svg _p/
python3 /home/claude/operator-design/opxy/tools/perceptibility.py _p --scores 4,4,5,3 --names settle,layers,stir,grain --header-bottom 20
rm -rf _p
