# Evidence — HS-45-04: Replay (prove it learned)

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-45-dictation-memory`.

## What shipped

The copilot learns — but the user never *saw* it get better. Replay makes the
"it's learning me" promise tangible: take a real stored utterance, re-run it
through the **current** pipeline, and show before → after. Correct an utterance,
replay it, watch the routing change.

### Endpoint — `POST /api/dictation/journal/{id}/replay`

`holdspeak/web/routes/dictation/pipeline.py`. Loads the entry, re-runs its
stored **transcript** through `_run_dictation_dry_run_text` in **dry-run mode**
— no typing, `journal=None` (**no new row**, original row untouched) — using the
entry's **original `project_root`** so routing context matches. Returns
`{before, after, detail, changed}`: `before` from the stored row, `after` =
`{block_id, confidence, target_profile, final_text, runtime_status}` derived from
the fresh run (`_routed_from_stages` picks the routed block), `changed` = a diff
flag. 404 on a missing entry / no journal; 400/500 mirror the dry-run route.

### UI — the Journal (HS-45-02 cards)

`web/src/pages/dictation.astro` + `web/src/scripts/dictation-app.js`. Each
journal card gets a **↻ Replay** action → posts replay → renders an inline
**before → after diff**: a headline ("↻ The pipeline routes this differently
now." vs "Same result as before…"), a `route` row and a `target` row (changed
values in accent, the old value struck through), the **improved final text**, and
a focus-safe **Copy** (clipboard) with **"Preview only — nothing was typed."**

### Re-insert decision (recorded)

Re-insert is **preview + copy-to-clipboard** — focus-safe and deliberate.
**OS-typing re-insert is deferred:** there is no web→typer seam in the route
layer, and typing into the active app from a background web click is the precise
**focus-steal vector this phase forbids**. The story explicitly permits
preview-only ("preview alone already proves the learning"). The clipboard copy is
the safe, explicit re-insert primitive (the user pastes where they want).

## Tests — `tests/integration/test_dictation_journal_replay.py` (5 tests)

- replay re-runs the transcript and returns before/after **without** a new
  journal row or mutating the original;
- **the payoff, offline:** baseline replay → record a `target` correction for the
  transcript → replay again → the routed `target` flips to the corrected profile
  (`browser`), `changed: true` — proven with no mic / no LLM via the
  target-correction nudge the dry-run applies;
- 404 on a missing entry; 404 with no durable repo;
- the **Replay action + before/after diff** ship in the page/bundle, and
  re-insert is preview-only (the bundle carries "Preview only", not OS-typing).

```
$ uv run pytest -q tests/integration/test_dictation_journal_replay.py
5 passed in 1.49s

$ uv run pytest -q tests/unit/test_dictation_routes_split.py
2 passed   # route-table guard updated: 34 → 35 (the replay route)
```

### Live screenshot

`scripts/screenshot_replay.py` (no mic, no LLM): seeds an entry targeting
`terminal_shell`, records a `target → browser` correction for its transcript,
then clicks **Replay** in the Journal and captures
**`evidence/replay_before_after.png`** — the diff showing
**`target: terminal_shell → browser`** (old struck through, new in accent) under
"↻ The pipeline routes this differently now.", with the copy-able improved result
and the "Preview only — nothing was typed." note.

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2363 passed, 17 skipped
$ uv run ruff check holdspeak/web/routes/dictation/pipeline.py
All checks passed!
$ (cd web && npm run build)   # ✓ 12 pages built
```

**0** `holdspeak/static/_built/` tracked.

## Invariants held

- **Never mutates the original** — replay is a fresh dry-run with `journal=None`;
  the stored row + the journal count are unchanged (asserted).
- **No mic** — replays the durable transcript, not audio; the correction→replay
  payoff is proven offline via the target-correction nudge.
- **Focus-safe** — preview + clipboard copy only; no OS-typing from the web.
- **Inherits current config/corrections/project-root** — replay reuses the same
  dry-run entry point, so it automatically reflects what the copilot knows *now*.
