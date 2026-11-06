import math, sys
sys.path.insert(0, '../passes/02-subject')
from sketch import Camera
for H,F in [(2.0,700),(2.5,900),(3.0,1050)]:
  for ang in [50,58,65]:
    a=math.radians(ang)
    look=(0, H/math.tan(a), 0)  # look at surface point
    cam = Camera((0,0,H), look, F, (240,104))
    def sy(y): return cam((0,y,0))[1]
    def solve(target):
        lo,hi=0.01,50
        for _ in range(80):
            m=(lo+hi)/2
            if sy(m)>target: lo=m
            else: hi=m
        return m
    y0,y1=solve(172),solve(34)
    px=lambda y: cam((0.15,y,0))[0]-cam((0,y,0))[0]
    # vertical: z of -0.05 at y0
    dz = cam((0,y0,-0.05))[1]-cam((0,y0,0))[1]
    print(H,F,ang, round(y0,3), round(y1,3), 'pitch near/far', round(px(y0),1), round(px(y1),1), round(px(y1)/px(y0),2), 'dz', round(dz,1))
