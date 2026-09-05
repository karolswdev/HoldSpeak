# HS-177-06 — The walk

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-05
- **Unblocks:** HS-177-07
- **Owner:** unassigned

**CONDITIONAL: this story proceeds only if HS-177-01 produces a GO
verdict. If the measured decision is CUT, this story is cancelled.**

## Problem

The owner's attended walk on his desk is the exit gate (Article IX.4).
The Thread at Work introduces new behavior (Room grounding, Watch
entity citations, Chase over Room data, Plan with steward output) that
must be proven on his real desk with real Room data. The walk is the
proof that the Thread is a work tool.

## Scope

- In:
  - The owner's attended walk on his desk, both widths (1440 + 393).
  - The walk covers:
    1. He opens a Chase thread from a Room ("Continue in thread" from
       the Room).
    2. The thread reads Watch entities from the Room; the model cites
       them by ref.
    3. He asks: "What is [team member] waiting on from me?" The
       answer cites Watch entities with freshness.
    4. He confirms a Chase effect (commitment transition or agenda
       add); the kernel receipt shows in the thread.
    5. He opens a Plan thread from a Room; the model reads the
       steward's last run and the Room's delta.
    6. He keeps the Plan answer as a Note.
    7. He opens a Draft thread; no tools fire; composition only.
  - The stopwatch per face (Article IX.2).
  - His verdict (Article IX.4).
- Out:
  - Automated rig legs (those are in stories 03-05).
  - Linux walk.

## Acceptance criteria

- [ ] The owner walks all seven beats on his real desk (Article IX.1,
      IX.4).
- [ ] A Chase thread grounded on a Room reads Watch entities and cites
      them by ref.
- [ ] A Chase effect fires with a kernel receipt visible in the
      thread.
- [ ] A Plan thread reads the steward's last run and the Room's delta.
- [ ] A Draft thread has no tools and no context lookups.
- [ ] His word.

## Test plan

- Unit: n/a (walk story).
- Integration: n/a.
- Manual: the seven-beat walk on his desk; screenshots at both widths;
  the stopwatch per face; his verdict recorded verbatim.

## Notes / open questions

- The walk depends on: (a) at least one Room with Watch entities, (b)
  at least one steward run on a Room, (c) at least one People
  relationship with commitments. If his desk lacks these at walk time,
  they must be created during the walk.
