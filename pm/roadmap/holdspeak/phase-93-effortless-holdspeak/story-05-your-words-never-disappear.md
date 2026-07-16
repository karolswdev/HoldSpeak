# HS-93-05 — Your words never disappear

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
  recovery, reconnect-safe delivery identity, bounded default lanes, production
  Web implementation evidence, and automated cross-client verification are
  complete; full fault matrix, control-mode, owner, and physical-device evidence
  remain open
- **Depends on:** HS-93-02, HS-93-03
- **Unblocks:** HS-93-08, HS-93-09
- **Owner:** unassigned
- **Progress:** [implementation record](./progress-story-05.md)

## Problem

Dictation has strong recovery seams but no physical proof across Web and native,
and first-value counts are currently fixed client assertions. The daily magic
must survive permission, model, token, network, target, and delivery failures
without losing the user's words or lying about success.

## Scope

- **In:** Honest first-value instrumentation; local draft persistence for First
  Words, Dictation, native paired delivery, and Desk voice-to-fill; exact failure
  categories and Retry/Copy/Keep/Setup actions; exactly-once delivery; real
  microphone/model/token/network/conflict matrix; bounded canonical test lanes
  separating metal tests from default automation.
- **Out:** Rewriting Whisper backends, changing hotkey semantics without owner
  evidence, or storing phrase content in metrics.
- **Paths:** setup/onboarding records, transcription and delivery routes/runtime,
  Web FirstWords/Dictation/speak-to-fill, Swift Dictate model/view and desktop
  client, pytest markers/CI, UAT dictation scenarios, and security docs.

## Acceptance criteria

- [x] First-value measures derive from observed interaction events and elapsed
      time, not fixed success payloads; phrase content never enters measurement.
- [x] Production Web preserves an editable draft through permission denial,
      missing model, rejected token, unreachable hub, delivery conflict,
      timeout, and reload, proven by the forced-fault matrix runner with the
      failure copy asserted per fault; the physical iPhone/iPad legs are
      candidate-Y scope.
- [x] Every failure names what failed and offers only applicable Retry, Copy,
      Keep as Note, alternate Runs on, and Open Setup actions — the
      applicability mapping is implemented and component-tested, and the
      alternate Runs-on path re-runs through the real settings seam.
- [x] Dictation, permission, model, delivery, and recovery copy passes the
      census failure-facts rule (what failed, what is retained, destination
      when relevant, next action).
- [x] Successful local transcription and paired delivery each occur exactly
      once under retry and reconnect: same-id replay deduplicates to one
      effect, changed payload refuses, an indeterminate hook stays pending
      without replaying, and a failed receipt can never be upgraded.
- [x] Secure requires preview before basic commit, Normal follows the explicit
      preference, and YOLO commits without a HoldSpeak prompt — hub-resolved
      policy with no private client matrix, proven by hub and Web component
      tests including exactly-once token-bound commit and draft-retaining
      failed commit.
- [x] Default Python/Web/Swift automation is bounded and excludes opt-in metal
      work by name; real-metal commands and prerequisites are explicit.
- [x] Machine evidence records the forced-fault walks with screenshots and
      exact failed-request assertions; the physical-device provenance records
      (real microphone, audio route, interruption during active capture) are
      candidate-Y scope.

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the real-microphone production walks and physical iPhone/iPad fault matrix
move verbatim to [BACKLOG candidate Y](../BACKLOG.md) and are not claimed
here.

## Test plan

- **Unit:** instrumentation state machine, draft persistence, idempotency,
  failure-category/action mapping, no-content metrics, and marker guards.
- **Integration:** setup/transcription/delivery routes, Web component flow,
  paired Swift provider, reconnect/retry, and bounded CI lanes.
- **Manual / device:** Real microphone on production Web, iPhone, and iPad;
  execute every forced failure plus one canary delivered exactly once.

## Notes / open questions

The story may lower steps or decisions only after capturing a real baseline.
Do not optimize a hardcoded counter.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
