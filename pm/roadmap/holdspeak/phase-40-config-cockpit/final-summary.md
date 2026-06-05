# Phase 40 — Final Summary

- **Phase opened:** 2026-06-05
- **Phase closed:** 2026-06-05
- **Chunks shipped:** 6 (HS-40-01 … HS-40-06)

## Goal — was it met?

Original goal:

> Make the whole dictation copilot **configurable, observable, and memorable from
> the Web UI**. (1) No file editing — every dictation/pipeline knob (incl. the
> Phase-39 ones) is set from a rich, Signal-styled, readiness-driven cockpit.
> (2) Memory survives restarts — correction memory becomes DB-backed and gets a
> UI to view/curate it; depth telemetry is rendered richly. A UX + persistence
> phase that does **not** change pipeline behavior (the Phase-39 invariant holds:
> off by default; byte-identical when disabled).

**Yes — proven by a real dogfood.** Configured the copilot **entirely in the web
UI** (pipeline on · 3 rewrite passes · corrections on · infer-target on),
recorded a correction in the Memory tab, **restarted** (a fresh server over the
same config file + DB), and confirmed **both the config and the correction
persisted** — the Memory tab shows the card after the restart, telemetry
correctly reset (it's session-scoped by design). Capture:
[`evidence/dogfood_post_restart.png`](./evidence/dogfood_post_restart.png) +
the transcript in [evidence-story-06](./evidence-story-06.md).

- **Settings-API knobs** — [evidence-01](./evidence-story-01.md)
- **Persistent correction memory** — [evidence-02](./evidence-story-02.md)
- **The Copilot Setup cockpit (UI)** — [evidence-03](./evidence-story-03.md)
- **Memory + telemetry UI** — [evidence-04](./evidence-story-04.md)
- **Documentation** — [evidence-05](./evidence-story-05.md)
- **Closeout (this)** — [evidence-06](./evidence-story-06.md)

## Exit criteria — final state

- [x] The four Phase-39 knobs round-trip through `GET`/`PUT /api/settings` with
      validation (out-of-range rejected); integration-tested — HS-40-01. *(They
      already round-tripped via the merge + dataclass construction; the story
      closed the real gaps: clean type errors + 12 tests.)*
- [x] Correction memory persists across a process restart (DB-backed); a fresh
      `CorrectionStore` loads recent corrections; the canonical schema snapshot
      regenerated + proven; no behavior change when corrections are off — HS-40-02.
- [x] A Signal cockpit sets every dictation/pipeline knob from the UI (no JSON
      editing), readiness-driven, with inline validation; bundle rebuilt;
      screenshot — HS-40-03 (+ a pre-existing blank-tab bug fixed).
- [x] A UI panel lists/curates persistent corrections (add/remove/clear/toggle)
      and renders the depth telemetry (p50/p95 + guidance); screenshot — HS-40-04.
- [x] The user guides lead with web-UI setup; no live doc says you must edit
      JSON/YAML by hand; doc-guards + link-check green — HS-40-05.
- [x] Closeout: dogfood + demo + `final-summary.md`; README → done; PR — HS-40-06.
- [x] Full suite green throughout; pipeline behavior unchanged (off-by-default
      invariant holds); the bundle is rebuilt but only `web/src` committed.

## What shipped (by story)

| Story | Outcome |
|---|---|
| HS-40-01 | `PUT /api/settings` gives the four depth knobs clean type-error coercion (the round-trip + 4xx already worked via the merge + `DictationPipelineConfig.__post_init__`); +12 round-trip/rejection tests. |
| HS-40-02 | `dictation_corrections` table + `DictationCorrectionRepository`; schema snapshot regenerated; `CorrectionStore` loads-on-construct + writes-through; wired in the **live `WebRuntime`** (test-safe), bare servers in-memory + byte-identical. |
| HS-40-03 | The Signal **Copilot depth** cockpit — segmented rewrite-passes, toggle switches, reveal-on-toggle threshold, wired to `/api/settings` with inline validation + "Save & test in dry-run". **Fixed a pre-existing `activateSection` bug** that left every non-default `/dictation` tab blank. |
| HS-40-04 | The **Memory** tab — curation (deletable correction cards + add + Forget-all + in-context toggle; new `DELETE` routes) and a depth-telemetry panel (per-stage p50/p95 bars + guidance + multi-pass chips). Route-table lock 28→30. |
| HS-40-05 | Both guides lead with the web cockpit (`config.json` demoted to "Advanced"); persistent memory + the memory/telemetry UI documented with screenshots; the stale "never persisted" claim fixed. |
| HS-40-06 | UI-only dogfood across a restart (config + correction persisted); invariant re-verified; this summary; PR. |

## Metrics

- **Tests:** 2186/16 at phase open → **2221 passed, 16 skipped** at close
  (+35: HS-40-01 +12, HS-40-02 +12, HS-40-03 +1, HS-40-04 +10; HS-40-05 docs-only).
- **Routing invariant:** off-by-default byte-identical — `test_intent_dispatch`
  / `test_intent_router` + the no-repo `CorrectionStore` path green (25).
- **Schema:** `SCHEMA_VERSION` 1 (one new table + index); canonical snapshot
  regenerated + proven by `test_fresh_schema_matches_canonical_snapshot`.
- **Bundle:** rebuilt every UI story; **0** `holdspeak/static/_built/` files tracked.

## Lessons

- **Re-verify the brief against the codebase.** HS-40-01's premise ("`_coerce`
  drops the knobs") was stale — they already round-tripped. The brief's own rule
  ("codebase wins") paid off; the story became hardening + tests, not a new path.
- **The cockpit was invisible.** A latent `activateSection` bug meant every
  non-default `/dictation` tab rendered blank (the `hidden` attribute was never
  cleared). Found only by actually screenshotting the page — a reminder that a
  green test suite doesn't prove the UI renders. Fixed in HS-40-03; it unblocked
  runtime/readiness/KB/hooks/dry-run too.
- **Inject persistence where the DB is reachable test-safely.** Wiring the repo
  in `MeetingWebServer.__init__` via the `get_database()` singleton would have
  dragged every server-constructing test onto the real user DB. Injecting it in
  the live `WebRuntime` (optional repo on the store) kept bare servers
  byte-identical and the tests hermetic.

## Handoff — Phase 41 candidates (surface, not decide)

- **Release & Dogfood / Growth** — the long-deferred directions (first-run UX,
  packaging, onboarding).
- **Telemetry persistence** — depth telemetry still resets on restart (labelled
  "this session"); persisting it is the natural next durability step.
- **Consolidation UI** — the Phase-39 `consolidate_suggestions` helper is tested
  but unwired; a UI to merge near-duplicate project-doc suggestions.
- **Cross-device memory sync** — corrections persist locally (SQLite only);
  multi-device sync was explicitly out of Phase 40.
- **Correction memory in the live nudge** — the persistent set now hydrates the
  ring on boot; a "promote a manually-added correction into routing immediately"
  affordance could close the loop tighter.
