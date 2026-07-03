# HSM-19-07 — Docs + the staged metal walk

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** in-progress — the docs half is DONE (README companion section carries the
  six new abilities, voice guard green; ARCHITECTURE's client-layer section verified
  current) and the walk is STAGED press-play at [`HSM-19-07-WALK.md`](./HSM-19-07-WALK.md)
  (six checks W1–W6 with controls, sharing the 18-06 couch session). What remains is the
  owner's device walk; PASS×6 closes this story and the phase.
- **Depends on:** 19-01…19-06 (documents what shipped; the walk exercises it).
- **Unblocks:** phase close (the owner's device walk is the gate).
- **Owner:** unassigned

## Problem

Every phase gets its own documentation story (standing rule), and this phase's metal gate
must be press-play so it can join the owner's 18-06 couch session instead of costing a
separate setup.

## The design

1. **Entry points current:** README + `docs/ARCHITECTURE.md` where the iPad's meeting-side
   capabilities are named (the companion reads aftercare/artifacts/proposals/learning;
   imports into the hub pipeline) — entry points, not just deep docs (the Phase-64 lesson).
2. **`HSM-19-07-WALK.md`**, press-play, mirroring `HSM-18-06-WALK.md`: the same `.43`
   rewriter setup, five checks with controls — W1 aftercare digest + file-issue →
   proposal, W2 facet narrowing against the real archive, W3 a real `.vtt` import from
   Files, W4 the confidence ring over real synthesized artifacts, W5 a proposal approved
   from the queue (slack executes; the egress mark verified). Fillable trace, PASS×5
   closes the phase.
3. **Screenshots current** under `screenshots/` for every story.

## Scope

- **In:** entry-point docs, the walk doc, the trace template, screenshot inventory.
- **Out:** running the walk (the owner's hands, on the cabled iPad — per the standing
  verify-on-device rule).

## Test plan

- Docs voice guard green (`uv run pytest -q -k voice` if the touched files are guarded).
- The walk doc validated press-play against a live local hub (steps executable, no
  missing prerequisite).
