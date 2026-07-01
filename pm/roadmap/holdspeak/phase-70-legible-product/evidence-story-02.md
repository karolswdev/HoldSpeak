# Evidence — HS-70-02: Home — "what is this + your next action"

**Date:** 2026-06-30
**Verdict:** done. `/` is no longer the meeting-runtime dashboard; it is an
orientation **Home** that answers the two questions a confused user has in the
first ten seconds: *what is this* (the positioning one-liner) and *what do I do
now* (the two modes as co-equal cards + a single next-action).

## What shipped

- **`web/src/pages/index.astro`** — a new, focused Home:
  - **Identity:** eyebrow "Your local voice copilot" + `One copilot, two modes.`
    + the positioning lede (no em-dashes, per the voice rule).
  - **Next action:** an accent band fed by `GET /api/setup/status` — it shows the
    server's `primary_action` (label + route) while `first_run` or
    `overall !== "ready"`, and stays hidden once the user is set up. (In the
    shots: "Set a valid local model path (currently '…Qwen3.5-9B…')".)
  - **The two modes, co-equal:** Dictation and Meetings as `.signal-card`s with a
    white-on-gradient glyph chip, a one-line what-it-does, a dynamic subtitle,
    and action buttons (Dictation → `/dictation`; Meetings → `/live` to start +
    `/history` to browse).
  - **Quiet Studio:** a dashed, visually-secondary link to the advanced tier —
    never louder than the two modes.
  - Dynamic subtitles fill **pre-rendered elements' `textContent`** (no
    innerHTML-injected structural DOM), so the scoped CSS stays valid.
- **`web/src/pages/live.astro`** — the 1378-line live-meeting runtime dashboard
  moved off `/` (a `git mv` from `index.astro`; behaviour unchanged), now
  `current="meetings"`. It is Meetings-mode content; HS-70-05 unifies it with the
  archive.
- **`holdspeak/web/routes/pages.py`** — a `/live` route serving
  `_built/live/index.html` (the three-registration rule).
- **`tests/e2e/test_route_preflight.py`** — `/live` added to `PAGE_ROUTES`.

## The empty state (the "won't scare a new user" proof)

With a fresh DB, the mode subtitles are guiding, not blank: Dictation →
"Nothing yet. Hold your key and speak."; Meetings → "Nothing yet. Capture or
import your first meeting." (HS-70-07 formalizes this pattern app-wide.)

## The routing ripple (test retargets)

Moving the runtime dashboard off `/` moved its content-assertions with it. Ten
tests asserted dashboard content at `/` (or read `pages/index.astro`); each was
retargeted to `/live` / `live.astro` in lockstep (the dashboard did not change,
only its route):
- `test_web_server.py::TestDashboardEndpoint` (7 GETs `/` → `/live`).
- `test_web_dashboard_home.py` (idle-home cards / command-center: `index.astro`
  → `live.astro`).
- `test_history_slack_surfaces.py` (the Pending-actions Slack guard copy moved
  with the dashboard: `index.astro` → `live.astro`).
- `test_web_presence_indicator.py` (the runtime presence card: `index.astro` →
  `live.astro`).

Home gained the **first-run guard** the old dashboard carried
(`test_web_setup_route.py::test_dashboard_has_the_first_run_guard`): an inline
script fetches `/api/setup/status` and sends a first-run user to `/welcome`, a
hard-blocked user to `/setup` — everyone else stays on Home. (HS-70-03 owns the
wider first-run consolidation; Home is where the guard belongs.)

## Proof

- **`screenshots/home-empty.png`** — fresh DB: identity + the NEXT band + both
  mode cards with guiding empty subtitles + the quiet Studio link.
- **`screenshots/home-seeded.png`** — a seeded meeting + journal entry: the
  subtitles fill (`Last: "add a retry with backoff to the upload path"` /
  `Last: Q3 planning sync`); the mic + meeting glyphs render white on the
  gradient chip.
- **Tests:** `npm run build` green (17 pages, `/live` + `/` both built); route
  pre-flight **2 passed** (Home + `/live` swept, zero page errors); full suite
  **3045 passed, 37 skipped** (`--ignore=tests/e2e/test_metal.py`). The dashboard
  move is a `git mv` with no binding change, so no dashboard test needed editing.
