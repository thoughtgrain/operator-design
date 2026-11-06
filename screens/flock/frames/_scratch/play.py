import sys
sys.path.insert(0, sys.argv[1])
import build as b
from dataclasses import replace
from pathlib import Path
out = Path(sys.argv[2])
st = replace(b.DEFAULT, crank_turn=120, drift=0.35, lit=6, pluck=0.8, bob=4, playing=True)
b.write(st, "playing", "playing", out)
