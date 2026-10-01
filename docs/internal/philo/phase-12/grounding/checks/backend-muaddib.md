# Check — Muad'Dib (Claude Opus 5.5, session https://claude.ai/code/session_01L3k9v1STCS3ur6wJYy5AgF), 2026-09-30

Artifact: `docs/internal/philo/phase-12/grounding/backend.md` @ `6dd5feb06` (draft PR #714, Astra, session `01a0f4e2-337a-74e0-a8c5-571d7d344efd`).

VERDICT: RATIFY

FINDINGS:
1. The four findings agree with the faces half (#713):
   - an explicit document binding per icon (backend F1 = faces F8);
   - a Floor projection seam, not new primitives (backend F2 = faces F11);
   - an artifact source as one renderer plus named refusals (backend F3);
   - preview on drop with no auto-prepare (backend F4 = faces F4).
2. The two forks match the faces defaults: one brief icon for the latest brief (faces Q6); Summary first with the picker (faces G boards).
3. Verification. `test_hs171_shade_glass.py::test_shade_brief_row_1440` is a date time-bomb (it accepts only `SEP`/`2026`, and the real `generated_at` now reads `OCT 01`). It is red on main for every run from 2026-10-01. Home: a test fix now, owned by Muad'Dib (outside Phase 12). The thread-loop timeout is class (c).

CONDITIONS: none. MISSED: none of owner cost. TUESDAY: yes, the backend supports the drag-to-preview job with no new authority.
UNKNOWN: probes not rerun.
