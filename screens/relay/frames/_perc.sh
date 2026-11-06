#!/bin/sh
# scratch: copy frames to c<N>-NNN names and run the perceptibility check
cd /home/claude/operator-design
D=screens/relay/frames
mkdir -p $D/_perc
i=1
for c in stages leak clock feedback; do
  for v in 0 50 100; do cp $D/$c-$v.svg $D/_perc/c$i-$(printf %03d $v).svg; done
  i=$((i+1))
done
python3 opxy/tools/perceptibility.py $D/_perc --scores 5,4,3,4 --names stages,leak,clock,feedback
