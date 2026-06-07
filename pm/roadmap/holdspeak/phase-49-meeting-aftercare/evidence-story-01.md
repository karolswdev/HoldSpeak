# Evidence — HS-49-01: The aftercare digest (open / decided / changed)

Write-once record of what shipped for the aftercare digest, the foundation the
rest of Phase 49 presents and feeds. The rules that matter: every count is real
and pulled from data that already exists, the diff compares real prior-meeting
data, and the surface stays quiet when there is nothing to act on. Read-only —
no new writes, no behavior change to capture / plugins / synthesis.

## What shipped

**Backend**
- `holdspeak/meeting_aftercare.py` — a pure `compute_meeting_aftercare(db, id)`
  over meetings + action items + the `decisions` artifact. No store of its own;
  no writes.
  - **What's open** — `list_action_items(include_completed=False, meeting_id=...)`
    (status `pending`), grouped by owner. Named owners sort A→Z, unassigned
    (blank owner folds to `None`) sinks to the bottom. Each item carries its
    `source_timestamp` so HS-49-02 can hang a transcript jump off it.
  - **What was decided** — the `decisions` artifact's `structured_json["decisions"]`
    (where `decision_capture` synthesis writes them; see
    `plugins/synthesis.py:_render_decisions`). Deduped by normalized decision
    text, first wins; blank-text entries dropped; a real `source_timestamp`
    surfaced only when present.
  - **Since last meeting** — the previous meeting is the one with the greatest
    `started_at` strictly before this meeting's (`id` tie-break, deterministic).
    The diff is computed against its real decisions + action items: `new_decisions`
    (current minus prior, by text), `new_actions` (current open tasks not present
    in prior by task text), `closed_actions` (prior items now `done`/`dismissed`).
    `changed` is the OR of the three. `None` when there is no prior meeting.
  - **Quiet contract** — top-level `is_empty` is true when nothing is open,
    nothing was decided, and nothing changed. The caller's cue to render nothing.
- `holdspeak/web/routes/meetings.py` — `GET /api/meetings/{id}/aftercare`. A pure
  DB read; 404 for an unknown meeting; returns the digest JSON including
  `is_empty`.

**UI** (`web/src/pages/history.astro` + `web/src/scripts/history-app.js`)
- A "Your next move" aftercare panel at the **top of the meeting-detail side
  column**, above the artifact dump — the lightest home that reads as action, no
  new nav, no second artifact list (page-density rule honored: the panel is its
  own card + CSS block, not piled onto an existing one).
- Three sections, each shown only when it has content: **Still open** (count
  badge + per-owner groups + due / source pills), **What was decided** (decision
  + rationale), **Since {prior meeting}** (NEW DECISION / NEW ACTION / CLOSED
  deltas, the closed delta in the success color).
- `openMeeting(id)` fetches `/api/meetings/{id}/aftercare` and only binds it when
  `is_empty` is false, so an empty meeting shows no panel at all.
- The panel is rendered from Alpine `x-for` templates in the `.astro` markup
  (cloned nodes keep their `data-astro-cid`), so the CSS lives in the page's
  scoped `<style>` block — confirmed applied by screenshot, not by class-presence.

## Tests (ran, read the output)

- `tests/unit/test_meeting_aftercare.py` — unknown-meeting → None; empty meeting
  is quiet; open-by-owner ordering (A→Z, unassigned last, done excluded);
  decisions with provenance + blank-text drop; the real since-last diff
  (new decision / new action / closed action); no-change stays quiet.
- `tests/integration/test_web_meeting_aftercare_api.py` — the route aggregates
  real seeded data; viewing performs **no** write (action-item rows byte-identical
  before/after); 404 for an unknown meeting.
- `uv run pytest -q tests/unit/test_meeting_aftercare.py tests/integration/test_web_meeting_aftercare_api.py`
  → **9 passed**.
- Story sweep `uv run pytest -q -k "meeting or aftercare or action_item or artifact or proposal" --ignore=tests/e2e/test_metal.py`
  → **477 passed, 12 skipped** (skips are pre-existing opt-in / missing-fixture e2e).

## Build + screenshot

- `(cd web && npm run build)` → 12 pages built, clean. `git ls-files
  holdspeak/static/_built` → empty (0 tracked; source-only commit).
- `scripts/screenshot_aftercare_digest.py` boots the real `MeetingWebServer`
  against a seeded temp DB and drives the meeting modal.
  `screenshots/story-01-aftercare-digest.png` shows the panel above the artifacts:
  "Your next move" + AFTERCARE tag, STILL OPEN (3) by owner with the `Source [2:08]`
  provenance pill, WHAT WAS DECIDED with rationale, and SINCE API DESIGN KICKOFF
  with NEW DECISION / NEW ACTION / CLOSED deltas. CSS applies on the
  Alpine-template DOM.

## Honesty / invariants held

- Read-only: the only new endpoint is a GET; no new write primitive; capture,
  plugins, and synthesis are untouched.
- Real data only: counts come from `list_action_items` and the `decisions`
  artifact; the diff compares the real chronologically-prior meeting; quiet at
  no-prior and no-change; no fabricated deltas.
- Provenance is surfaced only where a real `source_timestamp` exists (no fake
  0:00) — the thread HS-49-02 picks up.
