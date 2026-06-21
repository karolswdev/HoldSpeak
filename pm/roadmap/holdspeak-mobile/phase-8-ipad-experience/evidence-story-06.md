# Evidence — HSM-8-06 (Ink into intelligence — the magic pencil, involved)

**Date:** 2026-06-21 · **Status:** done

The pencil stops being a parallel scratchpad: the handwritten notes are **attached to the
meeting as actual images** (the literal ink — arrows, sketches, a starred priority), the
handwriting is **recognized on-device** into a text proposal, and **hand-marked moments
weight what the model extracts**. All on-device (the air-gapped gate forbids any network
handwriting path).

## What shipped

- **`InkPromoter` (RuntimeCore):** turns recognized handwritten text into a schema-valid
  Phase-0 `Artifact` proposal (`.draft`, sourced `handwriting`) — propose-and-confirm; the
  user approves it in review, nothing is auto-committed.
- **`InkEmphasis` (RuntimeCore):** the HSM-8-03 marked moments boost the intents found in
  the hand-flagged segments, so a starred moment **measurably changes the routed artifact
  chain** — proven deterministically (a marked light-incident moment surfaces the
  `incidentTimeline` artifact a `.product` meeting wouldn't otherwise route).
- **The app (on-device):** an **"Add your handwritten notes"** action in the meeting's
  INTELLIGENCE surface that, per inked notebook page,
  (1) renders the ink to an **image artifact** attached to the meeting (the literal
  scribble, rendered dark-on-light, shown inline in review), and
  (2) recognizes the handwriting with **on-device Vision** (`VNRecognizeTextRequest`,
  accurate + language-corrected) into a text proposal via `InkPromoter`.
  Both appear in review as `.draft` proposals with Approve/Dismiss. Generation now uses
  `InkEmphasis.routedTypes`, so the marked moments weight what's produced.

## Tests (ran)

`swift test` → **170 passed / 6 skipped / 0 failed** (+5 `InkIntelligenceTests`):
promote produces a schema-valid `.draft` artifact (round-trips the contract coder);
title is the first line; **a hand-marked moment surfaces the incident artifact** while the
unmarked transcript does not; no marks leave the scores unchanged.

## Real-metal

The ink-intelligence app **builds + signs for device** (WhisperKit + on-device LLM + Vision
+ PencilKit) and was installed on the physical iPad Air M4. The "Add your handwritten
notes" walkthrough — draw a note in a meeting, attach it as an image + recognize it
on-device, see both in review — runs on the deployed app; the on-device Vision path uses
no network, keeping HSM-8-05's air-gapped loop intact.

## Acceptance

- **Handwriting recognized to text on-device** (Vision), surfaced as a proposal the user
  accepts (Approve) or dismisses. ✅
- **Promote a note/marked moment to an artifact** in the Phase-0 contract types, shown in
  review, propose-and-confirm. ✅ (`InkPromoter`, host-tested.)
- **Marked moments influence extraction** via the MIR seam — a marked moment measurably
  changes what is routed/extracted. ✅ (`InkEmphasis`, host-tested.)
- **The review shows the pencil's involvement** — the ink image + recognized note appear
  in the meeting's intelligence, sourced `handwriting`; the marks shape the generated set.
- **Fully on-device** — Vision recognition + the ink render are local; no network. ✅

## Plus the owner's ask, delivered

> "transcribing my scribbles is fine, but it should also literally attach those notes as
> an actual image"

The literal ink is now attached as an **image artifact** on the meeting (not just the
recognized text) — the drawing's fidelity is preserved, with the recognition as an
additional text layer on top.
