# HS-65-04 — Closeout: tag, publish, verify

- **Project:** holdspeak
- **Phase:** 65
- **Status:** backlog
- **Depends on:** HS-65-01, HS-65-02, HS-65-03
- **Unblocks:** phase exit
- **Owner:** unassigned

## Problem
The tag is the publish; it happens once, from the merged main, after
everything else is green.

## Scope
- **In:** PR merged on green → `git tag v0.3.0` on the merge commit →
  push → the release workflow publishes → poll PyPI for 0.3.0 → fresh
  venv `pip install holdspeak==0.3.0` FROM PYPI reaches doctor → publish
  the GitHub release with the notes → final-summary; README cadence;
  memory.
- **Out:** the announcements (handed off, not posted).

## Acceptance criteria
- [ ] Workflow green; PyPI serves 0.3.0; the from-PyPI install proof
      recorded.
- [ ] GitHub release live with the notes.
- [ ] final-summary; cadence; memory.

## Test plan
- The from-PyPI install proof is the test.
