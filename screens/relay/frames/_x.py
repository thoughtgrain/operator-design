import sys, subprocess
sys.path.insert(0, '.')
import build
combos = {"_x1": dict(stages=0, leak=0, clock=1, feedback=1), "_x2": dict(stages=1, leak=1, clock=1, feedback=1),
          "_x3": dict(stages=0, leak=1, clock=1, feedback=0)}
for k, c in combos.items():
    open(k + ".svg", "w").write(build.draw(c, k).svg())
    subprocess.run(["rsvg-convert", "-w", "480", "-h", "220", "-b", "black", k + ".svg", "-o", k + ".png"], check=True)
    print(k, open(k + ".svg").read().count("<path"))
from PIL import Image
for stem in ["rest", "_x1", "_x2"] + [f"{n}-{v}" for n in build.LABELS for v in (0, 50, 100)]:
    im = Image.open(stem + ".png").convert("L").crop((0, 20, 480, 220))
    px = list(im.getdata())
    print(stem, "black %.1f%%" % (100 * sum(1 for p in px if p < 8) / len(px)), "paths", open(stem + ".svg").read().count("<path"))
