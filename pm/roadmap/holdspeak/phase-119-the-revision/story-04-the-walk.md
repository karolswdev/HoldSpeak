# HS-119-04 — The walk

- **Project:** holdspeak
- **Phase:** 119
- **Status:** done
- **Depends on:** HS-119-01, HS-119-02, HS-119-03
- **Unblocks:** --
- **Owner:** unassigned

## The thesis (the bar)

This is the Phase 118+119 proof. Phase 118 shipped nine stories of new
capability but its walk (HS-118-10) couldn't complete because
integrations were broken. Phase 119 fixed the regressions, upgraded the
mic, and revised the seed. This walk proves everything works together —
not in isolation, not in tests, but on the real hub with real mic, real
model, real viewport.

Every surface, every input path, every output path, every system
integration. If it shipped in Phase 118 or 119, it appears in this
walk.

**Articles served:** IX (proof over claim — nothing is done because its
code merged; it is done when it ran; real hub, real mic, real model,
real device, real viewport; evidence rides with the change),
VIII (native-grade craft — every glass is first-class; the walk covers
both desktop and mobile viewports), IV (voice as input — live mic
proof with click-to-toggle and streaming transcription).

## Deliverables

### Screenshot walk — 1440x900 (desktop)

1. **The desk.** Fresh seed: inference profiles, workbench, starter
   zones. No demo clutter.
2. **The inlet.** Workbench open, inlet visible, ready for input.
3. **@-autocomplete.** Type `@` in the inlet, verify zone
   autocomplete appears with starter zones.
4. **Grounding chips.** Drop a desk object onto the inlet, verify
   grounding chip appears.
5. **Sprite states.** Workbench in idle state, then processing
   state — verify sprite variants render.
6. **Artifact triage.** Pending-review artifact with accept/reject/
   rework controls visible.
7. **Presence.** Presence indicator showing connected activity (not
   "RECONNECTING").

### Screenshot walk — 393x852 (mobile)

1. **The desk.** Mobile viewport, seeded desk, objects visible and
   tappable.
2. **The inlet.** Workbench open, inlet visible, MicButton tappable.
3. **Mic active.** MicButton in listening state with pulse and
   waveform visible.

### Video proof

1. **Click-to-toggle mic with streaming transcription.** Click the
   MicButton, speak a sentence, verify streaming text appears in
   the field as Whisper processes chunks, click again, verify
   finalized text. Full cycle visible.
2. **Voice drawer resolution.** Speak a zone reference into the
   inlet, verify it resolves to a grounding chip.

### Live mic proof

1. **Correction cycle.** Speak a phrase, verify the dictation
   pipeline applies corrections (if corrections exist in the
   learning store). If no corrections exist, speak a phrase,
   manually correct it, speak the same phrase again, verify the
   correction was learned.
2. **Pipeline parity.** Speak via the browser mic, verify the
   returned text matches the quality of the hotkey path (both
   pass through `process_transcript`).

### Live inference proof

1. **Add item and run.** Add an item to the workbench via the
   inlet (typed or spoken instruction with @-referenced grounding).
   Run the workbench. Verify the conductor produces an artifact in
   `pending-review` state.
2. **Triage.** Accept the artifact. Verify it becomes a real desk
   object with provenance.

### System integration proof

1. **Presence.** Verify the presence system connects, shows
   activity, and does not freeze.
2. **WebSocket.** Verify events arrive when desk objects change.
3. **Meeting recorder.** Start a recording, stop it, verify
   transcript is produced (if hardware allows).
4. **Dictation hotkey.** Press the system hotkey, speak, verify
   corrected text arrives via desktop paste (if hardware allows).

### Evidence

- All screenshots captured via Playwright at the specified
  viewports against the real hub.
- All video captured as screen recording or Playwright trace.
- All live proofs documented with before/after state.
- All evidence captured via DW (`dw evidence capture`).

## What NOT to do

- Do NOT use seeded or mocked data for the walk. Everything runs
  on the real hub with real data created during the walk.
- Do NOT skip a proof because "it was tested in the story." The
  walk proves integration, not isolation. (Article IX.)
- Do NOT claim a proof that wasn't captured. Evidence rides with
  the change.

## Test plan

- This story has no automated tests of its own. It is the
  integration proof that the automated tests in stories 01-03
  predicted correctly.
- Every deliverable above is captured as evidence.
- The walk is complete when every deliverable has a captured
  artifact (screenshot, video, or documented proof) and no
  deliverable shows a failure.
