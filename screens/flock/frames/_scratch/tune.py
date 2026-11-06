import sys, itertools, math
sys.path.insert(0, sys.argv[1])
import build as b
from dataclasses import replace
from PIL import Image
def png(st,name):
    p=b.write(st,name,'t',b.HERE/'_scratch'); return Image.open(b.render(p)).convert('L')
def diff(a,c):
    A=a.load();C=c.load();n=0
    for y in range(20,220):
        for x in range(480):
            if abs(A[x,y]-C[x,y])>=24: n+=1
    return 100*n/(480*200)
base_w=list(b.WING)
for sp, L, a0, a1 in [(0.72,1.0,198,118),(0.72,1.1,198,118),(0.75,1.1,200,116),(0.72,1.15,196,120)]:
    lo=0.9
    b.TIER={"A":lo,"B":lo+sp,"C":lo+2*sp,"D":lo+3*sp}
    b.WING=[(u*L,v) for u,v in base_w]
    b.wing_angle=lambda s,a0=a0,a1=a1: a0-(a0-a1)*s
    g=min(b.bird_gaps(replace(b.DEFAULT,cohere=c,speed=v,scatter=t)) for c in (0,.5,1) for v in (0,.5,1) for t in (0,.5,1))
    top=min(b.top_of_drawing(replace(b.DEFAULT,cohere=c,speed=v,scatter=t)) for c in (0,.5,1) for v in (0,1) for t in (0,1))
    d=diff(png(replace(b.DEFAULT,speed=0),'a'),png(replace(b.DEFAULT,speed=1),'c'))
    print(sp,L,a0,a1,'gap',round(g,1),'top',round(top,1),'speed%',round(d,2))
