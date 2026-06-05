# Phase 40 — Agent Brief (read this first)

You are picking up **Phase 40 — Configuration Cockpit & Persistent Memory** for
HoldSpeak. This brief is self-contained: it has the mission, the exact code
seams (already mapped), the rules of the road, and a per-story definition of
success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story file you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line/number below.

---

## 0. Mission

Make the whole dictation copilot **configurable, observable, and memorable from
the Web UI**. The user's words: *"Nobody wants to frig around with files and
settings like this."* Two outcomes:

1. **No file editing.** Every dictation/pipeline knob (incl. the Phase-39 ones)
   is set from a rich, Signal-styled, readiness-driven cockpit.
2. **Memory survives restarts.** Correction memory becomes DB-backed and gets a
   UI to view/curate it; depth telemetry is rendered richly.

It's a **UX + persistence** phase. It does **not** change pipeline behavior —
the Phase-39 invariant holds (off by default; byte-identical when disabled).

---

## 1. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template
  in `pm/roadmap/PMO-CONTRACT.md` §"Contract template"); the pre-commit hook
  validates + deletes it. A story flipping to `done` **must** ship its
  `evidence-story-{n}.md` in the same commit, or the hook rejects you (this bit
  me twice in Phase 39 — don't edit a *shipped* story's evidence; new work = new
  story).
- **One PR per story**, accumulating on the phase branch
  `phase-40/hs-40-01-settings-api-knobs`. Open the PR at phase close and merge
  with a merge commit when CI is green (memory `feedback_merge_phases_via_pr`).
- **Tests actually run.** Flip a story to `done` only after running the relevant
  tests via `uv run pytest -q ...` and reading the output. Type-check is not
  validation (PMO §3).
- **Operating cadence (same commit):** story header status → current-phase-status
  story row + "Where we are" → roadmap README "Last updated" → any canon doc the
  story touches.
- **No `Co-Authored-By`** in commits (project canon). End PR bodies with the
  Claude Code line.
- **Greenfield:** HoldSpeak isn't really released (memory
  `feedback_holdspeak_not_really_released`) — design freely, no backwards-compat
  ceremony.

## 2. The UI bar (HS-40-03 / 04 especially)

- **High standards.** Flat/basic components are rejected (memory
  `feedback_high_ui_standards`). Apply the **Signal** design system richly
  (memory `project_phase30_ui_overhaul`): real depth, motion, affordances,
  states, help text, overflow-safe, copy/preview affordances where useful.
- **Use the `ui-ux-pro-max` skill** (vendored at `.claude/skills/ui-ux-pro-max`)
  for the UI work. Reference the Phase-36 elevated-card patterns
  (`web/src/pages/history.astro`) for the look.
- **The web bundle is gitignored** (memory `reference_web_bundle_gitignored`).
  Edit `web/src/**`, run `cd web && npm run build` to verify, and **commit only
  `web/src` source** — never `holdspeak/static/_built/**`. Check `git status`
  before every commit.

## 3. Commands

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py     # full suite (skip the mic-hanging metal file)
uv run pytest -q tests/integration/test_web_dictation_settings_api.py   # settings round-trip
uv run pytest -q -k "doc_drift or dangling or no_live_doc or link"      # doc guards
cd web && npm run build                               # rebuild the Astro bundle (verify UI)
uv run ruff check <files>                             # lint touched files
```

Baseline at phase open: **2186 passed, 16 skipped** (Phase 39 close).

---

## 4. The territory (verified seams — re-check before editing)

### Settings API (HS-40-01)
- `holdspeak/web/routes/system.py` — `GET /api/settings` (~L442) returns
  `Config.to_dict()` (the four Phase-39 knobs are already in there as dataclass
  fields). `PUT /api/settings` (~L461) validates/coerces a fixed set of pipeline
  fields (see the `max_total_latency_ms` block) and **omits** `rewrite_passes`
  / `corrections_enabled` / `target_detect_llm_enabled` / `target_detect_llm_below`
  → `_coerce` (`config.py`) silently drops them.
- The knob definitions + bounds live on `DictationPipelineConfig`
  (`holdspeak/config.py`): passes `1..5`, threshold `0.0..1.0`,
  `DictationConfigError` on out-of-range. **Reuse those bounds** (construct +
  catch) rather than re-implementing.
- Tests: `tests/integration/test_web_dictation_settings_api.py`.

### Persistence (HS-40-02)
- `holdspeak/db/` is a `Database` container (`db/core.py`) + per-domain
  repositories on one canonical `SCHEMA_SQL`, `SCHEMA_VERSION = 1`.
- **Mirror `holdspeak/db/actuators.py`** for the new
  `DictationCorrectionRepository` (`__init__(connection, container)`, `with
  self._connection() as conn:`, dataclass records, `_json_*` helpers). Register
  on the container in `db/core.py`; export in `db/__init__.py`.
- **THE TRAP:** adding a table requires **regenerating the committed canonical
  schema snapshot** — there is a snapshot test that builds a fresh DB and
  compares `sqlite_master`. Grep the db tests for how the snapshot is generated
  and regenerate it; otherwise the suite goes red.
- The store to wrap: `holdspeak/plugins/dictation/corrections.py` `CorrectionStore`
  (bounded ring; gist-only + secret-rejected). It's owned by `MeetingWebServer`
  (`server.dictation_corrections`) which has access to the `Database` — inject
  the repo there; leave the dry-run/test stores repo-less (in-memory, unchanged).

### Cockpit + panels (HS-40-03 / 04)
- Frontend: `web/src/pages/dictation.astro` (sections: readiness / runtime /
  blocks / KB / project-context / agent-hooks / dry-run) +
  `web/src/scripts/dictation-app.js` (~65KB vanilla JS). Built to the gitignored
  `holdspeak/static/_built/`.
- Data already on the API: `GET/PUT /api/settings`,
  `GET/POST /api/dictation/corrections`, and the readiness `depth` block
  (`GET /api/dictation/readiness` → `depth.stages` p50/p95, `depth.guidance`,
  `depth.rewrite_pass_ms`, `depth.corrections`).
- Blocks + KB editors already exist (`/api/dictation/blocks`,
  `/api/dictation/project-kb` + their page sections) — **embed/link, don't
  rebuild**.
- A **delete/clear** corrections route probably needs adding for HS-40-04 (the
  API is GET/POST today) — keep it consistent with the persistence repo.

---

## 5. Pickup order & per-story "done"

1. **HS-40-01** (no deps) — knobs in `PUT /api/settings` + round-trip tests.
   *Done = the four knobs persist via PUT→GET; out-of-range rejected 4xx; suite green.*
2. **HS-40-02** (no deps; parallel-able with 01) — DB table + repository + store
   persistence + **schema snapshot regenerated**.
   *Done = corrections survive a simulated restart; no-repo store unchanged; snapshot test green.*
3. **HS-40-03** (needs 01) — the Signal cockpit UI for every knob; readiness-driven.
   *Done = full UI-only config round-trips; rich Signal; bundle rebuilt; no `_built/` staged; screenshot.*
4. **HS-40-04** (needs 01+02) — memory panel (curate persistent corrections) +
   depth-telemetry panel.
   *Done = list/add/remove corrections + render p50/p95+guidance; Signal; screenshots.*
5. **HS-40-05** (needs 01–04) — docs lead with the UI; screenshots; doc-guards green.
6. **HS-40-06** — closeout: dogfood (configure → correct → restart → persisted),
   `final-summary.md`, README → done, PR + merge.

01 and 02 are independent (split into parallel worktrees if you want). The UI
stories (03/04) are the bar-raising work — budget time for the `ui-ux-pro-max`
pass and a screenshot review.

---

## 6. Watch-outs

- **Schema snapshot** (HS-40-02) — regenerate + commit it, or the suite reddens.
- **`_built/` leak** — `git status` before every commit; only `web/src` source.
- **Off-by-default invariant** — corrections persistence is additive; with
  `corrections_enabled=false` routing must stay byte-identical. Keep a test.
- **Don't reset un-sent knobs** (HS-40-01) — a partial PUT must preserve fields
  the client didn't send.
- **Reuse the config bounds** — one source of truth for the 1–5 / 0–1 ranges.

Good luck. The status doc tracks the live picture; keep it honest.
