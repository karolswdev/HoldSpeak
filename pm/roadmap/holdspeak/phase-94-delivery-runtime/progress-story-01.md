# HS-94-01 progress record — Counterpart contract and worktree truth

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped scope (upstream adoption of
the contract is BACKLOG candidate Y; the vendored dw implements it fully).

## What shipped

- **Worktree truth:** `dw_pmo/events.py` resolves the journal through
  `git rev-parse --git-common-dir`, so a linked `git worktree` (whose `.git`
  is a file) emits and reads the shared event stream instead of silently
  no-opping. Chosen semantics: one journal per repository in the common dir;
  the existing `tree` field distinguishes parallel worktrees.
- **Self-hosted layout:** `story_evidence_payload` containment accepts both
  `<repo>/pm/roadmap` and `<repo>/pmo-roadmap/pm/roadmap`, resolved only
  from the mapped repo path (a CLI document cannot widen containment).
- **`dw capabilities --json`:** declares `capabilities_schema: 1`, served
  schema versions (feed 1, events 2, sessions 1, evidence 1), statuses,
  verbs, commands, and the resolved roadmap dir.
- **Cursored events:** `dw events --json --after <cursor>` returns
  `events_schema: 2` envelopes with stable line-number `event_id`s and a
  `source_cursor`; the legacy bare-array read is byte-identical; malformed
  lines never shift numbering.
- **Evidence manifest/asset:** `dw evidence manifest` lists story, evidence,
  phase status, final summary, parsed captured runs, and hashed/typed/sized
  assets under a derived `bundle_id` (sha256 of project:story:index_tree, so
  a changed tree changes the bundle); `dw evidence asset` streams only
  manifest-bound files and refuses traversal, symlinks, oversize, and
  unknown refs with typed reasons.

## Verification

20 new tests in `tests/unit/test_dw_counterpart_contract.py` drive the
vendored dw by subprocess against real scratch repos (git init + worktree
add + self-hosted layouts): worktree event emission and cursor reads,
capabilities shape, no-dup/no-gap cursor semantics, manifest content and
captured-run parsing, and six asset-containment refusals. Plus three
self-hosted evidence tests in the missioncontrol route suite. Combined lane
at integration: 60 passed. Captured at close in
[evidence-story-01](./evidence-story-01.md).

## Candidate-Y residue

Upstream reusable-processes adoption (capabilities/cursored events/manifest
in the source repo, with the cross-repo CI fixture pinning the counterpart
commit).
