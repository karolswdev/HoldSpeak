# Phase 114 - The Nerve

**Status:** DRAFT. Seven stories that wire the intelligence
architecture to the user's hands. HoldSpeak has 14 distinct AI
surfaces; on a fresh install, zero of them work. This phase makes
intelligence reachable from a fresh desk, puts Ask AI behind a
keyboard shortcut, gives every inference surface an honest egress
readout, and makes the Models settings actually useful with
per-destination probing and model discovery. When this phase ships,
a user with a LAN LLM at .43:8080 can seed the desk and ask a
question in two steps, not twelve.

**Last updated:** 2026-08-02 (drafted from comprehensive AI
usability study — 14 surfaces audited, 19 findings prioritised,
design incorporation plan grounded in Signal Workbench material
model).

## Why this phase exists

Phase 112 proved the one-dial architecture works. The
`InferenceTarget` is the only truth, the Models module is the only
face. But between "the architecture works" and "a user can use AI"
there are 10–15 manual steps, no keyboard path, and 10 of 14
inference surfaces that invoke LLMs without an egress badge. The
nerve endings are missing.

The applicability study (2026-08-02) found:

1. **Zero of 14 AI surfaces work on a fresh install.** The seed
   creates drawers but no inference destination, no starter agent,
   no demo workflow. The first-run flow validates transcription,
   not intelligence.

2. **Ask AI has no keyboard shortcut, no floor menu entry, and no
   context verb on most objects.** It is reachable only through
   lasso selection of existing cards. Article II says intelligence
   must be a DeskPrimitive or an affordance on one.

3. **10 of 14 surfaces invoke LLM inference without an egress badge
   at the decision point.** Editor transforms, meeting intel,
   dictation pipeline, cadence, decision/delivery drafting, and
   workbench workflow runs have no Article III compliance.

4. **Probe tests the wrong target.** The Models "Probe" button
   validates the saved dictation runtime, not the destination row
   being edited. Model discovery APIs exist in the backend but
   have no React consumer.

5. **`this_machine` appears "ready" when local model files are
   absent.** The user sees a green lamp, asks a question, gets a
   502. Article VI violation.

## Grounding

- Constitution Articles II (primitive), III (egress), V (consent),
  VI (honest), IX (proof), XI (kernel).
- Positioning: "one local copilot."
- Phase 112 exit proof: the one-dial architecture works.
- Design instruction: egress is a LampGadget readout in the
  instrument footer, not an EgressChip in the title bar. Two homes,
  one species. Same row as the controls it describes. Always visible,
  never decorative.

## Relationship to Phase 113 (The Forge)

The Nerve is a prerequisite for The Forge. HS-113-04 (AI in the
editor) needs the RunsOnPicker and egress infrastructure this phase
creates. HS-113-05 (Voice Intent Router) needs the seeded
destination. Ship The Nerve first, then The Forge builds on solid
ground.

## Where we are

DRAFT — awaiting owner charter.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-114-01 | The seeded nerve | in-progress | [story-01-the-seeded-nerve](./story-01-the-seeded-nerve.md) | — |
| HS-114-02 | Ask AI is a first-class citizen | in-progress | [story-02-ask-first-class](./story-02-ask-first-class.md) | — |
| HS-114-03 | Per-destination probe | in-progress | [story-03-per-destination-probe](./story-03-per-destination-probe.md) | — |
| HS-114-04 | Egress on every inference path | in-progress | [story-04-egress-everywhere](./story-04-egress-everywhere.md) | — |
| HS-114-05 | Editor transforms: propose, don't replace | in-progress | [story-05-editor-proposals](./story-05-editor-proposals.md) | — |
| HS-114-06 | The honest target | in-progress | [story-06-the-honest-target](./story-06-the-honest-target.md) | — |
| HS-114-07 | The walk | backlog | [story-07-the-walk](./story-07-the-walk.md) | — |
