# HSM-15-12 — The context envelope (select meetings, expand their artifacts, into the ask)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** scaffolded — 2026-07-06, owner ask in the same breath as 15-11 (*"there's
  no clear path of being able to select meetings, and, in fact, expand them and include
  any bound artifacts... into the context of that q"*). 15-11 is WHERE the model runs;
  this is WHAT the question knows.
- **Depends on:** meetings + artifacts on the sync wire (shipped), the run path
  (`recipeRoleAndContext` / `runAssembled` / `callLLM`), `/api/ask` (16-04),
  `OnDeviceBudget` + the ContextGauge, [[story-11-agents-on-your-desktops-models]].
- **Owner:** unassigned

## Problem

Grounded 2026-07-06 (`DeskDioramaStage.swift:4977` `recipeRoleAndContext`): an agent's
context today is (a) `manualContext` typed text, (b) `useZoneContext` = ALL meetings
filed in the zone, each flattened to title + the first 2,000 chars of `routableText` —
all-or-nothing, artifacts never included — and (c) the KB as a **hint string only**
("Lean on the knowledge base X"), no content hydrated (the known gauge finding). The
route gesture (drop a meeting on an agent) makes the meeting the INPUT of one run — a
different verb than grounding. There is no way to say, at ask time: *these two
meetings, expanded to their decisions and action items, are what this question is
about.*

## The design — a picker, an envelope, and hub hydration

- **"Ground this ask" picker** — an attach affordance on the chat composer and the run
  sheet: select meetings (and notes / artifacts / KBs — any routable primitive). A
  selected meeting **expands**: transcript (bounded), intel summary, and each **bound
  artifact** (decisions, action items, summaries…) individually toggleable. The
  ContextGauge prices the selection live (`OnDeviceBudget.estimateTokens`), so the cost
  of "the whole transcript" vs "just the decisions" is visible before the run.
- **The envelope contract** — ONE structured assembly shared by every run target:
  ordered blocks with provenance headers (`[MEETING: <title> — <date>]`,
  `[ARTIFACT: decisions — <meeting>]`), appended into the existing `[CONTEXT]` block so
  the on-device, endpoint, and desktop paths stay one assembler. Selection persists per
  conversation (the chat keeps its grounding), not per recipe — the recipe's standing
  context (`manualContext`/zone/KB) stays what it is.
- **Hub hydration (the 15-11 pairing)** — when the run target is the desktop profile,
  the envelope ships **references, not bodies**: `/api/ask` gains
  `grounding: {meeting_ids, artifact_ids, expand}` and the hub hydrates from its own
  DB (it holds the full transcripts; the phone may hold truncated copies; DERP
  bandwidth stays sane). On-device/endpoint runs hydrate client-side from the synced
  records. Same envelope either way.
- **KB honesty rider** — replace the hint string with real hydrated KB content
  (bounded, gauge-priced) or an explicit "KB not hydrated on this device" marker.
  Never a hint pretending to be grounding.
- **Provenance on the answer** — the run record names what grounded it (the Phase-53
  source-cited spirit): the meetings/artifacts list rides the run artifact, so "why did
  it say that" has a receipt.
- **Verbs stay distinct** — drop-on-agent = input for one run; the envelope = grounding
  for a conversation; the recipe's standing context = authorship. Do not conflate
  (the Phase-47 lesson: KB ≠ context ≠ input).

## Acceptance criteria

- [ ] **The picker:** from an agent chat and from a run sheet, select ≥1 meeting and
      expand it — transcript and each bound artifact independently toggleable; the
      gauge re-prices live; the selection survives the conversation.
- [ ] **The envelope:** the run's prompt contains the selected blocks with provenance
      headers, via the ONE assembler — verified identical shape across on-device,
      endpoint, and desktop targets (host test on the assembly function).
- [ ] **Hub hydration:** a desktop-profile run sends references; the hub hydrates and
      the answer reflects content the phone never shipped (provable: a transcript
      section beyond the phone's truncation). Unknown ids refuse loudly.
- [ ] **KB honesty:** the KB block carries real content or an explicit non-hydrated
      marker — the hint string dies.
- [ ] **Provenance:** the run record lists the grounding (meetings + artifacts by
      name); the answer surface can show it.
- [ ] **Overflow:** a selection past the budget fails honestly at the gauge (pick
      less / summarize), never silent truncation mid-run.
- [ ] **The proof:** cross-country — an agent on the phone answers a question about a
      specific meeting's decisions, grounded via hub hydration, receipts in the run
      record. (Rides the 15-10/15-11 rig.)

## Build plan

1. **The assembler:** extract the envelope into a pure, host-testable function
   (blocks + provenance + budget) that `recipeRoleAndContext`/`runAssembled` call —
   the seam everything else plugs into.
2. **The picker UI:** composer/run-sheet attach → meeting list (synced records) →
   expansion rows (transcript / intel / artifacts) + the live gauge. Sim
   screenshot-verified (the 15-10 pre-upload rig).
3. **Hub:** `/api/ask` grounding param + server-side hydration + tests
   (manifest-of-ids in, refusal on unknowns, egress unchanged).
4. **KB hydration rider** + provenance on the run record.
5. **Docs + the cross-country proof.**

## Test plan

- Host (Swift): the pure assembler — ordering, provenance headers, budget refusal,
  KB marker. `swift test` (the app-target UI is sim-shot, not unit-tested).
- Hub: `uv run pytest -q -k ask` for the grounding hydration + refusals.
- Device: the cross-country grounded ask (acceptance row 7).

## Open questions (decide at build, not silently)

- **Transcript bounds:** whole-transcript grounding blows on-device budgets fast —
  default to intel summary + artifacts with transcript opt-in per meeting?
- **Live meetings:** can an in-progress meeting be grounding (partial transcript), or
  only finished records? (Lean: finished only for v1.)
- **Selection surface:** does the desk's multi-select (`__bundle__` routing) become
  the same envelope, unifying the drop-verb with the picker under one contract?

## Notes

- Sibling of [[story-11-agents-on-your-desktops-models]] — 15-11 gives the ask a
  desktop brain, 15-12 gives it your records. Built in either order; hub hydration
  lands best after 15-11's `/api/ask` touch.
