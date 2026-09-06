# HS-176-07 — The docs

- **Project:** holdspeak
- **Phase:** 176
- **Status:** done
- **Depends on:** HS-176-06
- **Unblocks:** HS-176-08
- **Owner:** unassigned

## Problem

Every new face and behavior introduced in Phase 176 (the correction
flow, the journal stream, MicButton coverage, the full speak-learn
loop) must appear in the project's documentation.

## Scope

- In:
  - docs/USER_GUIDE.md: re-shot for the correction flow on the Speak
    face, the journal stream with filters, MicButton on every input.
  - docs/ARCHITECTURE.md: the speak-learn loop as a Mermaid diagram
    (speak → pipeline → land → judge → correct → persist → next match
    → correction fires).
  - README.md: the "learns how you work" pillar updated to reflect
    that the correction loop is trained, not just designed.
- Out:
  - New standalone docs.
  - Rewriting existing docs beyond the 176 sections.

## Acceptance criteria

- [ ] USER_GUIDE.md re-shot for every new face (Article IX.2).
- [ ] ARCHITECTURE.md contains the speak-learn loop diagram; the
      Mermaid renders (verified by the mmdc guard).
- [ ] README.md pillar 2 ("It learns how you work") is truth-audited
      against the shipped tree (Article VI.2).
- [ ] Every claim in the docs is truth-audited (Article VI.2).

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- None.
