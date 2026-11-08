# Walks

A walk is a short guided review of the Desk. It opens windows, marks one part
of a window, and asks one question about it. You answer with one press.

## Open a walk

1. Open the link that you got. It starts with `/w/`.
2. The Desk opens. The walk opens the first window.
3. The walk makes the Desk dark, but not the part that you must look at. The
   part has a ring in the accent colour.
4. Read the card beside the part. Press a choice, for example **Keep** or
   **Redo**.
5. To add words, press **Say more**. Type or speak. Then press a choice, or
   press **Send** to send only the words. Words do not select a choice: the
   answer shows `words`.
6. To go to the next step without an answer, press **Skip** or Esc.
7. At the end, press **Back to the desk**. The windows stay open.

You can use the part that has the ring, for example **New program**. The card
shows the step number, for example `3 of 7`. On a phone, the card is a sheet
at the bottom, above the Dock, and the part moves above the sheet.

If the link does not open, the Desk shows one line and then operates as usual.

## Make a walk

A walk is a JSON file. Each step has one or more of these keys:

| Key | What it does |
| --- | --- |
| `open` | Opens an application window: `{"app": "surface-programs"}`. `app` is an application key or window id, or a Chair window such as `chair:needs`. `scope` is optional. `@first-project` and `@first-meeting` mean your first project or meeting. If there is none, the walk skips the step. |
| `verb` | Runs one Desk verb: `{"verb": "desk.refresh"}`. |
| `highlight` | Marks one part: `{"target": "programs-new", "words": "..."}`. A plain name is a `data-testid`. Other text is a CSS selector. The walk looks only in the window of the step: `window`, else the last `open`. If that window is not open, the walk skips the step. |
| `ask` | Asks one question: `{"ref": "s11-well", "question": "...", "choices": ["Keep", "Redo"]}`. |

Example: `docs/walks/2026-11-07-wave-two.json`. To make a walk and get its
two links (Tailscale first, then this computer), and to read the answers:

    uv run python scripts/walk.py new docs/walks/2026-11-07-wave-two.json
    uv run python scripts/walk.py read <id>

## What the hub keeps

Each walk is one folder: `~/.local/share/holdspeak/feedback/walks/<id>/`.

- `walk.json` keeps the script, the answers, and a hash of the link token.
  The token reads only its walk and stores only its answers.
- Each answer keeps a PNG image of the window of the step, for example
  `s11-well.png`, 16 MiB or less.
- One image for each question; a new image replaces the earlier one. The hub
  keeps the text of the last 5 earlier answers.
- All images 64 MiB or less. After this, the hub keeps the answer without the
  image and shows `walk_shot_budget`. One answer 24 MiB or less (else 413).
- An unknown link gets 404 and counts as a wrong try. Too many wrong tries
  from one address in one minute get 429.
