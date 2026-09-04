# Evidence - HS-169-01

- **Story:** HS-169-01 - The settled design + the canvas (the one-screen door; the Room as four questions; eight artboards at 1440 + 393; counsel first; OWNER RATIFIES)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-04T23:00:16Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/check_169_canvas.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6459eadf4c6cc91ac1c6e0fbe7dbe476e4872014

```text
BAD DoorAdjust.dc.html     off-palette=- accent-edge=0 head=True display=0 shot=False
BAD DoorChecking.dc.html   off-palette=- accent-edge=0 head=True display=0 shot=False
BAD DoorCold.dc.html       off-palette=- accent-edge=0 head=True display=0 shot=False
BAD DoorEmpty.dc.html      off-palette=- accent-edge=0 head=True display=0 shot=False
BAD DoorPhone.dc.html      off-palette=- accent-edge=0 head=True display=0 shot=False
BAD DoorPicker.dc.html     off-palette=- accent-edge=0 head=True display=0 shot=False
BAD History.dc.html        off-palette=- accent-edge=0 head=True display=1 shot=False
BAD Main.dc.html           off-palette=- accent-edge=0 head=True display=0 shot=False
BAD Room.dc.html           off-palette=- accent-edge=0 head=True display=1 shot=False
BAD RoomPhone.dc.html      off-palette=- accent-edge=0 head=True display=1 shot=False
BAD RoomQuiet.dc.html      off-palette=- accent-edge=0 head=True display=1 shot=False
artboards: 11 failures: 11
```

### Captured run — 2026-09-04T23:00:49Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/check_169_canvas.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6459eadf4c6cc91ac1c6e0fbe7dbe476e4872014

```text
OK  DoorAdjust.dc.html     off-palette=- accent-edge=0 head=True display=0 shot=True
OK  DoorChecking.dc.html   off-palette=- accent-edge=0 head=True display=0 shot=True
OK  DoorCold.dc.html       off-palette=- accent-edge=0 head=True display=0 shot=True
OK  DoorEmpty.dc.html      off-palette=- accent-edge=0 head=True display=0 shot=True
OK  DoorPhone.dc.html      off-palette=- accent-edge=0 head=True display=0 shot=True
OK  DoorPicker.dc.html     off-palette=- accent-edge=0 head=True display=0 shot=True
OK  History.dc.html        off-palette=- accent-edge=0 head=True display=1 shot=True
OK  Main.dc.html           off-palette=- accent-edge=0 head=True display=0 shot=True
OK  Room.dc.html           off-palette=- accent-edge=0 head=True display=1 shot=True
OK  RoomPhone.dc.html      off-palette=- accent-edge=0 head=True display=1 shot=True
OK  RoomQuiet.dc.html      off-palette=- accent-edge=0 head=True display=1 shot=True
artboards: 11 failures: 0
```
