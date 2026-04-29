# HoldSpeak Designer Handoff

This directory packages the current HoldSpeak UI/UX layer for a graphic
designer and product designer. It describes what exists, what each screen
does, where the interaction boundaries are, and which screenshots represent
the current implementation.

## Product Frame

HoldSpeak is a local-first voice typing and meeting-workflow tool. The web
runtime is not a marketing site; it is an operational surface for people who
are recording, reviewing, routing, and exporting work context on their own
machine.

The design direction should stay quiet, dense, and trustworthy:

- Local/private status should be visible without becoming alarmist.
- Primary actions should be obvious and guarded when they can mutate data.
- Tool surfaces should prioritize scanning, repeated use, and recovery.
- Panels should feel utilitarian, not decorative.
- Empty states should say what useful action comes next.

## Contents

- [functional-handoff.md](./functional-handoff.md) - screen-by-screen behavior,
  workflows, and interaction states.
- [style-handoff.md](./style-handoff.md) - current visual language, constraints,
  and open style questions.
- [ux-inventory.md](./ux-inventory.md) - routes, components, controls, data
  states, and designer review checklist.
- [screenshot-index.md](./screenshot-index.md) - captured screenshots and what
  each one is meant to evaluate.
- [capture-screenshots.py](./capture-screenshots.py) - repeatable Playwright
  capture script.
- [screenshots/](./screenshots/) - Playwright screenshots of the current app.

## Current Capture Target

Screenshots were captured from the local web runtime:

```text
http://127.0.0.1:64524
```

The runtime is local-only. Screens may show empty data states depending on the
developer machine's local activity and meeting database.

## Refresh Screenshots

With the HoldSpeak web runtime running:

```bash
uv run --extra dev python designer-handoff/capture-screenshots.py --base-url http://127.0.0.1:64524
```

If Playwright browsers are missing:

```bash
uv run --extra dev python -m playwright install chromium
```
