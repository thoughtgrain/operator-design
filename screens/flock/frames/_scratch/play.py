import sys
sys.path.insert(0, sys.argv[1])
import build as b
from dataclasses import replace
from pathlib import Path
out = Path(sys.argv[2])
st = replace(b.DEFAULT, crank_turn=120, ride=(0.0, 0.2, 0.0, 0.25, 0.0, 0.3, 0.35, 0.0), lit=6, pluck=0.8, bob=4, playing=True)
b.write(st, "playing", "playing", out)
