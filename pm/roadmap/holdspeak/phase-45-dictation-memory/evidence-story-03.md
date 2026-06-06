# Evidence — HS-45-03: The moment of truth (correct in flow, and it teaches)

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-45-dictation-memory`.

## What shipped

The moment a dictation lands wrong is when fixing is cheapest. This makes
correction an **in-the-moment, focus-safe gesture that teaches** — and records
the fix against the journal entry — instead of an after-the-fact detour to the
Memory tab.

### Endpoint — `POST /api/dictation/journal/{id}/correct`

`holdspeak/web/routes/dictation/pipeline.py`. Records a correction via the
Phase-40 `CorrectionStore` (write-through → future routing is nudged) **keyed on
the journal entry's own transcript**, then flips the entry's `corrected` flag and
links the correction id (`mark_corrected`). Reuses the existing engine — no new
memory/nudge built. Validates kind ∈ {intent, target}; 404 on a missing entry /
no journal; the teach is gist-only + secret-filtered by the store.

### The in-moment surface — the dry-run result panel

`web/src/pages/dictation.astro` + `web/src/scripts/dictation-app.js`. After a
dry-run journals a row, the result panel surfaces **"Was that right?"** with the
routed summary (block @ conf · target) and a **"Fix it →"** button → reveals a
small inline form (correct the *route* or the *target* → value) → **"Teach &
record"** → POSTs to the correct endpoint → a reduced-motion-safe **"Taught ✓"**
confirmation. The fix flow is identical for spoken + dry-run (the dry-run panel
is the guaranteed no-mic surface). Corrected entries already render a green ✓ in
the Journal (HS-45-02).

- **Focus-safe:** no `autofocus` anywhere; the dictation app script **never**
  calls `.focus()`; the form is revealed on click — the dictation flow / textarea
  keeps focus. (Same invariant as desktop presence.)
- **Provable with no mic:** the affordance shows whenever a journal entry exists
  (`journal_id` returned by the dry-run), independent of runtime — so an offline
  dry-run can be fixed-and-taught.

### Plumbing

`DictationJournalRecorder.record` now **returns the persisted record** (or None)
so the dry-run path can surface `journal_id` in its response for the fix to
attach to. The live path ignores the return; behavior unchanged.

### Pre-existing bug fixed (surfaced by the first browser dry-run)

`renderDryRun` referenced `telemetryHtml` but it was only ever `const`-declared
inside `renderHSMeta` — a **ReferenceError that left every browser dry-run result
blank** (swallowed by `runDryRun`'s try/catch; never caught because the dry-run
was only API-tested, never browser-tested). Defined it in scope from the run's
telemetry. The dry-run result panel now actually renders.

## Tests — `tests/integration/test_dictation_moment_of_truth.py` (7 tests)

- correct flips `corrected` + records a correction keyed on the entry transcript
  + links the correction id;
- **the teach nudges a similar future utterance** — a later phrase resolves to
  the corrected block via `best_match_in` (the intent-router's own nudge path);
- 404 on a missing entry; 400 on a bad kind;
- a **secret-like transcript marks corrected but does NOT teach** (gist dropped);
- the **dry-run returns a `journal_id`** that resolves to a real row;
- the in-moment affordance is **focus-safe** — `#dry-moment` present, no
  `autofocus` in the page, `submitMomentFix` shipped, and the dictation script
  bundle contains **no `.focus()`**.

Story-01's recorder tests updated for the new return type (record → record|None).

```
$ uv run pytest -q tests/integration/test_dictation_moment_of_truth.py
7 passed in 1.16s
```

### Live screenshot

`scripts/screenshot_moment_of_truth.py` (no mic, no LLM): enables the pipeline
over a seeded project, runs an **offline** dry-run (journals a row → the fix
affordance appears), opens the form, teaches `intent → agent_task_buildout`, and
captures **`evidence/moment_of_truth.png`** — the green **"Taught ✓ — the copilot
will nudge similar dictations toward this, and the journal entry is marked
corrected."** state.

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2358 passed, 17 skipped
$ uv run ruff check holdspeak/web/routes/dictation/ holdspeak/plugins/dictation/journal.py
All checks passed!
$ (cd web && npm run build)   # ✓ 12 pages built
```

**0** `holdspeak/static/_built/` tracked.

## Invariants held

- **Additive / byte-identical when not correcting** — no routing/rewrite/typing
  path touched; the fix is a separate, opt-in POST. The recorder return-type
  change is transparent to the live path.
- **Reuses the engine** — the Phase-40 `CorrectionStore` + `dictation_corrections`
  do the teaching; this is the in-moment *surface* + the journal↔correction
  *linkage*, not a new memory engine.
- **Local & private** — the teach is gist-only + secret-filtered (a secret-like
  transcript flags the entry but stores nothing).
- **Focus-safe** — proven structurally (no `autofocus`, no `.focus()`).
