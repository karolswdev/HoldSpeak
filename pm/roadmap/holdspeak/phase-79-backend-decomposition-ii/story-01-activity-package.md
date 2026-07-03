# HS-79-01 — `db/activity.py` becomes the activity package

- **Project:** holdspeak
- **Phase:** 79
- **Status:** done — see [`evidence-story-01.md`](./evidence-story-01.md). Six concern
  mixins (largest 406 lines), zero body-line drift (programmatically checked), zero
  patch-target edits, suites unmodified and green.
- **Depends on:** nothing.
- **Unblocks:** HS-79-04 (the guard locks the new shape).

## Problem

`holdspeak/db/activity.py` is 1,596 lines: one `ActivityRepository` with ~45
methods across eight concerns (ledger, import checkpoints, privacy, nudge
dismissals, domain rules, project rules, enrichment connectors + runs,
annotations, meeting candidates). Every activity feature since Phase 53 landed
in the same class body.

## The design

The Phase-63 mixin pattern: `holdspeak/db/activity/` with single-concern
mixin modules (`records.py`, `rules.py`, `enrichment.py`, `candidates.py`,
plus the shared normalizers where they are used), composed into
`ActivityRepository` in `__init__.py`. Bodies move verbatim; the import
surface (`from .activity import ActivityRepository` in `db/__init__.py`) is
unchanged; tests unmodified except documented patch-target paths (expected:
none — the repo is reached through `db.activity`, not module-level patches).

## Test plan

Full unit suite unmodified and green; the story evidence quantifies the move
(source lines out == lines in, modulo the package plumbing) and lists any
patch-target edits (expected: zero).
