# HS-93-05 — Your words never disappear

- **Project:** holdspeak
- **Phase:** 93
- **Status:** in progress — content-free event measurement, local text/audio
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
- [ ] Web, iPhone, and iPad preserve an editable draft through permission denial,
      missing model, bad token, unreachable hub, dead selected target, conflict,
      timeout, app backgrounding, and relaunch.
- [ ] Every failure names what failed and offers only applicable Retry, Copy,
      Keep as Note, choose alternate Runs-on target, or Setup actions.
- [ ] Dictation, permission, model, delivery, and recovery copy follows the
      factual failure structure in `copy-contract.md`; no apology, reassurance,
      product pitch, or mascot narration delays the retained draft and action.
- [ ] Successful local transcription and paired delivery each occur exactly once
      under retry/reconnect; a duplicate or silent remote fallback fails the
      story.
- [ ] Secure requires preview before basic commit, Normal follows the explicit
      preview preference, and YOLO commits without a HoldSpeak approval prompt;
      all three retain the same draft, exactly-once, destination, and failure
      guarantees on React and Swift.
- [x] Default Python/Web/Swift automation is bounded and excludes opt-in metal
      work by name; real-metal commands and prerequisites are explicit.
- [ ] Physical-device evidence records steps, decisions, elapsed time, audio
      route, model, destination, recovery outcome, and exact build without phrase
      content.

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
