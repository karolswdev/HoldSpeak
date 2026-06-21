# Final summary — HSM-13-04 Gate: Answer the Coder by Voice (Track N)

**Date:** 2026-06-20 · **Gate:** Track N (Gate 10) — **ACHIEVED**

> "We're coding away in our tmux session ... our iPad is pointed to the same server.
> Boom. The agent has a question. Now we know it on the iPad, and we can use our
> native functionality to send back a voice note ... and use all the rich plugins."

That scenario now works on real hardware. A coding agent's question, surfaced on a
physical iPad, **answered by a spoken voice note transcribed on-device**, delivered into
the live tmux coder session — on an explicit send, never autonomously.

## The result

- **Proven on metal (iPad Air M4 → on-device WhisperKit → live tmux coder):** the
  waiting question surfaced on the iPad; the owner spoke an answer; WhisperKit
  transcribed it on-device; it was delivered into the waiting agent's tmux pane via the
  inject path. The agent received an iPad-spoken answer — the gate's standard.
- **Real-metal caught a real bug:** the first delivery carried WhisperKit control tokens
  (`<|startoftranscript|>…<|endoftext|>`). Fixed with the pure, unit-tested
  `WhisperText.clean`; a **second real-metal run on the cleaned build delivered clean
  prose** ("…use postgres for the cache layer and the TTL is 5 minutes"). A no-LLM
  plumbing pass would have hidden the leak — the standing real-metal posture earned its
  keep again.
- **Built on the track:** the delivery wiring (`_deliver_remote_dictation`, the local
  tmux/type path), the `VoiceNoteComposer` (HSM-13-02), and the inject route (HSM-13-01)
  all carried the answer; this story added the on-device voice front end.

## Evidence

- [`evidence-story-04.md`](./evidence-story-04.md) — the voice closeout + the bug it caught.
- [`realmetal-log-gate.md`](./realmetal-log-gate.md) — the earlier delivery-half proof
  (typed answer → tmux coder) + the wiring.

## Tests

`swift test` 122/6-skip/0-fail (+5 `WhisperTextTests`); the voice app builds + signs for
device; delivery (5) + composer (10) host tests green.

## What remains in Phase 13 (not this gate)

- **HSM-13-03 — the Companion board:** surface *which* of several waiting coders an
  answer targets (`select`/`dismiss`/`pin`). This gate surfaced the single waiting
  question and delivered to it; multi-target selection is the phase's last story.

Phase 13 status after this gate: **3/4** (13-01 ✅, 13-02 ✅, 13-04 ✅; 13-03 remains).
The companion track's payoff — answer the coder by voice from the iPad — is real.
