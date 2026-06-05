# Evidence — HS-40-05 — Documentation

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-40/hs-40-01-settings-api-knobs`
- **Owner:** unassigned

## What shipped

The user-facing guides now **lead with the web cockpit**; `config.json` is
reframed as the advanced/headless fallback. A factual correction landed too:
the correction memory is no longer "in-memory, never persisted" (HS-40-02 made
it DB-backed) — the docs said the opposite.

- `docs/INTELLIGENT_TYPING_GUIDE.md` §10 "Copilot Depth" rewritten:
  - Leads with **`/dictation → Runtime → Copilot depth`** (the four knobs as a
    control table mapping UI control → config field), with the cockpit
    screenshot.
  - The **correction-memory** paragraph corrected to "DB-backed and persists
    across restarts" + a **`/dictation → Memory`** curation walkthrough and the
    Memory-tab screenshot.
  - **Depth telemetry** documented as the Memory tab's "Pipeline depth · this
    session" panel (p50/p95 bars, budget guidance, multi-pass chips), with the
    `GET /api/dictation/readiness` `depth` block kept as the headless equivalent.
  - The `config.json` block moved under an **"Advanced"** heading.
- `docs/DICTATION_COPILOT.md`:
  - The ② Correction-memory row corrected from "Session-scoped, in-memory, never
    persisted" → "**Persists across restarts** (DB-backed); curate it in
    `/dictation → Memory`."
  - "Turn it on" now leads with the **UI** (Runtime / Copilot depth / Memory) +
    the cockpit screenshot; the `config.json` block tucked into an
    `<details>` "Advanced: headless / scripted" disclosure.
- `docs/assets/cockpit/copilot-depth.png`, `memory-panel.png` — the embedded
  screenshots (copied from the HS-40-03/04 evidence).

## Verification artifacts

> `uv run` is broken on this machine; tests run via `.venv/bin/python -m pytest`.

- Doc guards + link-check:
  `.venv/bin/python -m pytest -q -k "doc_drift or dangling or no_live_doc or link"`
  → `4 passed` (the new `assets/cockpit/*.png` links resolve; no drift).
- Stale-claim sweep: `grep` for "never persisted / not persisted / dies with the
  process / session-scoped" across live docs → no remaining correction-memory
  hit (the other "in-memory" hits are device registry / action items / telemetry,
  correctly so).
- Field-name cross-check: every documented knob (`rewrite_passes` /
  `corrections_enabled` / `target_detect_llm_enabled` / `target_detect_llm_below`)
  matches `holdspeak/config.py` `DictationPipelineConfig`.

## Acceptance criteria — re-checked

- [x] The guides present the web cockpit as the primary setup path; `config.json`
      is the advanced/headless alternative (moved under "Advanced" / a `<details>`).
- [x] Persistent correction memory + the memory/telemetry UI are documented
      (storage = SQLite, durability = survives restart, curate/clear in the
      Memory tab) — and the old "never persisted" claim is fixed.
- [x] Screenshots embedded (`assets/cockpit/copilot-depth.png`,
      `memory-panel.png`); doc drift-guard + link-check green.
- [x] Every documented control/field matches what shipped in 01–04.

## Deviations from plan

- None. (No new screenshots captured — reused the HS-40-03/04 evidence images.)
