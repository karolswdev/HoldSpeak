# HS-36-06 — Phase closeout + final-summary

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** HS-36-01, HS-36-02, HS-36-03, HS-36-04, HS-36-05
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Close Phase 36 cleanly: confirm both tracks landed — **experience** (card shell,
copy-as-Markdown, per-type polish, no overflow) and **intelligence** (segment-aware
intent extraction) — the bundle is rebuilt, the spoken-e2e passes, and the
**before/after** comparison is captured. Then write the phase `final-summary.md`.

## Scope

- **In:**
  - Final `cd web && npm run build` (so the served app/e2e reflect the latest source);
    `holdspeak/static/_built/` is a **gitignored build product** — confirm it's NOT
    staged/committed (only `web/src/**` source is).
  - **The headline before/after.** Present the two captured screenshots of the same
    messy meeting (HS-36-04): **BEFORE** the intelligence fix (old fixed-window/keyword
    routing — intents diluted away, sparse artifacts) and **AFTER** (segment-probe
    routing — the genuinely-present intents fished out, a dense/varied artifact set,
    rendered in the new cards). Both in this phase's `evidence/`; the diff is the phase's
    headline evidence.
  - Re-run the spoken-e2e for real (incident-retro + the dynamic meeting) to confirm the
    final look + selectors; capture the AFTER shot if not already captured in HS-36-05.
  - Confirm all spoken-e2e artifact selectors pass (preserved or updated in lockstep —
    not silenced).
  - `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.
  - `final-summary.md` (lead with the before/after); flip the project README phase row →
    `done` + Current-phase + Last-updated; refresh HANDOVER (tee up Phase 37 — Actuators).
- **Out:** new work; this is verification + record.

## Acceptance criteria

- [ ] Bundle rebuilt from the final source (gitignored — not committed); `_built` is not
      staged; the served app reflects the source.
- [ ] **BEFORE and AFTER screenshots** of the same messy meeting committed to
      `evidence/`; the AFTER shows materially more of the genuinely-present intents
      surfaced (and the new cards). The diff is described in `final-summary.md`.
- [ ] Spoken-e2e (incident-retro + dynamic) re-run for real; all artifact selectors pass.
- [ ] Full suite green.
- [ ] `final-summary.md` written; README phase row `done`; HANDOVER refreshed (Phase 37
      — Actuators teed up).

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s` (dangerouslyDisableSandbox
  to reach the LAN LLM) — incident-retro + dynamic meeting pass; AFTER screenshot shows
  the rich extraction + the new cards.

## Notes / open questions

- The BEFORE shot is captured in HS-36-04 (old routing) and the AFTER in HS-36-05 (new
  routing) — both land in this phase's `evidence/`; this story just verifies + presents
  them. Name them clearly (e.g. `dynamic_meeting_before.png` / `_after.png`).
