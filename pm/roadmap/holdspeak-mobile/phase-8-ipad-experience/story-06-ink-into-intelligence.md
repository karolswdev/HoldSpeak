# HSM-8-06 — Ink into intelligence (the magic pencil, involved)

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** done
- **Depends on:** HSM-8-02 (notebook), HSM-8-03 (linking + marked moments), HSM-8-04 (artifact review), HSM-6-02 (artifacts), HSM-7-03 (MIR seam)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The owner's words: the magic pencil notes must be "somehow involved" — not a
parallel scratchpad. Today HSM-8-02 stores ink and HSM-8-03 links it to a moment,
but the handwriting never touches the meeting intelligence. This story makes the
pencil a first-class input to the meeting record: what you write and mark by hand
shapes and attaches to the artifacts, on-device. This is the difference between a
notebook that sits next to the transcript and a notebook that is *part of* the
meeting's output.

## Scope

- **In:** weaving ink into the Phase-6/7 intelligence, fully on-device —
  (1) **handwriting-to-text** on a written note (PencilKit Scribble / on-device
  Vision recognition), so a scribbled note can be promoted to text;
  (2) **promote a note to an artifact**: a written/marked note becomes (or attaches
  to) an action item / decision / note on a `Segment`, through the contract types;
  (3) **marked moments feed extraction**: the HSM-8-03 one-gesture marks are passed
  as emphasis hints into the MIR seam (HSM-7-03) so what the user flagged by hand is
  weighted in what the model extracts; (4) the ink↔artifact links surface in the
  HSM-8-04 review so the user sees their handwriting reflected in the output.
- **Out:** cloud handwriting recognition (must be on-device — the air-gapped
  scenario HSM-8-05 forbids network). Full OCR of arbitrary documents. Autonomous
  creation of artifacts from ink without the user's confirmation (propose, never
  auto-commit). Rebuilding the artifact engine (Phase 6) or MIR (Phase 7).

## Acceptance criteria

- [ ] A handwritten note can be recognized to text on-device (Scribble / Vision),
      with the user able to accept/correct the recognition before it is used.
- [ ] The user can **promote a note or marked moment to an artifact** — an action
      item / decision / a note attached to a `Segment` — expressed in the Phase-0
      contract types and shown in the HSM-8-04 review (propose-and-confirm, never
      auto-committed).
- [ ] **Marked moments (HSM-8-03) influence extraction:** they are passed as
      emphasis hints through the HSM-7-03 MIR seam, and a test shows a marked moment
      measurably changes what is extracted vs. the same transcript unmarked.
- [ ] The review surface shows the link between a handwritten note/mark and the
      artifact it shaped (the pencil is visibly *involved*, not parallel).
- [ ] All of it works fully on-device (no network), so HSM-8-05's air-gapped loop
      keeps this richness with zero connectivity.

## Test plan

- Unit: handwriting-to-text over a fixture stroke set → recognized text (or the
  accept/correct path) without network; promote-to-artifact produces a schema-valid
  contract object; a marked-moment emphasis hint changes the MIR routing/extraction
  vs. unmarked (deterministic, model-free where possible).
- Device: write a to-do by hand in a real (offline) meeting, recognize it, promote
  it to an action item, and see it in review linked back to the ink (folded into
  the HSM-8-05 air-gapped walkthrough where practical).

## Notes / open questions

- Recognition is on-device only (PencilKit Scribble / Vision `VNRecognizeText`); the
  air-gapped gate (HSM-8-05) is the hard constraint — no cloud handwriting path.
- "Emphasis hints" reuse the desktop's selection-pin → grounding idea (desktop
  Phase 53): a user-flagged moment grounds/weights the extraction. Keep the hint a
  contract-level signal so it can ride sync (Phase 10) and stay compatible with the
  desktop.
- Propose-and-confirm only — promoting ink to an artifact is the user's call, never
  automatic (charter non-goal: the runtime never acts autonomously).
