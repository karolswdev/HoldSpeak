# HS-16-05 Evidence — RFC reality-check + phase exit

**Date:** 2026-06-01.
**Story:** [story-05-rfc-reality-check.md](./story-05-rfc-reality-check.md).
**Phase summary:** [final-summary.md](./final-summary.md) (the primary deliverable).

## Implementation Evidence

**RFC reality-check (`docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`):**
- §"Initial Built-In Plugins (Phase 1)": the 5 listed entries annotated —
  `mermaid_architecture` ✅ shipped, the other four ⚠️ stub.
- New **"Reality status (2026-06-01)"** subsection: a table of all **thirteen**
  `_BUILTIN_PLUGIN_DEFS` entries with shipped/stub status and a one-liner per
  stub describing what its real `run()` should produce.
- New **"Appendix A — What 'shipped' means in this RFC"** with the four-bar
  definition; notes `mermaid_architecture` as the first plugin meeting all four.

**Calibration pass** (`evidence/calibration.txt`): 3 transcripts (heavy / mixed /
low architecture density) × available configs × 3 runs each.

```text
local-Q6 (.43:8080, Qwen3.5-9B-UD-Q6_K_XL):  heavy 3/3, mixed 3/3, low 3/3 (100%), ~1–3.6s, conf 1.00
local-Q4 (127.0.0.1:8081, Qwen3.5-9B-Q4_K_M): heavy 0/3, mixed 0/3, low 0/3 (0%),  ~28–30s, conf 0.00
cloud (gpt-5-mini): NOT TESTED — no API key on this remote machine
```

Finding: reliable on Q6 across all densities; Q4 is a reasoning-style build that
leaks chain-of-thought into `reasoning_content` and leaves `content` empty
(parse fails + ~10× slower). Content-extraction mismatch, not a diagram-quality
cliff — `mermaid_architecture` stays ✅ shipped with the ≥Q6 / reasoning-fallback
caveat handed to phase 17. Full reading in `final-summary.md`.

**Phase closeout:**
- `final-summary.md` written (goal assessment, exit-criteria re-run, stories
  table, calibration table, surprises/lessons, phase-17 handoff, asset/test
  posture) per `roadmap-builder.md` §2.5.
- `current-phase-status.md` frozen with a **"Phase closed: 2026-06-01"** line.
- Project `README.md`: phase-16 row → `done`; "Last updated" + "Current phase"
  pointer updated to the next non-done phase.

## Tests

No new test code (per the story). Regression sweep only:

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py
# 1902 passed, 13 skipped
```

## Result

Phase 16 closes 5/5. The plugin substrate is proven end-to-end on a real
LLM-backed plugin, the parent RFC no longer overstates what exists, and phase 17
has a calibration baseline + the reasoning-content caveat to act on.
