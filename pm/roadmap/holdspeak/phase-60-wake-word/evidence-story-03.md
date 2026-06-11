# Evidence — HS-60-03: The armed UX + settings

**Date:** 2026-06-11
**Branch:** `phase-60-wake-word`

## 1. What shipped

- **The armed state is first-class on the ambient surfaces**: a presence
  `_STATE_META` entry (amber, "Armed", an active-window state — never
  hidden) and the Qlippy dock mapping (`armed → listening` sprite). Any
  open HoldSpeak page with the socket sees the `armed` runtime activity.
- **The wake preview card** (`qlippy-events.js`): sticky, with the safety
  copy front and center ("Nothing has been typed. Local only… Your
  controls: Type it, or dismiss and nothing happens."), the transcript,
  the pipeline result in the mono preview, and **Type it** posting the
  one-shot token.
- **The one-shot Type-it route** (`POST /api/dictation/wake/type`): wired
  through a new `on_wake_type` callback (WebRuntimeCallbacks → server attr
  → WebContext) to the runtime's `_type_wake_preview`, which burns the
  token and types ONLY the server-stored preview — **client-supplied text
  is structurally ignored** (asserted: a payload smuggling
  `"text": "rm -rf injected"` types the stored preview). 503 with no
  runtime; 400 with no token; 404 once burned.
- **The settings section** (Voice → Wake word): the enable switch with the
  honest description (preview-never-typed default + **the egress note**:
  "First enable downloads the detection models once (about 7 MB) from the
  openWakeWord GitHub releases; after that everything runs locally"),
  model, action (the type option's hint says the quiet part: "a false
  detection would type into whatever app is focused"), threshold, window,
  and the Desktop-presence recommendation (the always-visible armed
  indicator).
- **First-enable self-healing**: `_start_wake_listener` now downloads the
  models once when the configured model is missing (the logged, documented
  egress moment), then retries — a small HS-60-02 amendment recorded here.

## 2. The indicator posture, recorded honestly

The unmissable-indicator condition is served by the surfaces built for
ambient state: presence/Qlippy (recommended in the settings copy) and any
open socket page. The dictation cockpit has no websocket today; rather
than adding a second socket consumer for a banner, the recommendation +
the broadcast-everywhere design carries the condition. Recorded as the
design decision; the closeout proves the armed state live.

## 3. Live screenshots (zero page errors)

- `story03-preview-card.png`: the "Armed" HUD card and the wake preview
  card together — Qlippy with the check glyph, "Heard you — review before
  it types", transcript → result, the safety copy, Type it.
- `story03-armed.png`: the armed state on the presence surface.
- `story03-settings.png`: the Voice section with the Wake word group.

## 4. Tests

`tests/integration/test_wake_ux.py` — 8 tests: the one-shot route
(types-once-burns, no-token 400, no-runtime 503, **never accepts client
text**), the armed presence state (STATE_META + the window view active),
the dock mapping lock, the preview-card safety-copy locks, the settings
honest-truth locks (egress note, the false-detection warning, the
presence recommendation).

```
$ uv run pytest -q tests/integration/test_wake_ux.py
8 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2723 passed, 17 skipped
```

(2715 → 2723.) Build clean; 0 `_built/` tracked.
