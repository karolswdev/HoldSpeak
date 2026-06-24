# HS-67-05 — Docs wiring

- **Project:** holdspeak
- **Phase:** 67
- **Status:** backlog
- **Depends on:** HS-67-01, HS-67-02, HS-67-03, HS-67-04

- **Owner:** unassigned

## Problem

A dogfood harness nobody can find won't get run. The harness must be
discoverable from the contributor-facing docs, with the standing lesson that
docs stories touch the entry points, not just a buried file.

## Scope

- **In:** a short pointer to `dogfood/` from `CONTRIBUTING.md` (how to dogfood
  before a release) and/or the docs index; the `dogfood/README.md` kept as the
  in-place guide; a note in the roadmap. Voice-guard-clean for any `docs/*.md`
  touched.
- **Out:** rewriting product docs; the run itself (HS-67-06).

## Acceptance criteria

- [ ] `CONTRIBUTING.md` (or the docs index) links to `dogfood/PROTOCOL.md` with a
      one-line "how to dogfood a release".
- [ ] Any touched `docs/*.md` passes the doc-drift + voice guards
      (`uv run pytest -q tests/unit/test_doc_drift_guard.py`).
- [ ] `dogfood/README.md` is accurate to the shipped harness.

      See `evidence-story-05.md`.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_doc_drift_guard.py` (and the link
  check) green after the edits.
- Manual: follow the doc link cold and reach a runnable protocol.

## Notes / open questions

- Keep HS-IDs and roadmap vocabulary out of any user-facing `docs/*.md` (the
  guard enforces this); `dogfood/**` is exempt.
