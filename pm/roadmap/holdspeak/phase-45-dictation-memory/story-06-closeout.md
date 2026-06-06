# HS-45-06 — Closeout: before/after + dogfood + PR

- **Project:** holdspeak
- **Phase:** 45
- **Status:** backlog
- **Depends on:** HS-45-01, HS-45-02, HS-45-03, HS-45-04, HS-45-05
- **Owner:** unassigned

## Problem
Close Phase 45: prove the loop end-to-end with a no-mic dogfood, capture the
headline before/after (a black-box dictation vs a journaled, correctable,
replayable one), re-verify the invariants, write the `final-summary.md`, and open
the PR to `main`.

## Scope
- **In:**
  - A **no-mic dogfood** (a script under `scripts/`, mirroring
    `dogfood_first_run.py` / `dogfood_wizard.py`): dry-run a few utterances →
    the **journal** populates → **correct** one in the moment → it **teaches** →
    **replay** that utterance → the routing visibly changes → "it learned".
    Emit a clear `JOURNAL DOGFOOD OK` line.
  - **Before/after** evidence: the daily dictation loop *before* (ephemeral
    black box) vs *after* (journal timeline + in-moment fix + replay diff) —
    screenshots from the live cockpit.
  - **Invariant re-assertion:** `journal_enabled=false` ⇒ byte-identical
    dictation/dry-run output; no transcript egress; the in-moment surface never
    steals focus.
  - `final-summary.md` (goal/was-it-met, before/after, per-story recap,
    invariants, verification, handoff); flip the phase to CLOSED; update the
    roadmap README (current-phase + last-updated + the phase-index status).
  - Push the branch + open a PR to `main`; merge (merge commit) when CI is green.
- **Out:** new features (all landed in 01–04).

## Acceptance criteria
- [ ] The dogfood runs green end-to-end (`JOURNAL DOGFOOD OK`): dry-run → journal
      → correct → replay shows the corrected routing — **zero file edits, no mic**.
- [ ] Before/after captured for the dictation loop; `final-summary.md` written.
- [ ] Invariants re-asserted (journal-off byte-identical; no egress; focus-safe).
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      **0** `holdspeak/static/_built/` tracked.
- [ ] PR to `main` opened; merged when CI green; roadmap docs reflect CLOSED.

## Test plan
- Integration / dogfood: `uv run python scripts/dogfood_journal.py` → `JOURNAL DOGFOOD OK`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual: review the before/after captures; confirm the PR CI checks pass.

## Notes / open questions
- Keep the dogfood entirely on the dry-run path so it runs anywhere (no mic / no
  LAN-LLM dependency beyond what dry-run already needs).
