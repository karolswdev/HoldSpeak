# HS-100-01 — The grounding

- **Project:** holdspeak
- **Phase:** 100
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-100-02

## Problem

Five phases of UI work shipped without anyone writing down what a
person at this desk is trying to do. Every future judgment needs the
ground truth first: the philosophy as ratified, the seams as built,
and the use cases as lived — not as imagined.

## Scope

- In:
  - a deep read of the canon: CONSTITUTION.md (articles, verbatim
    obligations), POSITIONING.md (the story, pillars, competitive
    frame, voice), the plan RFCs (plugin system, MIR, DIR, web
    flagship), README/USER_GUIDE (the promised surface);
  - the seams as built: ARCHITECTURE docs + the real route/verb
    inventory — what the hub can actually DO today, where the value
    is produced (dictation pipeline, meeting intelligence, delivery/
    steering, knowledge/grounding, the mesh);
  - the use cases as lived: every UAT campaign, scenario, and debrief
    (the owner's real sittings ARE the usage record), the dogfood
    findings, the phase history's owner verdicts collected in one
    place;
  - **docs/internal/GROUNDING.md**: the jobs HoldSpeak is hired for
    (ranked), the moments of felt value per job, the personas/postures
    at the desk (working ≠ configuring ≠ reviewing), the seams that
    serve each job, and the explicit non-goals.
- Out:
  - any judgment of the current UI (HS-100-02); any design (03); any
    code.

## Acceptance criteria

- [ ] GROUNDING.md exists and cites its sources (article numbers,
      RFC sections, campaign IDs) — no unsourced claims.
- [ ] The jobs are RANKED with the evidence for the ranking; each job
      names its moment of felt value and the seam that produces it.
- [ ] The owner-verdict history (95→spike) is collected verbatim as
      an appendix — the bar this phase must clear, in the owner's own
      words.

## Test plan

- Doc guards; the citations spot-checked against sources.

## Evidence required

- The document; the source list; guard output.
