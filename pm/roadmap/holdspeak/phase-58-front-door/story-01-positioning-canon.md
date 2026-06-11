# HS-58-01 — The positioning canon

- **Project:** holdspeak
- **Phase:** 58
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-58-02, HS-58-03, HS-58-04
- **Owner:** unassigned

## Problem
Nobody ever decided what HoldSpeak's story is. Each doc pitches its own
corner; the front door under-sells the whole; future doc stories have no
standard to align to.

## Scope
- **In:** `docs/internal/POSITIONING.md`: the one-liner (the user's "one
  copilot, two modes" lead), the audience statement (developers), 3-4
  pillars each with named shipped proof points, the honest named
  competitive frame (per tool: what they do better / what we do better /
  who should pick which; architecture-level, date-stamped), the voice
  rules (humanizer standard, no-dash rule, the honesty bar), the
  canonical feature-name table. CLAUDE.md source-canon entry; internal
  docs index touch if one exists.
- **Out:** any user-facing doc change (later stories).

## Acceptance criteria
- [ ] The canon encodes the user's three decisions verbatim and every
      pillar's proof points name shipped capabilities.
- [ ] The competitive frame covers cloud dictation, local Whisper apps,
      AI dictation services, Talon, raw Whisper CLIs — honest both ways.
- [ ] The canonical-name table declares one name per feature surface.
- [ ] CLAUDE.md lists the canon as a source-canon doc.

## Test plan
- Doc-guard slice (the canon is internal — the vocab guard must NOT scan
  it) + full suite.
