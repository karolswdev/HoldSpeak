# Evidence — HS-52-05: The Voice Commands board (the centerpiece)

Write-once record of the surface the feature lives or dies on. Built UI-first to
`design-voice-commands-board.md`, screenshot-verified.

## What shipped

- **`web/src/pages/commands.astro`** — a dedicated `/commands` board (its own route,
  not a settings section), Signal dark identity, built on the existing component
  system + tokens.
- **`web/src/scripts/commands-app.js`** — vanilla JS behaviour (matching the
  dictation-app list-editor pattern): loads `/api/settings`, renders the card grid with
  `createElement` (never `innerHTML` for user values), and the adaptive editor; persists
  via `PUT /api/settings` (just the `dictation.macros` section, which the merge preserves).
- **Route + nav**: `web/routes/pages.py` serves the built board at `/commands`;
  `TopNav`/`AppLayout` gained a `commands` route and a "Commands" entry under the
  "Configure" group.
- **`POST /api/commands/test`** (`web/routes/system.py`) — the Test affordance. Egress
  kinds (`open_url`/`launch_app`/`shell`) fire on the host through the same bounded
  connector the dispatcher uses (the browser cannot open a terminal); `type_text` returns
  a preview (it types into the focused app, nothing to run here). A failed command is
  reported inline, not as a 5xx.

## The affordances that make it a tool, not a list (per the design)

- **A card per command** with a per-kind left color edge and badge (open_url=cyan,
  launch_app=orange, shell=amber, type_text=green), the keyword as a mono chip.
- **A live preview line on every card** ("launches Terminal", "runs: git push origin
  HEAD") — the exact string `VoiceMacroAction.preview()` produces, kept in lockstep in JS.
  What you see is what fires.
- **The shell danger treatment**: the command in a danger-tinted mono box + a "⚠ runs
  code" badge on the card; in the editor, a red-framed command box + the line "Runs this
  on your machine when you say the keyword. No confirmation." Honest, never naggy.
- **A per-card Test button** + an editor Test, firing through `/api/commands/test`.
- **A per-kind adaptive editor**: the payload field morphs by kind (URL input / app input
  / mono command box / snippet textarea); a normalized match hint ("matches: terminal");
  a keyword-conflict warning; Save disabled until valid.
- **An inviting empty state** with one-tap starters that pre-fill the editor.
- **A master switch** (off by default), and the grid notes "off" state.

## Screenshot evidence

Captured by `scripts/screenshot_voice_commands.py` (boots a real server over a temp
config seeded with all four macro kinds, no mic/LLM, no real command fired), committed
to `screenshots/`:
- `board-populated.png` — the grid with all four kinds + the add-card; the shell card's
  danger box and "⚠ runs code" badge.
- `board-empty.png` — the empty state with starters.
- `editor-open-url.png` — the adaptive editor (URL field).
- `editor-shell-danger.png` — the shell command box (red-framed) + the danger note + the
  live `runs: git status` preview.

The new `/commands` route is also picked up by the `screenshots.yml` route-screenshot CI
on this web-touching PR.

## A bug caught by screenshot-verifying (not just "it built")

The first capture showed the editor + every payload field visible on load: my author
`display: grid/flex` rules overrode the UA `[hidden] { display: none }`. Fixed with
explicit `.vc-editor-overlay[hidden] / .vc-field[hidden] / .vc-preview-line[hidden]`
rules. This is exactly why the standing rule is "a class in the bundle != it applies;
screenshot-verify."

## Tests

```
cd web && npm run build              -> clean; /commands/index.html generated
uv run pytest -q tests/integration/test_web_commands_board.py
-> 4 passed   (the /commands route serves the board; the Test endpoint previews
   type_text, rejects an unknown kind (400), rejects an empty payload (400))

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2499 passed, 17 skipped   (was 2495; +4 is the new board tests, no regressions)
```

0 `holdspeak/static/_built/` tracked (source committed, bundle gitignored).

## Not done here (by design)

- The user guide is HS-52-06; the closeout dogfood + PR is HS-52-07.
