import colorsys, sys
from PIL import Image
from pathlib import Path
D=Path('/Users/karol/dev/tools/HoldSpeak/wt-p14-a0c/web/public/desk/sprites/system')
OUT=Path(sys.argv[1])
def lighten(im):
    im=im.convert('RGBA'); px=im.load(); w,h=im.size
    for y in range(h):
        for x in range(w):
            r,g,b,a=px[x,y]
            if not a: continue
            hh,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
            if s>0.35 and l>0.25: continue  # the ember accent stays
            if l<0.16: continue             # the outline stays
            l2=l+(0.84-l)*0.4               # grey body lifted toward the steel highlight
            r2,g2,b2=colorsys.hls_to_rgb(hh,l2,s)
            px[x,y]=(round(r2*255),round(g2*255),round(b2*255),a)
    return im
for n in ['mic','dock-speak']:
    lighten(Image.open(D/f'{n}.png')).save(OUT/f'{n}.png')
