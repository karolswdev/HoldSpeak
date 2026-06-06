# Evidence — HS-42-08 — First-run evidence + docs closeout

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

See [`final-summary.md`](./final-summary.md) for the full phase wrap-up.

## What shipped (closeout — verification + record)

- **The TTFD dogfood** — `scripts/dogfood_first_run.py` (committed, reproducible):
  fresh server → `/setup` interactive, one primary action, the guided
  first-dictation, "Test my runtime", a real dictation success (the runtime's
  `dictation_typed` broadcast) → "It worked" + the durable milestone, a returning
  user yields to the dashboard (no nag), and `config.json` never hand-edited.

  ```
  1. launch → /setup interactive: 1.13s
  2. one primary action: "Set a valid local model path (…)"
  3. model assistant test: ✓ Basic voice typing — no LLM runtime configured…
  4. first dictation: It worked — text landed in your app. You're all set.
     durable milestone set (by the runtime on a real dictation): True
  5. returning user → dashboard (no nag)
  6. config.json hand edits: NONE (zero file editing)
  TTFD-to-ready: 1.13s · all-in-app, zero file edits · DOGFOOD OK
  ```

  Capture: [`evidence/first_run_dogfood.txt`](./evidence/first_run_dogfood.txt).
  The real-mic stopwatch on a physical device stays a manual capture
  (hardware-gated — same posture as the metal/spoken-e2e suites).

- **Docs lead with the guided path** — `docs/GETTING_STARTED.md` rewritten: a new
  "Open Setup — the guided home" step + the CLI nudge, the routes table gains
  `/setup` + `/settings`, and hand-edited config is demoted. Doc drift-guard +
  link-check green.

- **Record reconciled** — `final-summary.md` written; `current-phase-status.md`
  → CLOSED 8/8; story-08 → done; roadmap README "Current phase" → CLOSED +
  phase-index row → done; HANDOVER TL;DR refreshed to Phase 42.

## Verification

```
uv run pytest -q tests/unit/test_doc_drift_guard.py     → 3 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py       → 2306 passed, 16 skipped
git ls-files holdspeak/static/_built/ | wc -l           → 0
uv run python scripts/dogfood_first_run.py              → DOGFOOD OK
```

## Acceptance criteria

- [x] TTFD captured (`DOGFOOD OK`, launch→/setup 1.13s, zero file edits); the
      real-mic frame stays a hardware-gated manual capture.
- [x] Getting Started leads with the guided `/setup` path; no live doc makes
      hand-edited config the primary path; doc-guards + link-check green.
- [x] Full suite green (2306/16); all-optional-off default byte-identical; no
      `_built/` tracked (0).
- [x] `final-summary.md` exists; status frozen; README → done; HANDOVER updated;
      PR opened/merged.
