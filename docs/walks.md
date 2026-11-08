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
5. To add words, press **Say more**. Type or speak.
6. To go to the next step without an answer, press **Skip** or Esc.
7. At the end, press **Back to the desk**. The windows that the walk opened
   stay open.

You can use the part that has the ring. For example, you can press
**New program** when the walk tells you to.

The card shows the step number, for example `3 of 7`. On a phone, the card is
at the bottom of the screen.

If the link does not open, the Desk shows one line and then operates as usual.

## Make a walk

A walk is a JSON file. Each step has one or more of these keys:

| Key | What it does |
| --- | --- |
| `open` | Opens an application window: `{"app": "surface-programs"}`. `app` is an application key or window id, or a Chair window such as `chair:needs`. `scope` is optional. `@first-project` and `@first-meeting` mean your first project or meeting. If there is none, the walk skips the step. |
| `verb` | Runs one Desk verb: `{"verb": "desk.refresh"}`. |
| `highlight` | Marks one part: `{"target": "programs-new", "words": "..."}`. A plain name is a `data-testid`. Other text is a CSS selector. The walk looks in the newest window of the application first. |
| `ask` | Asks one question: `{"ref": "s11-well", "question": "...", "choices": ["Keep", "Redo"]}`. |

Example: `docs/walks/2026-11-07-wave-two.json`.

To make a walk and get its two links (Tailscale first, then this computer):

    uv run python scripts/walk.py new docs/walks/2026-11-07-wave-two.json

To read the answers:

    uv run python scripts/walk.py read <id>

## What the hub keeps

Each walk is one folder: `~/.local/share/holdspeak/feedback/walks/<id>/`.

- `walk.json` keeps the script, the answers, and a hash of the link token.
- Each answer keeps a PNG image of the window, for example `s11-well.png`.
  The size limits are the same as for Desk feedback: 16 MiB for one image.

The link token reads only its walk and stores only its answers. It does not
sign you in.

The hub keeps these limits for one walk:

- One image for each question. A new image for a question replaces the
  earlier image.
- A new answer to a question keeps the text of the earlier answers: the
  choice, the words and the time. The hub keeps the last 5 earlier answers.
- All the images of one walk are 64 MiB or less. After this limit, the hub
  does not keep a new image, but it keeps the answer. The answer shows
  `walk_shot_budget`.
- One answer is 24 MiB or less. The hub refuses a larger answer with 413 and
  does not read it.
- The hub reads the answer only after it finds the walk. An unknown link gets
  404 and counts as a wrong try. Too many wrong tries from one address in one
  minute get 429.
