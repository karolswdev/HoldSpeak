# HS-177-02 — The design

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-01 (GO verdict)
- **Unblocks:** HS-177-03, HS-177-04, HS-177-05
- **Owner:** unassigned

**CONDITIONAL: this story proceeds only if HS-177-01 produces a GO
verdict. If the measured decision is CUT, this story is cancelled.**

## Problem

Every face in 177 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The Thread at Work introduces new face regions (Room data in the
thread context, Watch entity ref cards in thread turns, the grounded
ask result with cited refs) and modifies existing ones (the Chase and
Plan mode palettes). Without artboards these cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - Room data in the thread context area (the grounding strip showing
    Watch entities, needs-you items, and the Room's name; the ref
    card for a Watch entity cited in an answer).
  - The grounded ask result (an answer that cites Watch entities by
    ref, with provenance chips showing the entity source: GitHub PR,
    Jira issue, meeting decision).
  - The Chase mode palette widened to show project.* tools alongside
    existing people/follow-through tools.
  - The Plan mode palette widened to show project.get_room and
    project.get_steward_run.
  - The receipt row in the thread for a Chase effect (commitment
    transition, door item add) with the kernel receipt ref.
- Out: implementation; new library species (use existing ones).

## Acceptance criteria

- [ ] Artboards at 1440 + 393 on the ratified shell for every new
      face region (Article IX.2; UX-CANON.md rule E.1).
- [ ] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [ ] The owner's word on the canvas (Article IX.4).
- [ ] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [ ] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [ ] The Watch entity ref card shows the entity's source (GitHub /
      Jira / meeting) without egressing content (Article III).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The Watch entity ref card: does it show inline in the thread turn
  (like a grounding chip) or as a linked pullout? The existing
  grounding ref pattern (thread_service.py:23, hydrate_refs_detailed)
  uses inline chips for desk refs. The same pattern should extend to
  Watch refs. The owner decides on the canvas.
