# Walks

A walk is a short guided review of the Desk. It opens windows, marks one part
of a window, and asks one question about it. You answer with one press.

## Open a walk

1. Open the link that you got. Its path starts with `/w/`. The first link
   uses the hub's tailnet name over https (Tailscale Serve), not its IP
   address. The second link is for this computer.
2. The Desk opens. A ring marks one part of a window. A note beside it gives the step's words.
3. Read the question in the note. Press a choice, for example **Keep** or **Redo**.
4. To add words, press **Say more**. Type or speak, then press a choice or **Send**.
5. Press **Skip** to continue without an answer. Press Esc to stop the walk.

The note stays inside the window. On a phone, it docks above the window's status line.
**Help ▸ Speak the guide** turns the guide voice on or off on this device. The default is off.
At the end, the guide closes. The windows stay open.

## Make a walk

A walk is a JSON file. Each step has one or more of these keys. The walk does
them in this order: `open`, `verb`, `press`, `scroll`, `say`, `highlight`,
`ask`.

| Key | What it does |
| --- | --- |
| `open` | Opens an application window: `{"app": "surface-programs"}`. `app` is an application key or window id, or a Chair window such as `chair:needs`. `scope` is optional. `@first-project` and `@first-meeting` mean your first project or meeting. If there is none, the walk skips the step. |
| `verb` | Runs one Desk verb: `{"verb": "desk.refresh"}`. |
| `press` | Selects a kit list row, rail row or tab. Other controls are refused. |
| `scroll` | Names a part to bring into view in its window. |
| `say` | Shows the step's words in the note. |
| `highlight` | Marks one part: `{"target": "programs-new", "words": "..."}`. A plain name is a `data-testid`. Other text is a CSS selector. The walk looks only in the window of the step: `window`, else the last `open`. If that window is not open, the walk skips the step. |
| `thing` | In `press`, `scroll` or `highlight`: the name of the part, for example `"people rows"`. If the window has no such part, the guide skips that step. An empty app guide goes to the action that starts a new item. |
| `ask` | Asks one question: `{"ref": "s11-well", "question": "...", "choices": ["Keep", "Redo"]}`. |

`target` and `window` in `press` and `scroll` work as in `highlight`. An
`open` of a Project Room (`open-project-memory` with a project scope) shows
the Room, not the Update posture that the Room kept from an earlier visit.

Example: `docs/walks/2026-11-08-handheld.json`. To make a walk and get its
two links (the tailnet name over https first, then this computer; set
`HOLDSPEAK_TAILNET` to your hub's https tailnet address), and to read the answers:

    uv run python scripts/walk.py new docs/walks/2026-11-07-wave-two.json
    uv run python scripts/walk.py read <id>

## An app's own walk

Each app with a guide has **Show me <app>** in **Help**. At phone width, **?** opens Help beside Search.

1. Open **Help**, then press **Show me <app>**. You can also press **?** on a keyboard.
2. Read each step. The guide can select a list row or tab. It does not press actions that write or send.
3. Press **Next** or **Done**. **Stop**, Esc, or your own press in the window stops the guide.

The guide restores the selection and view it changed. It asks no question and makes no walk record.
An empty list skips to the action that starts a new item.

If feedback is enabled, **Say what is off** opens capture at the note. Type words, or press **Record** and **Stop**.
Press **Save** to keep the selected part, window image, guide step and your words in one feedback bundle.
**Cancel** returns to the same guide step. After Save, that step shows **Saved.**
**Help ▸ Give feedback** opens the same capture when no guide runs.

The app script is `web/src/desk/walks/<name>.walk.json`. Its three or four steps have no `ask`.
The top-level `review` key holds the question used only by `walk.py apps`.
The manifest's `walk` field names the script. `tests/unit/test_app_walks.py` checks its parts and safe presses.

To walk through all the apps from one link:

    uv run python scripts/walk.py apps

## What the hub keeps

Each link walk is one folder: `~/.local/share/holdspeak/feedback/walks/<id>/`.

- `walk.json` keeps the script, the answers, and a hash of the link token.
  The token reads only its walk and stores only its answers.
- Each answer keeps a PNG image of the full screen as you saw it, with
  the window guide note and ring, for example `s11-well.png`, 16 MiB or
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
