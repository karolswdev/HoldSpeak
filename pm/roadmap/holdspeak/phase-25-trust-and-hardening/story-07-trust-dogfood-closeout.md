# HS-25-07 — Trust Hardening Dogfood + Closeout

- **Project:** holdspeak
- **Phase:** 25
- **Status:** backlog
- **Depends on:** HS-25-01, HS-25-02, HS-25-03, HS-25-04, HS-25-05, HS-25-06
- **Unblocks:** Phase 15
- **Owner:** unassigned

## Problem

The hardening stories each prove themselves in isolation; the phase needs one
end-to-end dogfood that confirms the trust posture holds together under real
use, plus the canon updates and the `final-summary.md` that close the phase.

## Scope

### In

- Live dogfood of the hardened paths:
  - Misconfigured/missing local intel model → confirm **no** transcript egress
    and a clear surfaced state (HS-25-01).
  - Web runtime token gate working for the bundled client; non-loopback bind
    refused without a token (HS-25-02).
  - Transcription timeout fires and recovers on a forced hang (HS-25-05).
- Run the full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`;
  capture output.
- Re-check every phase exit criterion with evidence links.
- Update canon touched by the phase (`README.md`, `docs/MEETING_MODE_GUIDE.md`,
  `docs/SECURITY.md`) and the project `README.md` "Last updated".
- Write `final-summary.md`; freeze `current-phase-status.md`; flip the project
  README phase index (25 → done) and move the current pointer to the next phase
  (26).

### Out

- Any new hardening work beyond closing HS-25-01..06.

## Acceptance criteria

- [ ] Dogfood notes recorded for the three live scenarios above with observed
      results (not just assertions).
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` output captured and
      green (or failures named with follow-up stories).
- [ ] Every Phase 25 exit criterion re-checked with an evidence link.
- [ ] `final-summary.md` written; `current-phase-status.md` frozen.
- [ ] Project `README.md` phase index + current pointer updated.

## Test plan

- Unit/integration: full suite per the command above.
- Manual / device: the three dogfood scenarios on real hardware.

## Notes / open questions

- This is the closeout chunk; it ships only after HS-25-01..06 are `done`.
- Honor the metal-exclusion memory: the full-suite command ignores
  `tests/e2e/test_metal.py`.
