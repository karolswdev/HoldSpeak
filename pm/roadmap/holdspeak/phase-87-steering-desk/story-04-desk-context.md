# HS-87-04 — Ground: desk objects ride into the steer

- **Project:** holdspeak
- **Phase:** 87
- **Status:** done
- **Depends on:** HS-87-03
- **Unblocks:** HS-87-06
- **Owner:** unassigned

## Problem

The owner's sentence: *"including specific things from the Desk as
context."* The desk already knows how to hydrate its objects into a
model run with provenance (the grounding pass). A steer deserves the
same: pick a meeting artifact, a note, a KB entry — the agent in the
pane receives the real content, labeled, capped, and the audit knows
exactly what rode along.

## Scope

- In: factor the hub's `/api/ask` grounding hydration into a shared
  helper (`grounding_hydrate(refs) -> [(kind, title, text)]`) used by
  BOTH ask and steer; `POST /steer` accepts `grounding: [refs]`;
  composition: the spoken/typed message, then per-object fenced
  blocks with one-line provenance headers, hard-capped (~8 KB total,
  per-object cap, the cap SHOWN in the composer before send);
  `GroundingSection` reused in the pull-out composer (the same
  picker the ask panel uses); audit rows carry the refs.
- Out: new hydratable kinds (whatever ask hydrates today is the
  set); auto-grounding (the human picks every object); persistence
  of picks across sessions (per-steer, deliberately).

## Acceptance criteria

- [ ] The same refs hydrate byte-identically through ask and steer
      (one helper, a test pins parity).
- [ ] The composed steer shows the exact final text (context blocks
      included) BEFORE send — executed == previewed, the actuator
      rule applied to composition.
- [ ] Over-cap picks refuse at compose time, naming the size; unknown
      refs refuse naming the id (the ask seam's existing behavior,
      preserved).
- [ ] Control vs treatment on a live session (the Phase-53 proof
      pattern): the same question steered without and with a
      grounded artifact; the agent's next output demonstrably uses
      the grounded content — captured in evidence.
- [ ] Full suite green (read from the file).

## Test plan

- Unit: hydration-parity test, cap/refusal tests, composition
  formatting tests (fences, headers, ordering).
- Integration: the control-vs-treatment live proof.
- Manual / device: drag-pick a meeting artifact into a steer.

## Implementation direction

- **The factoring is the story.** Find the hydration inside the ask
  route (`web/routes/primitives/ask.py`, the `grounding` refs
  handling from Phase 83); move it verbatim into a shared module
  (e.g. `holdspeak/grounding.py` or the primitives `_shared`), leave
  ask's behavior byte-identical (its tests must pass unmodified —
  the Phase-63 verbatim-move discipline).
- **Composition format:**
  `--- from meeting: "Kickoff 2026-07-01" (artifact: decisions) ---`
  then the content, then a closing fence; message first, context
  after (agents read the ask before the payload); a final line
  naming how many objects rode along.
- **The gauge pattern:** the composer shows `context 3.2 KB / 8 KB`
  live as picks change (the Phase-83 context gauge is the visual
  precedent; a tiny version suffices).
- **Provenance:** reuse the refs shape `RunProvenance` records —
  the audit row's `grounding` field is the same list; no second
  vocabulary.
- **UI:** `GroundingSection.tsx` mounts inside the pull-out composer
  with zero changes if possible (it already speaks picker + gauge);
  if it is ask-coupled, decouple by props, never by copy-paste.
