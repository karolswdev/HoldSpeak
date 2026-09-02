# HS-165-06 - The docs: the Gate B partner surface

- **Project:** holdspeak
- **Phase:** 165
- **Status:** backlog
- **Depends on:** HS-165-04
- **Unblocks:** HS-165-07
- **Owner:** unassigned

## Problem

Gate B partners need a surface: what the project family does, how
the palette scopes it, how a client connects — the dedicated docs
story (house law).

## Scope

- **In:** the MCP docs surface extended for the project family
  (find the existing home — docs/ or README §MCP from the 133 arc;
  extend, never fork): the tool table (names, effects, command_id
  law), the resources, the palette + thread mode, the §15 scenario
  as a worked example (real transcript excerpts from 05's walk),
  the boundary notes (legacy reactions family vs graduated tools;
  what V0 refuses). POSITIONING voice rules apply; no prose in the
  UI law does not apply here — this IS prose, keep it honest and
  terse. Vocabulary guard (no em/en dashes) if it covers docs —
  check the guard's scope and follow it.
- **Out:** marketing; remote/ecosystem docs (MCP-008 deferred).

## Acceptance criteria

- [ ] A Gate B partner can go from zero to the §15 scenario with the doc alone (the walk transcript proves each step shown).
- [ ] Tool/resource tables match the shipped schemas exactly (greppable against project.py).
- [ ] Docs gates green (whatever lints cover docs/).

## Test plan

- **Docs + lint;** cross-checked against 05's transcript.
