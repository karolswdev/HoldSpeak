# HS-65-02 — The release cut

- **Project:** holdspeak
- **Phase:** 65
- **Status:** done
- **Depends on:** HS-65-01
- **Unblocks:** HS-65-04
- **Owner:** unassigned

## Problem
PyPI is fourteen phases stale at 0.2.2; the version, the changelog, and
the install proofs must be ready before any tag exists.

## Scope
- **In:** pyproject → 0.3.0; the CHANGELOG 0.3.0 entry (P51–P64, Keep a
  Changelog, canon names); a version-claims sweep over README/docs;
  build sdist+wheel locally exactly as the workflow does (bundle-presence
  checked); fresh-venv install from the wheel → `holdspeak doctor` on
  macOS AND on .43 (real metal, the standing rule).
- **Out:** the tag (closeout only).

## Acceptance criteria
- [x] Version + changelog shipped; no stale version claims.
- [x] The wheel carries the bundle; both fresh-venv doctors recorded.
- [x] Full suite green.

      See `evidence-story-02.md`.

## Test plan
- The wheel build + two install proofs; the full suite.
