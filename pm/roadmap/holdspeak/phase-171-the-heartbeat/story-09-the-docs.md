# HS-171-09 — The docs

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** HS-171-08
- **Unblocks:** HS-171-10
- **Owner:** unassigned

## Problem

Every new face introduced in Phase 171 (the shade PROJECTS section, the
macOS notification, the cadence row, the command-deck entries, the dock
badge) must appear in the project's documentation. The USER_GUIDE needs
re-shot screenshots, the ARCHITECTURE doc needs the heartbeat loop, and
SECURITY needs the notification egress statement.

## Scope

- In:
  - docs/USER_GUIDE.md: re-shot for the shade PROJECTS section, the
    notification, the cadence row in Settings, the command-deck
    PROJECTS section.
  - docs/ARCHITECTURE.md: the heartbeat loop (cadence tick -> sweep ->
    needs-you cache -> notification edge -> shade poll) as a Mermaid
    sequence diagram.
  - docs/SECURITY.md: the notification egress statement (local OS
    notification, never remote push; Article III.1).
  - README.md: one-line mention of the Heartbeat under the feature
    list if one exists.
- Out:
  - New standalone docs.
  - Rewriting existing docs beyond the Heartbeat sections.

## Acceptance criteria

- [ ] USER_GUIDE.md re-shot for every new face (Article IX.2).
- [ ] ARCHITECTURE.md contains the heartbeat loop diagram; the Mermaid
      renders (verified by the mmdc guard).
- [ ] SECURITY.md states the notification is local-only (Article III).
- [ ] Every claim in the docs is truth-audited against the shipped tree
      (Article VI.2).

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- None.
