# HS-112-06 - The open mic

- **Project:** holdspeak
- **Phase:** 112
- **Status:** done
- **Depends on:** HS-112-02
- **Unblocks:** HS-112-05
- **Owner:** unassigned

## The thesis (the bar)

The owner's live rider on the charter: "I do want us to also use the
browser's mic when we're on the Desk... push to talk (key) behaves
exactly the same — but on the Desk natively? We open a microphone
request once, keep sending voice, use VAD and so on — so that we're
finally in a voice-first environment for god's sake." The bar: **the
Desk asks for the microphone ONCE, holds the stream open, and a VAD
segments speech continuously — spoken utterances arrive without any
key or button — while push-to-talk keeps behaving exactly the same.**
Voice is the Desk's ambient input, not a control you operate.

## Ground

- Today every capture is gesture-bound: `getUserMedia` is requested
  per hold inside `startCapture()` (`web/src/lib/speakToFill.ts:64`)
  and released on stop — a permission-and-teardown cycle per
  utterance, on the deprecated `ScriptProcessorNode`.
- The floor arbitration already has the right shape: the
  `VoiceTypingSession` lock (`holdspeak/voice_typing.py:29`) owns
  the audio floor with named owners; wake word already runs a
  continuous local listener with an armed capture window
  (`holdspeak/wake_word.py:48`, `runtime/wake_glue.py:147`) — the
  open mic is the browser-side sibling of that pattern.
- HS-112-02 gives this story its delivery half: once the Speak room
  posts through the real contract, VAD segments reuse the same
  route, journal, and receipts.

## Method

1. **One grant, one stream.** A Desk-level mic session: requested
   once, surfaced honestly (the mic state lives in the chrome — a
   lamp, not prose; egress badge rule applies), suspended not torn
   down between utterances. Replace `ScriptProcessorNode` with an
   `AudioWorklet` while the stack is open.
2. **VAD at the edge.** Client-side voice activity detection
   segments utterances (energy/hangover baseline; a small on-device
   model only if the baseline proves insufficient on the real desk).
   Segments flow through the HS-112-02 delivery contract with the
   same preview/type rule and idempotent delivery ids.
3. **The floor is still one.** The open mic is an owner on the
   existing arbitration model: push-to-talk (key or TALK) preempts
   it exactly as today; wake/meeting ownership refuses it by name.
   PTT behavior is byte-identical — pinned by the existing gesture
   tests.
4. **Off is real.** The open mic is opt-in per session, one verb to
   drop the stream entirely, and the lamp never lies — when it says
   closed, `getUserMedia` tracks are stopped, not muted.

## Test plan

- Live on the real desk: grant once, speak three separate utterances
  with silence between — three segments land through the delivery
  contract, no key touched, receipts journaled beside PTT entries.
- PTT regression leg: with the open mic live, hold the key and the
  TALK gadget — behavior identical to HS-112-02's proof (preemption
  pinned by test).
- The lamp legs: open/listening/segmenting/closed states shot at
  1440+393; the closed state verified by track state, not UI.
- Refusal legs in-flow: permission denied, floor owned by a meeting,
  endpoint unreachable mid-stream.
- No permission re-prompt across an hour-long session (stream
  suspend/resume, not re-request).
