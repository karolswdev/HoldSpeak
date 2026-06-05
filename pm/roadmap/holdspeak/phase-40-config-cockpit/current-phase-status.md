# Phase 40 — Configuration Cockpit & Persistent Memory

**Status:** CLOSED ✅ (6/6 stories). Opened + closed 2026-06-05. Direction chosen
by the user: a **web-first** way to set up the whole copilot ("nobody wants to
frig around with files and settings") + **persistent cross-session memory**.

**Last updated:** 2026-06-05 (**HS-40-06 — Phase CLOSED (6/6)** — UI-only dogfood
proved config + a correction survive a restart; `final-summary.md` written;
invariant re-verified; suite 2221/16. Branch
`phase-40/hs-40-01-settings-api-knobs` — push + open a PR to `main`.).

## Goal

Phase 39 made the dictation copilot deep and self-improving — but every knob
still lives in hand-edited JSON/YAML, and what it learns dies on restart.
Phase 40 makes the whole thing **configurable, observable, and memorable from
the Web UI**:

1. **No more file editing.** Every dictation/copilot setting — including the
   Phase-39 knobs (`rewrite_passes`, `corrections_enabled`,
   `target_detect_llm_enabled` / `_below`) — is set from a Signal-styled,
   readiness-driven cockpit. Toggles and sliders, inline validation, sensible
   defaults. A new user never opens `config.json` or `blocks.yaml`.
2. **Memory that survives restarts.** The dictation correction memory becomes
   **persistent** (DB-backed) and gets a UI to view and curate what it has
   learned. Depth telemetry (p50/p95 + budget guidance) is rendered richly.

This is a UX + persistence phase. It does **not** change the dictation pipeline
behavior (the Phase-39 invariant holds: off by default, byte-identical when
disabled). It surfaces and persists what already exists.

**The UI bar is high** (memory `feedback_high_ui_standards` +
`project_phase30_ui_overhaul`): rich **Signal** design, the `ui-ux-pro-max`
skill, affordances, no flat/basic controls. The web bundle is **gitignored**
(memory `reference_web_bundle_gitignored`): edit `web/src`, `cd web && npm run
build` to verify, commit source only.

## Scope

### In

- **Settings API: the missing knobs (HS-40-01).** Expose the four Phase-39
  pipeline knobs in `/api/settings` GET/PUT with validation + round-trip
  persistence. Backend foundation for the cockpit UI.
- **Persistent correction memory (HS-40-02).** A `dictation_corrections` table
  + `DictationCorrectionRepository` in the `db/` package; the `CorrectionStore`
  loads recent corrections on start and persists on record (the in-memory ring
  is kept for nudge-speed). Cross-session history surfaced on the API.
- **The Copilot Setup cockpit — UI (HS-40-03).** A Signal-styled,
  readiness-driven configuration surface in the web UI for the runtime +
  pipeline + the new knobs (toggles/sliders, inline validation), wired to
  `/api/settings`. No file editing.
- **Memory + telemetry UI (HS-40-04).** A panel to view/curate the (now
  persistent) corrections and enable/disable the feature, plus a rich
  depth-telemetry panel (per-stage p50/p95 + budget guidance from the readiness
  `depth` block).
- **Documentation (HS-40-05).** Dedicated docs story: update the user-facing
  guides to lead with the web-UI setup ("do it all in the UI"); screenshots;
  doc-guards green.
- **Closeout (HS-40-06).** Real dogfood of the cockpit + persistence; demo
  capture; `final-summary.md`; README → done; PR to `main`.

### Out

- **Rebuilding the existing blocks / project-KB editors** — they already work
  (`/api/dictation/blocks`, `/api/dictation/project-kb` + the dictation page).
  Link them into the cockpit; don't rebuild them.
- **Non-dictation settings surfaces** — hotkey / meeting / model already have
  web surfaces; this phase is the dictation/copilot cockpit.
- **Changing the dictation pipeline behavior** — Phase 40 surfaces + persists;
  it doesn't re-tune routing/rewriting. The Phase-39 invariant is unchanged.
- **Cloud sync of memory / multi-device** — persistence is local SQLite only.
- **Persisting telemetry across restarts** — in-memory is fine for the depth
  panel; only *corrections* persist this phase (telemetry persistence is a
  later candidate).

## Exit criteria (evidence required)

- [ ] The four Phase-39 knobs round-trip through `GET`/`PUT /api/settings` with
      validation (out-of-range rejected); integration-tested. (HS-40-01)
- [ ] Correction memory persists across a process restart (DB-backed); a fresh
      `CorrectionStore` loads recent corrections; the canonical schema snapshot
      is regenerated + proven; no behavior change when corrections are off.
      (HS-40-02)
- [ ] A Signal-styled cockpit sets every dictation/pipeline knob from the UI
      (no JSON editing), readiness-driven, with inline validation; bundle
      rebuilt; screenshot captured. (HS-40-03)
- [ ] A UI panel lists/curates persistent corrections (add/remove/toggle) and
      renders the depth telemetry (p50/p95 + guidance); screenshot. (HS-40-04)
- [ ] The user guides lead with web-UI setup; no live doc says you must edit
      JSON/YAML by hand; doc-guards + link-check green. (HS-40-05)
- [ ] Closeout: dogfood + demo + `final-summary.md`; README → done; PR merged.
      (HS-40-06)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout;
      the dictation pipeline behavior is unchanged (off-by-default invariant
      holds); the web bundle is rebuilt but only `web/src` is committed. (all)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-40-01 | Settings API: the missing knobs | done | [story-01-settings-api-knobs.md](./story-01-settings-api-knobs.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-40-02 | Persistent correction memory | done | [story-02-persistent-correction-memory.md](./story-02-persistent-correction-memory.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-40-03 | Copilot Setup cockpit (UI) | done | [story-03-copilot-setup-cockpit.md](./story-03-copilot-setup-cockpit.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-40-04 | Memory + telemetry UI | done | [story-04-memory-telemetry-ui.md](./story-04-memory-telemetry-ui.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-40-05 | Documentation | done | [story-05-documentation.md](./story-05-documentation.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-40-06 | Closeout | done | [story-06-closeout.md](./story-06-closeout.md) | [evidence-story-06.md](./evidence-story-06.md) |

## Where we are

**Phase CLOSED ✅ (6/6, 2026-06-05).** Opened right after Phase 39 merged (PR
#16) and closed the same day. The whole dictation copilot is now configurable +
curatable from the Web UI; a UI-only dogfood proved config + a correction
survive a restart. See [`final-summary.md`](./final-summary.md). Branch
`phase-40/hs-40-01-settings-api-knobs` — push + open a PR to `main`. Headlines:

- **Settings (HS-40-01) — done.** Re-verifying the seam showed the brief was
  stale: the four Phase-39 knobs **already** round-tripped + 4xx'd. `PUT
  /api/settings` builds `merged = deepcopy(current.to_dict())` then deep-merges
  the payload, so `pipeline_data` carries every field; the knobs flow through
  `DictationPipelineConfig(**pipeline_data)` and `__post_init__` enforces the
  1–5 / 0–1 bounds (`DictationConfigError` → 400). `_coerce` is only on the
  `load()` path, not PUT. Real gaps closed: clean type-error messages for
  non-numeric payloads (explicit `int()`/`float()` coercion mirroring the
  `max_total_latency_ms` block) + the missing test coverage (12 tests in
  `test_web_dictation_settings_api.py`). Suite 2198/16.
- **Persistence (HS-40-02) — done.** Added the `dictation_corrections` table +
  `idx_dictation_corrections_recent` to `SCHEMA_SQL` and a
  `DictationCorrectionRepository` (`db/corrections.py`, mirroring
  `db/actuators.py`) registered as `db.dictation_corrections`; **regenerated the
  canonical schema snapshot**. `CorrectionStore` gained optional persistence
  (`repository=…`): load-recent-on-construct + write-through-on-record, the
  in-memory ring still the nudge path. The repo is wired by the **live
  `WebRuntime`** (not `MeetingWebServer.__init__` — that uses the
  `get_database()` singleton and would force every server test onto the real
  DB); bare servers stay in-memory + byte-identical. Suite 2210/16.
- **Cockpit UI (HS-40-03) — done.** A Signal **Copilot depth** group on the
  `/dictation` runtime tab: a segmented rewrite-passes control (1–5, live badge +
  descriptor), real toggle switches for `corrections_enabled` +
  `target_detect_llm_enabled`, and a reveal-on-toggle `target_detect_llm_below`
  slider — wired to `/api/settings` with inline validation, a live depth summary
  in the meta banner, and a "Save & test in dry-run" jump. **Also fixed a
  pre-existing `activateSection` bug** that left every non-default tab
  (runtime/readiness/KB/hooks/dry-run) blank (the `hidden` attr was never
  cleared). Full UI round-trip + on-disk persistence verified via Playwright;
  screenshots in `evidence/`. Bundle rebuilt; only `web/src` committed.
- **Memory + telemetry UI (HS-40-04) — done.** A new **Memory** tab: a
  curation panel (deletable correction cards + add form + Forget-all + an
  in-context `corrections_enabled` toggle) and a depth-telemetry panel (per-stage
  p50/p95 bars + budget guidance + multi-pass chips + stat tiles). Added the
  missing `DELETE /api/dictation/corrections/{id}` + `DELETE
  /api/dictation/corrections` routes (route-table lock updated 28→30) and
  `CorrectionStore.list_for_display`/`remove`/durable-`clear`; GET now carries
  the durable `id`+`created_at`. Playwright-verified; screenshot in `evidence/`.

**Pickup order:** HS-40-01 (backend foundation, unblocks the UI) ✅ → HS-40-02
(persistence, independent, enables the memory UI) ✅ → HS-40-03 (cockpit UI, needs
01) ✅ → HS-40-04 (memory/telemetry UI, needs 02) ✅ → HS-40-05 (docs) ✅ → HS-40-06
(closeout) ✅. 01 and 02 are independent and can go in either order / in parallel
worktrees. **All six stories done — phase CLOSED.**

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Schema change breaks the canonical-snapshot test | High if forgotten | HS-40-02 must regenerate + commit the schema snapshot and prove a fresh build matches | The snapshot test fails / drifts |
| UI ships flat/basic and misses the Signal bar | Medium | Use the `ui-ux-pro-max` skill + Signal tokens; rich affordances; screenshot review | A reviewer calls the UI flat/basic |
| The committed web bundle leaks into a commit | Medium | `holdspeak/static/_built/` is gitignored; only `web/src` is committed; `git status` checked before commit | `_built/` files show up staged |
| Persistence changes default behavior | Medium | Corrections stay off-by-default; persistence is additive; the in-memory ring path is byte-identical when the feature is off | Routing changes with corrections disabled |
| Settings PUT drops/loses a field on round-trip | Medium | Round-trip integration test asserts every knob persists + reloads | A knob doesn't survive PUT→GET |

## Decisions made (this phase)

- 2026-06-05 — **Direction = Configuration Cockpit & Persistent Memory** — user
  pick (web-first config + persistence) as Phase 40 after Phase 39 closed.
- 2026-06-05 — **Persist *corrections* only this phase** (telemetry stays
  in-memory) — corrections are the durable, user-meaningful state; telemetry is
  ephemeral diagnostics.
- 2026-06-05 — **Keep the in-memory ring + DB-back it** (not DB-only) — the ring
  stays the fast nudge path; the DB is durability + history. Avoids a per-utterance
  DB read on the live typing path.

## Decisions deferred

- **DB-backed vs file-backed persistence for corrections** — trigger: HS-40-02 —
  default: the existing SQLite `db/` package (consistent with every other domain).
- **Whether the cockpit is a new page vs an expanded `/dictation` section** —
  trigger: HS-40-03 — default: expand the existing `/dictation` page (it already
  has the readiness/runtime/blocks/KB sections) rather than a new route.
- **Telemetry persistence** — trigger: real dogfood (HS-40-06) shows in-memory is
  too forgetful — default: stays in-memory.
