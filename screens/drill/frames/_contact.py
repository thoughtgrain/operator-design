from PIL import Image, ImageDraw
names=['rest']+[f'{c}-{v}' for c in ('ratio','teeth','wear','bite') for v in (0,50,100)]
W,H,G,L=480,220,8,14
cols=3
im=Image.new('RGB',(cols*W+(cols+1)*G, L+H+G + 4*(L+H+G)+G),(38,38,38))
d=ImageDraw.Draw(im)
def put(name,x,y):
    d.text((x,y),name.replace('-',' '),fill=(200,200,200)); im.paste(Image.open(name+'.png').convert('RGB'),(x,y+L))
put('rest',G,G)
for r,c in enumerate(('ratio','teeth','wear','bite')):
    for k,v in enumerate((0,50,100)):
        put(f'{c}-{v}',G+k*(W+G),G+(r+1)*(L+H+G))
im.save('contact.png')
