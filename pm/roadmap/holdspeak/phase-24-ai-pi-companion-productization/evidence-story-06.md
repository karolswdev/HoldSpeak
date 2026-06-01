# Evidence — HS-24-06 — Companion Public Docs and PixelLab Artwork

## Commit Trail

```text
$ git show --stat --oneline 11af81b 010a3ea a7fe78b a720af0
11af81b Add PixelLab documentation artwork
 README.md                                              |  13 +++++++++++++
 docs/GETTING_STARTED.md                                |   4 ++++
 docs/USER_GUIDE.md                                     |   7 +++++++
 docs/assets/pixellab/README.md                         |  10 ++++++++++
 docs/assets/pixellab/hold-to-talk-microphone.png       | Bin 0 -> 2458 bytes
 docs/assets/pixellab/meeting-intelligence-notebook.png | Bin 0 -> 1505 bytes
 docs/assets/pixellab/project-aware-typing.png          | Bin 0 -> 1628 bytes
 7 files changed, 34 insertions(+)
010a3ea Clarify docs artwork and clipboard token
 README.md                      | 18 +++++++++++-------
 docs/AIPI_LITE_DEV_WORKFLOW.md |  4 ++++
 docs/GETTING_STARTED.md        | 19 +++++++++++++++++--
 docs/USER_GUIDE.md             | 21 +++++++++++++++++----
 4 files changed, 49 insertions(+), 13 deletions(-)
a7fe78b Add transparent AIPI companion artwork
 README.md                                    |  10 ++++++----
 docs/AIPI_LITE_DEV_WORKFLOW.md               |   7 ++++++-
 docs/assets/pixellab/README.md               |   1 +
 docs/assets/pixellab/aipi-lite-companion.png | Bin 0 -> 13475 bytes
 4 files changed, 13 insertions(+), 5 deletions(-)
a720af0 Document AIPI agent companion use case
 README.md                      | 14 ++++++++++++--
 docs/AIPI_LITE_DEV_WORKFLOW.md | 19 +++++++++++++++----
 docs/USER_GUIDE.md             |  1 +
 3 files changed, 28 insertions(+), 6 deletions(-)
```

## Reference Checks

```text
$ rg -n "aipi-lite-companion.png|AIPI-Lite companion|Claude/Codex|clipboard|Workflow Map|AIPI-LIte.jpg" README.md docs/AIPI_LITE_DEV_WORKFLOW.md docs/USER_GUIDE.md docs/GETTING_STARTED.md docs/assets/pixellab/README.md
docs/assets/pixellab/README.md:11:| `aipi-lite-companion.png` | `c76b85ce-e780-4126-bc00-d004d885de3c` | Transparent background pixel art of a portable green ESPHome AI companion device inspired by AIPI-Lite hardware, handheld rectangular board with black screen, small microphone grille, two physical buttons, USB-C port, tiny Wi-Fi hotspot signal icon, meeting recording status glow, clean product documentation asset. |
docs/USER_GUIDE.md:6:- **Intelligent typing:** hold a hotkey, speak, and insert useful text into the active app. For coding assistants, HoldSpeak can use project context and recent Claude/Codex state to rewrite dictation into better prompts.
docs/USER_GUIDE.md:31:| AIPI-Lite companion | Portable ESPHome device for meeting controls, status, and spoken replies to waiting Claude/Codex sessions | [AIPI-Lite Developer Workflow](AIPI_LITE_DEV_WORKFLOW.md), `/companion` |
docs/USER_GUIDE.md:109:Say `clipboard` anywhere in a dictated phrase to insert the current clipboard
docs/USER_GUIDE.md:110:text at that position. HoldSpeak treats `clipboard` as a replacement token, so
docs/USER_GUIDE.md:111:the word itself is removed and the actual clipboard contents are inserted into
docs/USER_GUIDE.md:117:Taking a look at this clipboard could you refactor it?
docs/USER_GUIDE.md:120:If the clipboard contains:
README.md:7:**Voice typing** — hold your configured hotkey, speak, release. Text appears in any app. Punctuation commands (`"period"`, `"comma"`, etc.) work out of the box. When you say `"clipboard"` inside a dictated phrase, HoldSpeak replaces that word with the current clipboard text.
README.md:13:## Workflow Map
README.md:23:  <img src="docs/assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="260">
README.md:26:The optional AIPI-Lite companion is a portable ESPHome-based device you can
README.md:31:It also works as a coding-agent companion. With Claude/Codex hooks enabled,
docs/GETTING_STARTED.md:109:Say `clipboard` inside a dictated phrase when you want HoldSpeak to splice in
docs/GETTING_STARTED.md:110:the current clipboard text. The word `clipboard` is removed from the output and
docs/GETTING_STARTED.md:111:replaced with the clipboard contents.
docs/GETTING_STARTED.md:116:Taking a look at this clipboard could you refactor it?
docs/GETTING_STARTED.md:119:If the clipboard contains a code block, that code is inserted into the same
docs/AIPI_LITE_DEV_WORKFLOW.md:4:  <img src="assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="280">
docs/AIPI_LITE_DEV_WORKFLOW.md:7:The AIPI-Lite companion is a portable ESPHome-based device for meeting capture,
docs/AIPI_LITE_DEV_WORKFLOW.md:12:With Claude/Codex hooks enabled, HoldSpeak can show when an agent is waiting
```

`AIPI-LIte.jpg` does not appear in the reference-check output, confirming the
hard-background JPG is no longer used by these docs.

## Image Transparency Check

```text
$ python3 - <<'PY'
from PIL import Image
for p in [
    'docs/assets/pixellab/hold-to-talk-microphone.png',
    'docs/assets/pixellab/meeting-intelligence-notebook.png',
    'docs/assets/pixellab/project-aware-typing.png',
    'docs/assets/pixellab/aipi-lite-companion.png',
]:
    im = Image.open(p)
    alpha = im.getchannel('A') if im.mode == 'RGBA' else None
    print(p, im.mode, im.size, (min(alpha.getdata()), max(alpha.getdata())) if alpha else 'no-alpha')
PY
docs/assets/pixellab/hold-to-talk-microphone.png RGBA (128, 128) (0, 255)
docs/assets/pixellab/meeting-intelligence-notebook.png RGBA (128, 128) (0, 255)
docs/assets/pixellab/project-aware-typing.png RGBA (128, 128) (0, 255)
docs/assets/pixellab/aipi-lite-companion.png RGBA (192, 192) (0, 255)
```

## Notes

- This was docs/productization work only; no runtime tests were necessary.
- Product links were checked live on 2026-06-01 before landing:
  - <https://aipi.com/products/aipi-lite>
  - <https://www.amazon.com/dp/B0FQNNVV36>
