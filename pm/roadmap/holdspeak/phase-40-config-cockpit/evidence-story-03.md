# Evidence — HS-40-03 — Copilot Setup cockpit (UI)

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-40/hs-40-01-settings-api-knobs`
- **Owner:** unassigned

## What shipped

The `/dictation` runtime tab gained a rich **Copilot depth** group that sets
every Phase-39 knob from the UI — no `config.json` editing:

- **Rewrite passes** — a **segmented control** (1–5) with a live `N×` badge and
  a per-value descriptor ("Single pass — fastest…" → "Five passes — maximum
  refinement…"), plus a note that over-budget passes are auto-skipped.
- **Learn from my corrections** — a real **toggle switch** (`corrections_enabled`)
  noting the memory now survives a restart (→ curate in Memory).
- **Infer the target when unsure** — a toggle (`target_detect_llm_enabled`) that
  **reveals** a threshold slider (`target_detect_llm_below`, 0–1) with a live
  value badge only when on; collapses (animated) when off.

All wired to `GET`/`PUT /api/settings` (HS-40-01): the meta banner shows a live
depth summary (`depth: 3× passes · learns · infers target`), inline validation
mirrors the API bounds (1–5 / 0–1) before submit, and a **"Save & test in
dry-run"** button saves then jumps to the dry-run to try the exact config.

### Pre-existing tab bug fixed (required for the cockpit to be usable)

While verifying, the runtime tab rendered **blank** — a latent bug:
`activateSection` set `style.display = ""` but every `.view` carries the
`hidden` attribute and `.view[hidden] { display:none }` outranks the base
`.view { display:flex }`, so switched-to tabs never showed (proven by a HEAD
screenshot — clicking Runtime showed an empty page). Fixed `activateSection` to
drive the `hidden` attribute itself (clear on the active view, set on the rest).
This unblocks runtime **and** readiness / KB / project-context / hooks / dry-run.

## Files touched

- `web/src/pages/dictation.astro` — the `.depth-group` markup (segmented
  control + two switches + reveal-threshold) + the "Save & test in dry-run"
  button; Signal CSS for `.depth-group` / `.seg` / `.switch` / `.depth-subknob`
  (tokens only; segmented control, toggle switch, animated reveal).
- `web/src/scripts/dictation-app.js` — populate + collect the four knobs in
  `renderRuntime`/`saveRuntime`; `setRewritePasses`/`updateTargetBelowVis`/
  `updateTargetDetectReveal` helpers; `saveRuntimeAndTest`; depth summary in the
  meta banner; inline validation; **`activateSection` tab-`hidden` fix**.
- `tests/integration/test_web_dictation_settings_api.py` — new
  `test_dictation_page_includes_copilot_depth_controls` (the four control ids +
  "Copilot depth" + the test button are in the served page).
- `scripts/screenshot_cockpit.py` (**new**) — Playwright harness that serves a
  real server (temp config + DB, seeded corrections), drives the cockpit, and
  captures the evidence PNGs.
- `pm/.../evidence/cockpit_depth.png`, `cockpit_depth_group.png` — screenshots.

The Astro bundle was rebuilt (`cd web && npm run build`); only `web/src` is
committed — `git status` shows **no** `holdspeak/static/_built/` files.

## Verification artifacts

> `uv run` is broken on this machine; tests run via `.venv/bin/python -m pytest`.

- Build: `cd web && npm run build` → `8 page(s) built`, no errors.
- **Full UI round-trip (Playwright)**: set passes=4 · corrections on · infer
  on · threshold 0.55 in the UI → **Save** → reload the page → controls reflect
  it (`passes=4 badge=4× corrections=True llm=True below=0.55 threshold_revealed=True`)
  **and** the on-disk config matches (`passes=4 corrections=True llm=True below=0.55`).
- Tab fix proven: a clean probe (no DOM hacks) — `click rt → runtime: flex,
  hiddenattr: False` (was `display: none` at HEAD).
- Targeted: `.venv/bin/python -m pytest -q tests/integration/test_web_dictation_settings_api.py`
  → `27 passed`.
- Ruff (touched py) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2211 passed, 16 skipped` (was 2210/16; +1).
- Screenshots: `evidence/cockpit_depth_group.png` (the rich depth group, 3
  passes active, both toggles on, threshold revealed at 0.80) +
  `evidence/cockpit_depth.png` (the full cockpit).

## Acceptance criteria — re-checked

- [x] Every dictation/pipeline knob — incl. the four Phase-39 knobs — is
      settable from the UI and round-trips (set → PUT → reload shows it) —
      proven by the Playwright round-trip + on-disk check.
- [x] Rich Signal, not flat: segmented control, real toggle switches,
      reveal-on-toggle threshold, live badges, help text — see screenshots.
- [x] Inline validation matches the API (rewrite passes 1–5 integer,
      threshold 0–1) before submit.
- [x] Readiness-driven: the runtime load reads `/api/dictation/readiness` and
      renders runtime guidance; the meta banner shows the live depth summary.
- [x] No JSON editing required to fully configure the copilot.
- [x] Bundle rebuilt; no `_built/` staged; screenshots captured.

## Deviations from plan

- Fixed a **pre-existing** `activateSection` tab bug (blank non-default tabs) —
  out of the original scope but required for the cockpit (any cockpit) to be
  visible at all. It also restores readiness/KB/hooks/dry-run.
- The blocks / project-KB editors were **not** rebuilt (per scope) — they live
  on their own tabs, now reachable thanks to the tab fix.
