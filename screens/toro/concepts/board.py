#!/usr/bin/env python3
"""Round 5 board: python3 board.py . board-rider.png <tmpdir>  (rows r1–r5, columns rest/spread/cutoff/fold/aphx/playing at 1:1)"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
root=Path(sys.argv[1]); out=sys.argv[2]; tmp=Path(sys.argv[3])
styles=["r1-crt","r2-halftone","r3-ink","r4-iso","r5-bauhaus"]
poses=["rest","spread-100","cutoff-100","fold-100","aphx-100","playing"]
W,H,P=480,220,8
B=Image.new("RGB",(P+len(poses)*(W+P),P+18+len(styles)*(H+P)),(40,40,40))
d=ImageDraw.Draw(B)
for j,p in enumerate(poses): d.text((P+j*(W+P),P),p,fill=(200,200,200))
for i,s in enumerate(styles):
  for j,p in enumerate(poses):
    png=tmp/f"{s}_{p}.png"
    subprocess.run(["rsvg-convert","-w","480","-h","220",str(root/s/f"{p}.svg"),"-o",str(png)],check=True)
    B.paste(Image.open(png).convert("RGB"),(P+j*(W+P),P+18+i*(H+P)))
B.save(out)
