# HS-50-07 — Closeout — dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 50
- **Status:** backlog
- **Depends on:** HS-50-01, HS-50-02, HS-50-03, HS-50-04, HS-50-05, HS-50-06
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that HoldSpeak is now safe to install,
upgrade, and trust (one version, the safe schema matrix, a backup, an honest
doctor, a verified install), captured as a dogfood, and merged.

## Scope
- **In:**
  - A **dogfood** proving the safety matrix end to end, no real mic/LLM: create a
    fresh DB (at version); open at-version (no-op); stamp an older version -> open
    -> a backup is taken + schema applied + data intact; stamp a newer version ->
    open -> refused + the file untouched; `doctor` reports the schema state
    honestly; the version is one number. Print PASS.
  - `final-summary.md`; flip the phase to CLOSED; update the project README + phase
    status per the operating cadence; flip the [backlog](../BACKLOG.md) candidate C
    row to shipped; **open a PR to `main`** and merge on green CI.
- **Out:** new feature work; the actual PyPI publish (a maintainer step once the
  gate is green — note it in the summary).

## Acceptance criteria
- [ ] A green dogfood transcript proving fresh / equal / older(+backup) / newer(refused)
      and an honest doctor schema report.
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
      `npm run build` ✓; 0 `_built/` tracked.
- [ ] `final-summary.md` written; phase CLOSED; status docs + roadmap updated;
      BACKLOG candidate C flipped to shipped; PR to `main` opened (and merged on
      green CI).

## Test plan
- Full suite + the phase dogfood; manual read of the upgrade/backup policy doc.

## Notes / open questions
- Mirror the Phase-49 closeout pattern (dogfood script + final-summary + PR). The
  dogfood drives the DB layer directly (stamp the `schema_version` table) rather
  than a real schema change.
- If the team decides to publish to PyPI, that is a separate maintainer action
  after this PR merges; record the decision in `final-summary.md`.
