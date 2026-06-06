# Evidence — HS-42-03 — Welcome / Setup route + CLI nudge

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

The first real first-run surface — a Signal-styled `/setup` welcome route driven
entirely by `GET /api/setup/status`, a `/` guard that sends a first-run/blocked
user there (and never nags a healthy one), and a CLI launch nudge.

### The `/setup` page — `web/src/pages/setup.astro` + `setup-app.js`

- **Hero:** the HoldSpeak brand mark (PixelLab — `web/public/holdspeak-mark.png`),
  a "Welcome to HoldSpeak" eyebrow, a **dynamic headline** ("Everything's ready"
  / "N things need attention" / "Almost there — N optional items"), a subhead,
  a **progress bar** ("20 / 22 ready"), and a "Local · 127.0.0.1" chip.
- **One primary action:** a bright accent card with the single highest-severity
  next step from the contract (`primary_action`), e.g. "Set a valid local model
  path…", linking to its `route`.
- **Needs attention:** fail/warn rows (status glyph + label + detail + the fix),
  each anchored by section id so `primary_action.route` (`/setup#<id>`) lands.
- **First dictation CTA** (`#first-dictation`) — primed (green) when ready;
  HS-42-04 turns "Open dictation" into the guided real-app flow.
- **Ready grid:** every passing check as a compact green-ticked chip — so the
  user sees completeness (all 22 doctor checks surface: 20 ready + 2 attention).
- **Privacy + Presence summary cards** (a teaser for HS-42-05 / HS-42-07).

Restrained PixelLab treatment: **one** brand visual + small status glyphs only.

### The `/` first-run guard — `web/src/pages/index.astro`

An early, best-effort inline script fetches `/api/setup/status` and
`location.replace("/setup")` **only** when `first_run` or `overall === "blocked"`.
A mere WARN does **not** redirect — a healthy returning user stays on the
dashboard (the "never nag" invariant). A status failure never blocks the dashboard.

### The CLI nudge — `holdspeak/web_runtime.py`

`WebRuntime._print_setup_nudge()` (cheap `skip_network` read, fully defensive)
prints, on launch, for a first-run/blocked user:

```
  → First-run setup: open http://127.0.0.1:PORT/setup — 2 things need attention
    Next: Set a valid local model path (currently '~/Models/gguf/…').
```

Silent for a healthy returning user. The stale "History and settings … /history"
launch line was corrected to `Settings: …/settings · History: …/history`.

### The server route — `holdspeak/web/routes/pages.py`

`GET /setup` serves the built `_built/setup/index.html` with a graceful
not-built fallback.

## Verification (live, Playwright + stdout capture)

```
first-run  / -> /setup                     # redirected
returning  / -> /                          # stayed (milestone set; no nag)
CLI nudge:
  → First-run setup: open http://127.0.0.1:PORT/setup — 2 things need attention
    Next: Set a valid local model path (currently '~/Models/gguf/…').
ALL SETUP-FLOW CHECKS PASSED
```

Screenshot: [`evidence/setup_page.png`](./evidence/setup_page.png) — the hero +
progress, the orange primary-action card, the "Needs attention" rows, the
first-dictation CTA, the "Ready (20)" grid, and the Privacy/Presence cards.

## Tests run

```
uv run pytest -q tests/integration/test_web_setup_route.py
→ 5 passed
```

- `test_setup_route_serves_the_setup_page` — `GET /setup` 200, build-agnostic.
- `test_dashboard_has_the_first_run_guard` — `/` carries the
  `/api/setup/status` → `/setup` redirect guard.
- `test_cli_nudge_points_first_run_user_at_setup` /
  `test_cli_nudge_is_silent_for_a_healthy_returning_user` /
  `test_cli_nudge_never_raises` — the launch nudge.

Full suite: see the HS-42-03 commit message.

## Acceptance criteria

- [x] `/setup` renders the checklist from `/api/setup/status`; `/` shows
      setup-mode only for a first-run/blocked user (a healthy user is **not**
      nagged) — proven live for both states.
- [x] Exactly one primary action per state; each section shows status + fix; the
      `primary_action.route` anchors resolve.
- [x] The CLI prints the setup URL + readiness summary on launch (same status
      source); covered by tests.
- [x] One restrained PixelLab visual; no field wall / no raw doctor dump.
- [x] Bundle rebuilt; only `web/src` (+ `web/public/holdspeak-mark.png`)
      committed; desktop screenshot captured.
- [x] Default suite green; the healthy path is the unchanged dashboard.
