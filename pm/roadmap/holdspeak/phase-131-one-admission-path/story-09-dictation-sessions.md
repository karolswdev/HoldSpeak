# HS-131-09 — Dictation and transcription are admitted per session

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-01, HS-131-02, HS-131-07, HS-131-08
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

The shared `Transcriber` executes local Whisper directly for meeting
transcription, core dictation capture, and wake capture. Dictation's intent
classification, rewrite, compatibility fallback, local runtime, and mesh runtime
also call models outside inference admission. A continuous open mic can produce
many utterances, so top-level owner decisions per utterance would repeat
ceremony and violate the owner's "per sesh" ruling. Treating a meeting, wake, or
mic session as one model receipt would hide every actual invocation.

## Scope

### In

- Move every shared local Whisper execution in `holdspeak/transcribe.py`
  behind the authorized runner adapter, including MLX silent-audio
  preload/warmup at `:201-225` and ordinary `.transcribe()` dispatch at
  `:227-275,315-340`. Both are model invocations in the mechanical fence.
- If preload occurs while a meeting/dictation/wake session is being opened, make
  it an invocation child of that session. If preloading before a session, admit
  it as the authenticated runtime-service actor under the owner's explicit
  configured local-model/preload authority basis and exact deployment revision.
  Never fabricate an owner principal. Without a valid basis, defer warmup until
  first-session admission or refuse before invoking Whisper.
- Attach meeting transcription in
  `holdspeak/meeting_session/transcribe_loop.py:60-70` to the meeting session
  parent established by HS-131-08. Each transcription call is its own admitted
  invocation child.
- Admit one dictation session when mic authority is acquired. For a desktop
  hold gesture, each press/release capture is one session; for the browser's
  click-to-toggle open mic, the mic-open interval is one session containing
  multiple utterances.
- Treat a configured wake capture in `holdspeak/runtime/wake_glue.py:204-237` as
  a bounded wake/dictation session under the owner's configured wake authority.
  Its transcription is a child; any resulting typing or other effect keeps its
  existing separate effect admission.
- Capture immutable authority basis, insertion context/aim, a frozen routing and
  deployment plan, and cancellation in each session parent. The plan may contain
  distinct exact revisions for transcription, classification, rewrite, and
  punctuation; each invocation child names the one it executes.
- Route core capture in `holdspeak/runtime/dictation_capture.py:30-49,283-292`
  and every transcription, classification, rewrite, punctuation, local, cloud,
  compatibility fallback, and mesh provider call through the runner as an
  admitted invocation child continuing its session.
- Cover direct runtime seams in
  `holdspeak/plugins/dictation/runtime_openai_compatible.py:126-200`,
  `runtime_llama_cpp.py:134-169`, `runtime_mesh_relay.py:106-110`, and the intent
  router call in `plugins/dictation/builtin/intent_router.py:171`.
- At every lightweight child admission and claim, have the kernel validate that
  the parent session and authority are still live, unexpired, and unrevoked.
  Reuse the immutable authority basis without repeating an owner decision.
- Each fallback that reaches a provider creates a separate child and terminal
  receipt. Pure VAD, capture, buffering, and token streaming create no child.
- Session stop/cancel/expiry prevents new utterance children, reaches active
  provider work where possible, and blocks late text from delivery or rewrite.
- Preserve the click-to-toggle browser mic contract, hold-to-talk behavior,
  insertion idempotency, latency budget, and existing effect admission for text
  delivery.
- Keep audio, transcript prompt bodies, tokens, and dictated text out of the
  kernel journal; native dictation records remain the content authority.

### Out

- Mic UI redesign, gesture changes, or new pipeline controls.
- Admission per audio frame, VAD window, or token.
- Replacing the existing delivery effect kernel path.

## Acceptance criteria

- [ ] Desktop hold capture creates one admitted dictation session per capture;
  the browser click-to-toggle open mic creates one session across its utterances
  until closed.
- [ ] Every MLX preload/warmup invocation executes through the runner and ends
  in one terminal invocation receipt. A live-session preload is that session's
  child; a pre-session preload names runtime service as actor and the explicit
  configured local-model/preload basis, or defers/refuses before model dispatch.
- [ ] Shared local Whisper calls from meeting transcription, dictation capture,
  and wake capture each execute through the runner as an invocation child of
  their correct live session.
- [ ] Every actual transcription/classification/rewrite/punctuation provider
  call has one invocation child and one terminal invocation receipt, including
  fallback or retry dispatches.
- [ ] VAD, capture, buffering, and non-model computation create no invocation
  child.
- [ ] Every child admission and claim validates current session liveness,
  authority validity, expiry, and revocation through the kernel, captures its
  exact deployment revision, and does not repeat an owner decision.
- [ ] Stopping, revoking, expiring, or cancelling the session prevents new
  children and prevents late text or rewrites from landing.
- [ ] Wake-triggered and dictation text delivery retain their existing separate
  effect admissions and idempotency; inference admission does not duplicate the
  delivery act.
- [ ] A contemporaneous A/B using `scripts/measure_dictation_latency.py`, the
  fixed 16 kHz fixture, the same machine/model/backend/driver sink, 2 warmups,
  and 20 measured runs reports median and p95 release-to-landed. Phase 131 is no
  worse than its clean-fork control by more than `max(25 ms, 5%)` at either
  statistic.
- [ ] Kernel records contain no audio, dictated text body, prompt, or token
  stream.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_dictation_runtime.py` plus shared
  `Transcriber`, pre-session and in-session MLX preload, missing preload
  authority, session-liveness, child-cardinality, fallback,
  local/cloud/mesh, cancellation, and journal-privacy tests.
- Integration: `uv run pytest -q tests/integration/test_dictation_moment_of_truth.py`
  plus meeting transcription, wake transcription, a browser open-mic
  multi-utterance session, and a desktop hold session.
- Performance: run `scripts/measure_dictation_latency.py --warmups 2 --runs 20
  --typing-mode driver` contemporaneously on clean fork and story branch; extend
  its summary to p95 and evaluate the written median/p95 threshold.
- Manual / device: real browser mic and real model, one desktop hold session,
  two click-to-toggle open-mic utterances, one wake capture, cancellation before
  landing, and receipt inspection.

## Notes / open questions

The phase does not revive the old blanket exemption for Whisper or local models.
Article XI classifies a model invocation by what it does, not where it runs.
Session admission keeps the authority decision cheap without hiding child calls.
