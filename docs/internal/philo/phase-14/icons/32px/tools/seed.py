from PIL import Image
from pathlib import Path
S=Path('/Users/karol/dev/tools/HoldSpeak/wt-p14-a0c/web/public/desk/sprites')
names=sorted(p.stem for p in S.glob('*.png') if not p.stem.endswith(('_sel','_stale')))
def box(im):
    # premultiplied 2x2 box average, alpha cut at 50%
    w,h=im.size; src=im.load(); out=Image.new('RGBA',(w//2,h//2),(0,0,0,0)); d=out.load()
    for y in range(h//2):
        for x in range(w//2):
            px=[src[2*x+i,2*y+j] for i in (0,1) for j in (0,1)]
            a=sum(p[3] for p in px)
            if a/4<128: continue
            r=sum(p[0]*p[3] for p in px)/a; g=sum(p[1]*p[3] for p in px)/a; b=sum(p[2]*p[3] for p in px)/a
            d[x,y]=(round(r),round(g),round(b),255)
    return out
cols=6; rows=3
sheet=Image.new('RGBA',(cols*140,rows*140*2),(60,68,84,255))
for i,n in enumerate(names):
    im=Image.open(S/f'{n}.png').convert('RGBA')
    b=box(im); b.save(f'seed/{n}.png')
    sheet.alpha_composite(b.resize((128,128),Image.NEAREST),((i%cols)*140+6,(i//cols)*140+6))
    # light ground
    bg=Image.new('RGBA',(140,140),(158,164,176,255)); bg.alpha_composite(b.resize((128,128),Image.NEAREST),(6,6))
    sheet.alpha_composite(bg,((i%cols)*140,rows*140+(i//cols)*140))
sheet.save('seedsheet.png')
