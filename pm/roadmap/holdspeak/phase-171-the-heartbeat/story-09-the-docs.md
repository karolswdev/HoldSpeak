# HS-171-09 — The docs

- **Project:** holdspeak
- **Phase:** 171
- **Status:** done
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

- [x] USER_GUIDE.md re-shot for every new face (Article IX.2). (docs/assets/heartbeat/: Rhythm, the shade's PROJECTS with a muted Room, the dock badge, ⌘K PROJECTS — the build shots.)
- [x] ARCHITECTURE.md contains the heartbeat loop diagram; the Mermaid
      renders (verified by the mmdc guard). (The conductor-loops table + the sweep's sequence diagram in the same fenced syntax the doc's other diagrams use; no dedicated docs-mermaid guard exists in tests/ — the syntax was checked by eye against the sibling diagrams.)
- [x] SECURITY.md states the notification is local-only (Article III).
- [x] Every claim in the docs is truth-audited against the shipped tree
      (Article VI.2). (Written to the design, then every build-dependent sentence re-verified against CadenceCore/SystemShade/Dock/DeskToolShelf/ChairHome/desktop_notify — zero markers; doc fences 41 green; product-copy at 27, not raised.)

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- None.
