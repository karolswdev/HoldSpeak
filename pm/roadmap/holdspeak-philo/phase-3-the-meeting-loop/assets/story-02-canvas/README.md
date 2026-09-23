# PHILO-3-02 corrected Arrival canvas

**PENDING OWNER RATIFICATION.** This directory is the corrected static canvas
for the existing Arrival meeting row. It is not product code and it is not a
live product shot.

The one owner ratification question is: **is this corrected existing-row
presentation of transcript, arriving summary, and retry/failure facts the face
to build?**

Muad'Dib: publish this set for that owner decision. The Arrival face remains
held until the owner ratifies it.

| State | 1440 arrival | 393 arrival | 393 footer after scroll |
| --- | --- | --- | --- |
| Imported | [PNG](summary-imported.dc.png) | [PNG](summary-imported-phone.dc.png) | [PNG](summary-imported-phone.dc-footer.png) |
| Ready | [PNG](summary-ready.dc.png) | [PNG](summary-ready-phone.dc.png) | [PNG](summary-ready-phone.dc-footer.png) |
| Retrying | [PNG](summary-retrying.dc.png) | [PNG](summary-retrying-phone.dc.png) | [PNG](summary-retrying-phone.dc-footer.png) |
| Failed | [PNG](summary-failed.dc.png) | [PNG](summary-failed-phone.dc.png) | [PNG](summary-failed-phone.dc-footer.png) |

The editable HTML boards are listed in [canvas.json](canvas.json).

The eight boards keep the current row grammar and locations:

- `imported`: `35 S`, `81 WORDS`, `OFF`, planned `RUNS ON 192.168.1.43 · LAN`, and `Run summary` beside the existing route disclosure.
- `ready`: `35 S`, `81 WORDS`, `RAN`, actual `192.168.1.43 · LAN` receipt, the existing `Open` verb, and the summary plus transcript wells.
- `retrying`: `1 need you`, `RETRYING`, and `LAST ATTEMPT` / `LAST ERROR` facts in the existing summary well. There is no new row verb or attempt limit.
- `failed`: `1 need you`, `FAILED`, and `LAST ATTEMPT` / `LAST ERROR` facts in the existing summary well. There is no new row verb or attempt limit.

Each state has a 1440x900 board and a 393x852 board. The Chair owns the
scroll, the dock is a reserved shell band, and phone verbs have a 44 px
painted target. The CSS uses current Signal values (`#8b93a3` faint and
`#8a5a3d` filled accent ink) and the interior type steps: display 26, title
15, body 13, readable floor 12 px.

The source text is `tests/fixtures/philo3_architect_meeting.txt`, with its
retained generated audio facts of 34.67525 seconds and 81 words. The boards
show the human duration as `35 S`, retain the complete source owners and
actions, and use one generic unlabelled transcript voice. The canvas chrome
marks the boards `CANVAS · STATIC MOCK`; the ready summary is fixture
content outside product output. No board claims a real model result, host
execution, restart retrieval, or owner sitting.

Run the capture and static checks with Node 22 first in `PATH`, an isolated
`HOME`, and the existing browser cache:

```sh
PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH \
HOME=$(mktemp -d) \
PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
.venv/bin/python pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-canvas/capture-and-validate.py
```

The command retains eight arrival-position PNGs and four additional phone footer PNGs, `validation.json`, and `validation.log` in
this directory. The validation records the title and font checks, the
scroll-owning Chair, and `elementFromPoint` hits at the center, four edges,
and four corners of each phone `Run summary` or `Open` target. It does not
start a product server or hub and does not write desk state.

The canvas carries the Latin WOFF2 files used by the shipped Signal stack
(Inter, Space Grotesk, and JetBrains Mono) with their package licenses. The
capture waits for `document.fonts.ready` and records all three faces as
loaded in `validation.json`; the mono chrome uses the available 500 weight.

Astra retained each main board before the pointer checks scroll, then a separate
`summary-STATE-phone.dc-footer.png` after the footer checks. The main ready
board therefore shows its title, receipt and summary; the footer view proves
the lower controls remain reachable within the reserved working band.
