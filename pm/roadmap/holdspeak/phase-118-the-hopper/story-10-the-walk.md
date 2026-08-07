# HS-118-10 — The walk

- **Project:** holdspeak
- **Phase:** 118
- **Status:** backlog
- **Depends on:** HS-118-01, HS-118-02, HS-118-03, HS-118-04,
  HS-118-05, HS-118-06, HS-118-07, HS-118-08, HS-118-09
- **Unblocks:** --
- **Owner:** unassigned

## The thesis (the bar)

Every surface this phase touches must hold up on the real device,
with a real mic, real model, and real viewport. The walk is a
Playwright screenshot sequence + video trace against the real hub.
It proves the inlet, the @-autocomplete, the grounding chips, the
voice resolution, the output minting, the artifact triage, the
sprite state system, and the browser mic pipeline all render and
behave correctly at both viewports.

Static screenshots prove layout. Video traces prove animation and
transitions. Live mic capture proves the browser pipeline. Together
they constitute the Article IX evidence: honest proof on real metal.

**Articles served:** IX (honest proof — real hub, real mic, real
model, real device, real viewport).

## Deliverables

1. **Screenshot walk at 1440x900 (desktop).** Capture:
   - The desk with workbench sprites showing state variants:
     `idle`, `pending` (CSS hint pulse), `running`, `fresh`.
   - WorkbenchWindow open with the inlet visible (empty state).
   - Inlet with grounding chips from a drop (at least 2 chips).
   - Inlet with @-autocomplete popover open showing zone matches.
   - Inlet after voice resolution: chips from spoken zone names,
     full transcript visible in field.
   - Item card with minted artifact link, egress chip, and
     `pending-review` indicator.
   - Triage strip on item card: Accept / Rework / Reject chips.
   - Item card after Accept: triage strip gone, "Accepted" chip.
   - Item card after Rework: refinement input visible.
   - Batch triage section: "N outputs awaiting review."
   - Zone rename collision: inline error on duplicate name.
   - Runs wing with run history showing egress and model.
   - Memory wing with entries.
   - Sprite state CSS hints on non-Pixi surfaces (dashboard cards,
     window title bars).

2. **Screenshot walk at 393x852 (mobile viewport).** Capture the
   same surfaces at mobile width. Verify:
   - Inlet fills width, chips scroll horizontally.
   - Autocomplete popover doesn't overflow viewport.
   - Item cards and triage strips are legible and tappable.
   - Batch triage section wraps correctly.
   - Config strip is compact.

3. **Video trace for animated state.** Playwright trace (or screen
   recording) capturing:
   - Workbench sprite state transitions on the desk canvas: idle →
     pending (alpha 0.7) → running (alpha pulse) → fresh (green
     tint flash) → idle. These use the placeholder tints from
     HS-118-07, not dedicated assets.
   - CSS sprite-pulse animation on `sprite-active` elements in
     non-Pixi contexts (dashboard cards, title bars).
   - Voice resolution: grounding chips animate in with accent flash.
   - Reduced motion: all animations suppressed.

   Use a screen recording (exported video file), not a Playwright
   trace alone. A trace records diagnostics but is not an
   owner-reviewable animation proof. The video is the evidence;
   the trace is optional supplemental debugging data.

4. **Live mic proof.** With a real microphone:
   - Create a correction in the learning store (e.g. teach
     "HoldSpeak" → "HoldSpeak" capitalization). Then speak a phrase
     containing the corrected term into the inlet mic. Verify the
     browser pipeline returns the corrected form. This is a
     non-conditional proof — the correction is created during the
     walk, not assumed to exist.
   - Speak a zone name, verify grounding chip appears.
   - Verify mic floor authority: only one mic active at a time
     (browser mic and hotkey mic don't conflict).

5. **Live inference proof.** With a local inference target:
   - Add an item via the inlet with grounding.
   - Run the workbench.
   - Verify the agent prompt contains hydrated grounding content.
   - Verify the result mints a `pending-review` artifact.
   - Accept the artifact via triage.
   - Verify the artifact appears in the desk primitive list.

6. **Evidence file.** All screenshots, video traces, and mic/
   inference proof collected into `evidence-story-10.md` with
   viewport label, description per shot, and Delivery Workbench
   evidence capture commands. Assets stored under
   `assets/hs-118-10/`.

## What NOT to do

- Do NOT use seeded or mocked data. Start the real hub, create real
  workbenches, drop real primitives, run real local inference.
- Do NOT simulate the mic. Use a real microphone with real speech.
- Do NOT substitute Playwright viewport emulation for a real mobile
  device walk. Article IX requires a real device. If no mobile
  device is available, the mobile leg is deferred to a follow-up
  — it is not satisfied by emulation. Document the gap explicitly
  in the evidence file.

## Test plan

- `npx playwright test` or equivalent — screenshot capture at both
  viewports against the running dev server.
- Every screenshot reviewed for: correct layout, correct typography
  (mono throughout), correct color tokens (no hardcoded colors),
  accent treatment on interactive elements, readable text at both
  sizes, no horizontal overflow.
- Egress chips visible and correctly colored on all surfaces showing
  inference results.
- Video trace reviewed for: smooth transitions (no jank), correct
  animation timing, reduced-motion compliance.
- Mic proof reviewed for: correct transcription, pipeline processing,
  zone name resolution, floor authority.
- Evidence captured via `.githooks/dw evidence capture`.
