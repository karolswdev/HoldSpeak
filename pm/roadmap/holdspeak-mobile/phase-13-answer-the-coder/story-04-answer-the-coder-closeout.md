# HSM-13-04 — Answer-the-coder gate closeout

- **Project:** holdspeak-mobile
- **Phase:** 13
- **Status:** in-progress (2026-06-20 — delivery wiring real + the device→coder loop
  proven on real metal from a physical iPad; the **native on-device-voice** leg and
  the HSM-13-03 board surfacing remain. See [realmetal-log-gate](./realmetal-log-gate.md))
- **Depends on:** HSM-13-01, HSM-13-02, HSM-13-03
- **Unblocks:** — (Track N gate; the companion track's payoff is proven here)
- **Owner:** unassigned

## Problem

The whole track exists for one moment, and it has to be proven on the metal the
owner described: a real coding session, a real agent question, answered by voice
from a real iPad, landing back in that session. This story is the Track N gate —
the end-to-end walkthrough — with the never-autonomous guarantee held throughout.

## Scope

- **In:** a real-hardware walkthrough — a coding agent running in a tmux session
  with HoldSpeak hooks installed, pointing at the desktop server; a physical iPad
  Air M4 pointed at the **same** server; the agent raises a question; the iPad's
  Companion board surfaces it (HSM-13-03); the user answers with a native voice note
  (HSM-13-02); the answer is delivered through the inject path (HSM-13-01) into that
  coder session, on an explicit send. Evidence captured and `final-summary.md`
  written; Phase 13 closed (or the device step explicitly deferred with a ready
  script if the iPad is locked).
- **Out:** new feature work (this is the closeout of 13-01..03). Hardening scenarios
  (Phase 11). Multi-user / multi-session orchestration beyond picking one target.

## Acceptance criteria

- [~] End to end on real hardware: agent question (tmux + hooks → server) → surfaced
      on the physical iPad → answered by a native voice note → delivered into that
      coder session, evidenced by a device walkthrough (screenshots/log committed).
      *(Proven: a real Stop-hook awaiting session → an answer originating on the
      physical iPad → delivered into a live tmux coder pane (`tmux capture-pane`
      committed in realmetal-log-gate). Not yet: the **native voice note** (iPad sent
      typed text; needs on-device Whisper) and the HSM-13-03 board surfacing.)*
- [x] **Never autonomous:** the answer is delivered only on the user's explicit
      send, to the target shown in the board — demonstrated in the walkthrough (no
      auto-delivery path exercised). *(`_deliver_remote_dictation` fires only on the
      POST and **raises** rather than inventing a target; the composer delivers only
      from `.review` on an explicit send. No autonomous path exists.)*
- [~] **Rich-pipeline proof:** the delivered answer shows a pipeline transform
      (a correction/block/plugin applied), not raw transcript — captured in the
      evidence. *(The route runs the rich pipeline — proven in HSM-13-01; a live
      delivery with a configured correction applied is still to capture.)*
- [ ] `final-summary.md` records the gate result + evidence + deferrals;
      `current-phase-status.md`, this README's phase index, and the program README
      "Last updated" line are updated per the operating cadence. *(Cadence docs
      updated now; `final-summary.md` is written when the gate closes — i.e. once the
      iPad answers by voice.)*

## Test plan

- Device: the full walkthrough above on the unlocked iPad + a real desktop running a
  real waiting agent session (the `.43` homelab or a dev Mac, per the standing
  real-metal posture); capture screenshots and a short log (a build is not
  validation — the agent receiving the answer is).
- Regression: `swift test` green; the Python route tests (HSM-13-01) green.

## Notes / open questions

- Real-metal posture (standing rule): prove on a real endpoint/session, not a
  no-LLM plumbing pass — a plumbing-only run can hide a silently-broken delivery.
  Control-vs-treatment if the delivery's effect is in doubt.
- Device-gated: needs the iPad unlock + a reachable desktop with a live agent
  session. If blocked, host-prove every seam and stage the device step with a ready
  script (mirror HSM-5-06 / the Phase-56 macOS click) — but the gate is not "done"
  until the agent actually receives an iPad-spoken answer.
- This is the emotional close of the companion track; write the `final-summary` to
  show the owner's scenario working, not just tests passing.
