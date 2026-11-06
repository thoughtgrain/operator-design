import sys, importlib, subprocess, math
sys.path.insert(0, '/home/claude/operator-design/screens/lathe/frames')
import build as b
from PIL import Image
def mk(ang, F, wall, name):
    b._ang = math.radians(ang)
    b.CAM = b.Camera((0.0, 0.0, 2.0), (0.0, 2.0 / math.tan(b._ang), 0.0), F, (b.CENTRE_X, 104))
    b.Y0 = b._y_for_screen(b.Y_NEAR_SCREEN); b.Y1 = b._y_for_screen(b.Y_FAR_SCREEN)
    b.WALL_SCREEN = wall; b.Y_WALL = b._y_for_screen(wall)
    b.WEAR[:] = b._wear_items()
    p = f'/home/claude/operator-design/screens/lathe/frames/_scratch/{name}.svg'
    open(p,'w').write(b.build().svg())
    b.render_png(p, p.replace('.svg','.png'))
    near = b.CAM((b.P,b.Y0,0))[0]-b.CAM((0,b.Y0,0))[0]
    print(name, round(near,1))
    return p.replace('.svg','.png')
ims=[mk(54,680,96,'A'), mk(46,720,70,'B'), mk(54,680,46,'C'), mk(42,760,60,'D')]
sheet=Image.new('RGB',(960+12,440+12),(38,38,38))
for i,p in enumerate(ims):
    sheet.paste(Image.open(p).convert('RGB'),((i%2)*(480+12),(i//2)*(220+12)))
sheet.save('/home/claude/operator-design/screens/lathe/frames/_scratch/variants.png')
