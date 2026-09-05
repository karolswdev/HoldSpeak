# HS-175-08 — The docs

- **Project:** holdspeak
- **Phase:** 175
- **Status:** backlog
- **Depends on:** HS-175-06
- **Unblocks:** HS-175-09
- **Owner:** unassigned

## Problem

Every new face and behavior introduced in Phase 175 (calendar events on
the desk, event-born recordings, the meeting Watch adapter, the week
brief) must appear in the project's documentation.

## Scope

- In:
  - docs/USER_GUIDE.md: re-shot for the calendar week view, the
    event-born recording row, the meeting Watch entity in a Room, the
    week brief in the shade.
  - docs/ARCHITECTURE.md: the calendar-to-recording pipeline (ingest
    -> event -> auto-create recording -> conductor arms) as a Mermaid
    sequence diagram; the meeting Watch adapter in the watch-sources
    diagram.
  - docs/SECURITY.md: statement that the meeting Watch adapter reads
    from the local database only (Article III).
  - README.md: mention of calendar integration under the feature list
    if one exists.
- Out:
  - New standalone docs.
  - Rewriting existing docs beyond the 175 sections.

## Acceptance criteria

- [ ] USER_GUIDE.md re-shot for every new face (Article IX.2).
- [ ] ARCHITECTURE.md contains the calendar-to-recording pipeline
      diagram and the meeting Watch adapter; the Mermaid renders
      (verified by the mmdc guard).
- [ ] SECURITY.md states the meeting Watch adapter reads locally
      (Article III).
- [ ] Every claim in the docs is truth-audited against the shipped
      tree (Article VI.2).

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- None.
