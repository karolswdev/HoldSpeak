# Walks

A walk is a short guided review of the Desk. It opens windows, marks one part
of a window, and asks one question about it. You answer with one press.

## Open a walk

1. Open the link that you got. It starts with `/w/`.
2. The Desk opens. A thin pixel frame in the accent colour goes around the
   screen. The frame shows that the guide controls the walk. The guide is
   the pixel robot at the top-left corner. Its bubble shows the words of
   the step.
3. If the voice is on, press **Tap to begin**. The guide speaks each step
   and each question through the Desk voice (the hub voice, else the
   browser voice). The speaker button on the sheet turns the voice on or
   off on this device. The voice is on by default on a phone.
4. The guide opens the windows and presses the buttons. You watch: a pixel
   cursor goes to the button, and the button gets a ring.
5. The walk makes the Desk dark, but not the part that you must look at. The
   part has a ring in the accent colour.
6. Read the question. Press a choice, for example **Keep** or **Redo**.
7. To add words, press **Say more**. Type or speak. Then press a choice, or
   press **Send** to send only the words. Words do not select a choice: the
   answer shows `words`.
8. To go to the next step without an answer, press **Skip** or Esc. On a
   phone, you can also swipe the top of the sheet down.
9. At the end, press **Back to the desk**. The windows stay open.

You can use the part that has the ring, for example **New program**. The card
shows one dot for each question and the step number, for example `3 of 7`.
On a phone, the card is a sheet at the bottom, above the Dock, and the part
moves above the sheet. If a window has no such part, for example no people,
the guide says so (`No people rows here yet`) and goes to the next step.

If the link does not open, the Desk shows one line and then operates as usual.

## Make a walk

A walk is a JSON file. Each step has one or more of these keys. The walk does
them in this order: `open`, `verb`, `press`, `scroll`, `say`, `highlight`,
`ask`.

| Key | What it does |
| --- | --- |
| `open` | Opens an application window: `{"app": "surface-programs"}`. `app` is an application key or window id, or a Chair window such as `chair:needs`. `scope` is optional. `@first-project` and `@first-meeting` mean your first project or meeting. If there is none, the walk skips the step. |
| `verb` | Runs one Desk verb: `{"verb": "desk.refresh"}`. |
| `press` | The guide presses one part: `{"target": "programs-new", "words": "I press New program."}`. The cursor goes to the part in 0.5 s, the ring pulses, the walk clicks the part, and then waits 0.6 s. |
| `scroll` | Moves one part into the clear area above the sheet: `{"target": "room-fold-programs"}`. |
| `say` | The bubble shows the words: `{"words": "We start in Programs."}`. Nothing gets dark. A step with only `say` goes on after the words are read. |
| `highlight` | Marks one part: `{"target": "programs-new", "words": "..."}`. A plain name is a `data-testid`. Other text is a CSS selector. The walk looks only in the window of the step: `window`, else the last `open`. If that window is not open, the walk skips the step. |
| `thing` | In `press`, `scroll` or `highlight`: the name of the part, for example `"people rows"`. If the window has no such part, the guide says `No people rows here yet` and skips the step without a question. |
| `ask` | Asks one question: `{"ref": "s11-well", "question": "...", "choices": ["Keep", "Redo"]}`. |

`target` and `window` in `press` and `scroll` work as in `highlight`. An
`open` of a Project Room (`open-project-memory` with a project scope) shows
the Room, not the Update posture that the Room kept from an earlier visit.

Example: `docs/walks/2026-11-08-handheld.json`. To make a walk and get its
two links (the Tailscale IP first, then this computer), and to read the answers:

    uv run python scripts/walk.py new docs/walks/2026-11-07-wave-two.json
    uv run python scripts/walk.py read <id>

## What the hub keeps

Each walk is one folder: `~/.local/share/holdspeak/feedback/walks/<id>/`.

- `walk.json` keeps the script, the answers, and a hash of the link token.
  The token reads only its walk and stores only its answers.
- Each answer keeps a PNG image of the full screen as you saw it, without
  the walk frame, guide and sheet, for example `s11-well.png`, 16 MiB or
  less. The answer also keeps `view`: the screen width and height in CSS px,
  the device pixel ratio, the image scale, the platform and browser (for
  example `iPhone · Safari 26`), and the box of the part of the step. To cut
  out the part, multiply the box by the scale.
- One image for each question; a new image replaces the earlier one. The hub
  keeps the text of the last 5 earlier answers.
- All images 64 MiB or less. After this, the hub keeps the answer without the
  image and shows `walk_shot_budget`. One answer 24 MiB or less (else 413).
- An unknown link gets 404 and counts as a wrong try. Too many wrong tries
  from one address in one minute get 429.

The walk link opens the desk by itself: the redirect carries the desk's own bootstrap token, as the address `holdspeak web` prints does. Send a walk link only to the owner, over the tailnet.
