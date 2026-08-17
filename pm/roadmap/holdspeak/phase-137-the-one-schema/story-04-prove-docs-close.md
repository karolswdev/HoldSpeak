# HS-137-04 — Prove on the real DB, docs, close

- **Project:** holdspeak
- **Phase:** 137
- **Status:** backlog
- **Depends on:** HS-137-02, HS-137-03
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The whole point is that the owner's real database opens again with no
data loss. Unit tests use synthetic DBs; this story proves it against the
owner's actual v63 data — safely, on a copy.

## Scope

### In

- **The real-DB proof (A6), on a COPY — never the original.** Copy
  `~/.local/share/holdspeak/holdspeak.db` to a scratch path; open the
  copy under the reconcile; assert:
  - all 133 tables survive (126 canonical + the 7 experimental orphans),
  - representative row counts are unchanged across a sample of populated
    tables (meetings, decisions/decision_records, workbenches, memory),
  - `scheduled_recordings` now EXISTS (it was missing at v63),
  - every canonical column is present on its table (no missing-column),
  - the open does not raise (no version refusal).
  Capture this through `dw evidence capture`. A reusable script in
  `scripts/` (e.g. `verify_reconcile_real_db.py`) that operates on a copy.
- **Docs:** update `docs/ARCHITECTURE.md` where it describes the DB /
  migrations — the migration chain is replaced by a declarative
  reconcile-on-open; note the additive-only invariant and the CHECK
  caveat. Remove/adjust any doc that references the version-migration
  system. (Doc-drift guard must stay green.)
- **The counsel** (mandatory, fresh `claude-opus-4-6[1m]`): review the
  reconcile design, the deletion, the real-DB proof, and the accepted
  CHECK caveat — "what would you not ratify."
- **The final summary** + cadence (README current-phase + last-updated,
  the status doc, story rows).

### Out

- New behavior; this story is proof, docs, and closeout.

## Acceptance criteria

- [ ] The real-DB proof passes on a COPY (A6): 133 tables + sampled rows
  survive, `scheduled_recordings` gained, all canonical columns present,
  no version refusal — captured through `dw evidence capture`.
- [ ] The verify script is checked into `scripts/` and re-runs on a copy.
- [ ] ARCHITECTURE updated; doc-drift guard green.
- [ ] The full suite is green (isolated HOME, `-n auto`), read before the
  flip; the counsel's verdict is recorded for the sitting.

## Test plan

- Full suite the way CI sees it (isolated HOME, `-n auto`).
- The real-DB proof captured through `.githooks/dw evidence capture`,
  operating on a copy of the owner's DB.
