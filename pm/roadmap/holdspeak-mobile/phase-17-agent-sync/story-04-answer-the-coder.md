# HSM-17-04 — Answer the coder: spoken / typed / dropped-context

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** todo
- **Depends on:** HSM-17-03 (the question is on the desk), the proven inject path
  (`/api/dictation/remote`, `RemoteDictationResult`, the Phase-13 answer-the-coder gate), the voice
  composer (`VoiceNoteComposer` / WhisperKit), the keystone routing gesture (`drop()` /
  `routableText`).
- **Unblocks:** HSM-17-05 (AI-draft is a fourth input into this same composer + inject).
- **Owner:** unassigned

## Problem

A blocked coder on the desk is only useful if you can answer it from there. Phase 13 already proved a
spoken answer can land in a live session. This story makes "answer the coder" a first-class desk action
with the three human-authored input modes, all converging on one inject.

## The interaction

From a waiting agent primitive's pull-out, **Answer** opens a composer with three ways in:

1. **Typed** — the plain path; type the reply.
2. **Spoken** — WhisperKit transcribes your reply (the `VoiceNoteComposer` flow), editable before send.
3. **Dropped context** — drag a meeting / artifact / note **onto the agent's question** to answer *from
   that*; the dropped primitive's `routableText` is attached as grounding the human can see and trim.
   (This is the keystone routing gesture, pointed at an agent instead of the AI core.)

Then: **review → approve → inject.** On send, the composed text goes to the live session via
`/api/dictation/remote` (target = that session), the egress badge shows it leaving the iPad for the Mac,
and on success the primitive returns to `working`.

## Scope

- **In:** the Answer composer (typed + spoken + dropped-context grounding); attaching/trimming dropped
  context; approve-then-inject to the specific session via the existing remote-dictation path; the egress
  badge; the primitive returning to `working` on a delivered answer.
- **Out:** AI-drafted answers (17-05 — a fourth input into this same composer); multi-session broadcast.

## Acceptance criteria

- [ ] From a waiting agent primitive, you can compose an answer by **typing** or **speaking** (Whisper),
      edit it, and inject it into that exact session; it arrives in the live coder.
- [ ] Dropping a meeting/artifact/note onto the question attaches its `routableText` as visible,
      trimmable grounding that is included in (or alongside) the injected answer.
- [ ] Inject is **explicit** (a deliberate send), shows the egress badge, and on success the agent
      primitive flips back to `working`; a failed inject surfaces an honest error, nothing silently lost.
- [ ] Never autonomous: no path sends without a human send action.
- [ ] Proven on real metal in HSM-17-06.

## Test plan

- Real metal: drive a live coder to a question; from the desk, answer by voice → confirm it lands and the
  coder continues; answer a second question by dropping a meeting artifact as context + a short typed
  note → confirm the grounding is present in what the coder receives.
- Unit: the composer assembles typed + dropped-context into one payload; the inject targets the correct
  `sessionId`; egress scope resolves correctly.
