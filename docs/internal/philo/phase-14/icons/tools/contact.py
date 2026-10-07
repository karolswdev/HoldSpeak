"""Contact sheet: each PNG at 64 on the dark desk (#3c4454) and at 32 on the steel screen (#9ea4b0).
usage: contact.py out.png scale file1 file2 ...  (scale magnifies the whole sheet, nearest)"""
import sys
from PIL import Image, ImageDraw

out, scale, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
DARK, DITHER, STEEL = (0x3C, 0x44, 0x54), (0x36, 0x3E, 0x4D), (0x9E, 0xA4, 0xB0)
cell = 80
W = cell * len(files)
sheet = Image.new("RGB", (W, cell + 48), DARK)
d = ImageDraw.Draw(sheet)
for y in range(0, cell, 2):
    for x in range(0, W, 2):
        if (x // 2 + y // 2) % 2:
            d.point((x, y), DITHER)
d.rectangle([0, cell, W, cell + 48], fill=STEEL)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA")
    if im.size != (64, 64):
        im = im.resize((64, 64), Image.NEAREST)
    sheet.paste(im, (i * cell + 8, 8), im)
    small = im.resize((32, 32), Image.BOX)
    sheet.paste(small, (i * cell + 24, cell + 8), small)
    d.text((i * cell + 2, cell + 40), str(i), fill=(0, 0, 0))
if scale > 1:
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
sheet.save(out)
