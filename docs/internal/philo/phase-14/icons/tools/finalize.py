import json, os
from PIL import Image
S=os.path.dirname(os.path.abspath(__file__))
OUT="/Users/karol/dev/tools/HoldSpeak/wt-p14-a0-icons/docs/internal/philo/phase-14/icons/candidates"
picks=json.load(open(f"{S}/picks.json"))
for D,kinds in picks.items():
    os.makedirs(f"{OUT}/{D}",exist_ok=True)
    for k,ref in kinds.items():
        b,i=ref.split(":")
        im=Image.open(f"{S}/raw/{D}{b}/f{i}.png").convert("RGBA")
        assert im.size==(64,64)
        im.save(f"{OUT}/{D}/{k}-64.png")
        sm=im.resize((32,32),Image.BOX)
        r,g,bb,a=sm.split()
        a=a.point(lambda v:255 if v>=128 else 0)
        Image.merge("RGBA",(r,g,bb,a)).save(f"{OUT}/{D}/{k}-32.png")
print("ok")
