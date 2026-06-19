# Phase 9 — iPhone Experience

**Status:** planning (scaffolded 2026-06-18). Track J of the Council
Implementation Charter. The pocket Platform Host (Layer 4): the iPhone app that
delivers the charter's mobility promise — walk in, open, press Record, leave with
artifacts, no laptop.

**Last updated:** 2026-06-18 (scaffolded — stories HSM-9-01..04 stubbed from
charter Track J; no work started).

## Goal

Build the iPhone SwiftUI host over the Runtime Core for the pocket workflow:
Quick Capture (one-tap voice note), Meeting Capture (record → transcribe → queue
for intel), a Review Queue, and Voice Notes. The phase passes when the pocket
workflow is complete on an iPhone (Tier-2: iPhone 17 Pro Max) — the Track J gate.
Like the iPad host, it is thin: it presents the Runtime Core, it does not own
business logic. iPhone defaults are Whisper Base + a 4B LLM.

## Scope

- **In:** Quick Capture — one-tap voice note (HSM-9-01); Meeting Capture — pocket
  recording → transcribe → queue for intel (HSM-9-02); the Review Queue surface
  (HSM-9-03); Voice Notes + the pocket-workflow gate closeout (HSM-9-04).
- **Out:** the iPad-specific PencilKit notebook (Phase 8). Sync (Phase 10). The
  engines (Phases 2–7). Business logic in views. Hardening (Phase 11).

## Exit criteria (evidence required)

- [ ] Quick Capture records a voice note in one tap and it lands in the runtime
      (HSM-9-01).
- [ ] Meeting Capture records a meeting, transcribes it, and queues it for intel
      processing, all from the phone (HSM-9-02).
- [ ] The Review Queue shows captures and their processing state and opens a
      captured meeting's artifacts (HSM-9-03).
- [ ] **Track J gate — the pocket workflow is complete:** walk-in → record →
      leave → artifacts appear, proven end to end on a real iPhone, evidenced by a
      device walkthrough (HSM-9-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-9-01 | Quick Capture | backlog | [story-01](./story-01-quick-capture.md) | — |
| HSM-9-02 | Meeting Capture | backlog | [story-02](./story-02-meeting-capture.md) | — |
| HSM-9-03 | Review Queue | backlog | [story-03](./story-03-review-queue.md) | — |
| HSM-9-04 | Voice Notes + pocket closeout | backlog | [story-04](./story-04-voice-notes-pocket-closeout.md) | — |

## Where we are

Just scaffolded. The iPhone host reuses the same Runtime Core and view-model
patterns the iPad host (Phase 8) establishes, retargeted to a one-handed, pocket
form factor and the Tier-2 model defaults (Base/4B). The four stories follow
Track J's feature list (Quick Capture, Meeting Capture, Review Queue, Voice
Notes) and end on the pocket-workflow gate. Next: HSM-9-01 once Phases 2–3 are
callable; the artifact-bearing Review Queue depth wants Phase 6.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Tier-2 iPhone can't run the 4B model + Whisper Base within thermal/memory budget for a real meeting | high | Lean on the Phase-5 per-device defaults (4B) + Phase-3 Base; deferred/queued intel (process after capture) rather than live, so capture never blocks on inference | A pocket meeting can't be processed on iPhone even deferred — escalate to the model tier / Mode B (homelab) as the iPhone default |
| Pocket UX tempts business logic into the view for speed | medium | Reuse the Phase-8 view-model seams; the iPhone host is a second thin presentation of the same core | A view holds capture/transcribe/intel state — move it to the core |
| Background/locked-screen recording needed for "in your pocket" but not configured | medium | Decide the background-audio posture (carried from Phase 2) before HSM-9-02; state what the gate proves | The pocket workflow only works with the screen on — revisit the background-audio posture with the owner |
| Review Queue needs Phase 6 artifacts that lag | medium | Build capture + queue first; gate the artifact-review depth on Phase 6; show processing state honestly until then | The queue shows fake artifacts because Phase 6 isn't done — sequence after Phase 6 |

## Decisions made (this phase)

- 2026-06-18 — The iPhone host is a thin SwiftUI Platform Host (Layer 4) over the
  same Runtime Core as iPad, retargeted to the pocket form factor and Tier-2
  defaults (Whisper Base + 4B LLM) — charter Architecture §Principle + local-model
  strategy.

## Decisions deferred

- Live vs. deferred intel on iPhone (process during capture vs. queue and process
  after) — trigger: HSM-9-02 — default: deferred/queued processing so capture is
  never blocked by inference on the thermally-tighter Tier-2 device.
- Background / locked-screen recording posture — trigger: HSM-9-02 — default:
  inherit Phase-2's posture; revisit if the gate needs screen-off recording.
- Whether iPhone defaults to Mode A (4B local) or Mode B (homelab) out of the box
  — trigger: HSM-9-02 / Phase-5 thermal findings — default: Mode A with 4B; Mode B
  offered if local proves too tight on Tier-2.
