"""Paste a direction's icons into the A-1 board (2880x1800, DPR 2: a 64 CSS px sprite = 128 device px).
usage: insitu.py <D> <out_full.png> <out_crop.png>"""
import sys
from PIL import Image

D, out_full, out_crop = sys.argv[1:4]
ROOT = "/Users/karol/dev/tools/HoldSpeak/wt-p14-a0-icons/docs/internal/philo/phase-14"
board = Image.open(f"{ROOT}/canvas/shots/A-1-1440.png").convert("RGB")
orig = board.copy()

# (kind, x0, y0, has_count, has_lamp, has_badge) : art-box origins in device px, measured on A-1.
ICONS = [
    ("project-drawer", 88, 87, 1, 1, 0),      # Payments ledger
    ("project-drawer", 88, 311, 1, 0, 0),     # Platform observability
    ("project-drawer", 88, 535, 1, 0, 0),     # Staff hiring loop
    ("people-ledger", 88, 759, 0, 0, 0),      # People
    ("conductor-drawer", 88, 983, 1, 1, 1),   # Conductor
    ("meeting", 468, 112, 0, 0, 0),           # Ledger cutover sync
    ("meeting", 708, 112, 0, 1, 0),           # Vendor call
    ("note", 948, 112, 0, 0, 0),              # Questions for Avery 1:1
    ("note", 1188, 112, 0, 0, 0),             # Idea: shard the...
    ("artifact", 1428, 112, 0, 0, 0),         # Cutover requirements
    ("decision", 1668, 112, 0, 1, 0),         # Adopt OpenTelemetry
    ("repository", 468, 344, 0, 0, 0),        # payments-ledger
    ("person", 708, 344, 0, 0, 0),            # Avery Chen
    ("agent-claude-code", 2386, 89, 0, 1, 0), # Claude Code: rollback...
    ("smart-drawer", 2648, 87, 1, 1, 0),      # Needs you
    ("parked-drawer", 2648, 1389, 0, 0, 0),   # Parked
]
EMPTY = (1920, 640)  # an empty stretch of screen (pattern source)


def bg_patch(x, y, w, h):
    sx = EMPTY[0] + ((x - EMPTY[0]) % 32)
    sy = EMPTY[1] + ((y - EMPTY[1]) % 32)
    return orig.crop((sx, sy, sx + w, sy + h))


PLATES = {(138, 90, 61), (240, 138, 75), (242, 201, 76)}  # count plate, ask lamp, due lamp


def plate_rect(area):
    """The exact count/lamp rect: the bbox of its fill colour, grown by the bevel and the 2 px ink ring."""
    xs, ys = [], []
    for x in range(area[0], area[2]):
        for y in range(area[1], area[3]):
            if orig.getpixel((x, y)) in PLATES:
                xs.append(x); ys.append(y)
    assert xs, area
    return (min(xs) - 4, min(ys) - 4, max(xs) + 5, max(ys) + 5)


for kind, x0, y0, cnt, lamp, badge in ICONS:
    keep = []
    if cnt:
        keep.append(plate_rect((x0 - 24, y0 - 20, x0 + 40, y0 + 32)))
    if lamp:
        keep.append(plate_rect((x0 + 100, y0 - 16, x0 + 144, y0 + 24)))
    x1, y1 = x0 + 128 + (24 if badge else 4), y0 + 128 + (16 if badge else 4)
    board.paste(bg_patch(x0 - 4, y0 - 4, x1 - x0 + 4, y1 - y0 + 4), (x0 - 4, y0 - 4))
    for r in keep:  # count and lamp stay under the new sprite edge
        board.paste(orig.crop(r), r[:2])
    ico = Image.open(f"{ROOT}/icons/candidates/{D}/{kind}-64.png").convert("RGBA").resize((128, 128), Image.NEAREST)
    board.paste(ico, (x0, y0), ico)
    for r in keep:  # the count and the lamp sit over the sprite
        board.paste(orig.crop(r), r[:2])

board.save(out_full)
board.crop((0, 58, 1880, 1180)).save(out_crop)
