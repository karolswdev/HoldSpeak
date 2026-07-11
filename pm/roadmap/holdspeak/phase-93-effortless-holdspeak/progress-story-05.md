# HS-93-05 progress record — Your words never disappear

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `1e6a28f3` plus the uncommitted HS-93-01 through
HS-93-04 working tree<br>
**After build:** current Phase-93 working tree; no commit identity claimed<br>
**Acceptance status:** in progress — content-free first-value measurement and
bounded default automation are complete. Recovery and deduplicated delivery are
implemented and automatically verified, but the complete real-fault,
control-mode, owner, and physical-device matrix remains open.

## What changed

The recovery path now has three independent checkpoints instead of treating a
successful request as the only durable truth:

| Boundary | Durable state | Confirmation that clears it |
|---|---|---|
| Capture → transcription, Web | one scope-keyed WAV in browser IndexedDB, bounded to 16 MB | the transcription request returns normally |
| Capture → transcription, flagship Apple app | one 16 kHz mono PCM16 file in Application Support, bounded to 16 MB | non-empty on-device transcription succeeds |
| Text → paired desktop effect | editable text plus an opaque delivery id on the sending device; a matching claim/Receipt on the hub | the named desktop returns a delivered terminal Receipt |

Web text editors use the small synchronous
[`durableDraft.ts`](../../../../web/src/lib/durableDraft.ts) primitive. First
Words, Dictation Try it, Ask, Persona chat, capability input, Coder replies, and
armed steering now write their device-local draft on every edit and restore it
after remount/relaunch. Coder voice input no longer sends directly from a mic
callback: it lands in an editable draft and requires the existing explicit Send
action. A failed send leaves that draft intact.

[`pendingVoice.ts`](../../../../web/src/lib/pendingVoice.ts) adds the bounded
pre-text checkpoint. `stopAndTranscribe` saves the WAV before calling the hub;
the shared mic control detects it after remount and retries it before opening a
new capture. Retained audio stays recoverable even if the relaunched browser can
no longer open a microphone. Browsers without IndexedDB retain the live draft
and use a page-lifetime memory fallback; that fallback is not credited as
relaunch proof.

The flagship Apple Dictate model now persists the editable words, named
destination, raw/processed flag, and delivery id through
[`DictationRecoveryDraft.swift`](../../../../apple/Sources/Contracts/DictationRecoveryDraft.swift).
On release, it also atomically checkpoints the captured PCM before starting
WhisperKit. Relaunch shows either the editable text draft or a recovered-audio
state with Retry. Successful transcription removes the PCM; confirmed desktop
delivery removes the text draft. This implementation does not yet claim an
active-capture checkpoint before release.

## Observed, content-free first value

Database schema 21 adds `first_value_events`. Starting an attempt writes the
first `dictation_requested` event in the same transaction. Later events accept
only an allow-listed kind and the exact opaque shape
`<attempt>:<sequence>:<kind>`; a phrase cannot be smuggled into the id. The table
has no text, phrase, transcript, content, or audio column.

Steps and decisions are derived from the stored events, elapsed time is derived
from server timestamps, duplicate event ids are idempotent, and an event after
finish is refused. New attempts ignore client-supplied `steps` and `decisions`.
The React tracker sends only destination, bounded event kind/id, outcome, and a
bounded failure category.

The production evidence runner deliberately submitted false client counters of
20/20 after only one observed owner step. The returned Receipt reported one
step, zero decisions, two events, and server-derived elapsed milliseconds.

## Paired delivery identity

The Apple client mints a stable delivery id before its first paired request and
persists it beside the editable draft. The hub hashes the exact text, target,
target mode, and raw flag, then claims that id before pipeline or typing work:

```text
new id + request → pending claim → effect → terminal Receipt
same id + same request + terminal Receipt → cached Receipt; effect is not called
same id + different request → 409 conflict; effect is not called
ambiguous hook/Receipt failure → 425 pending; retry never replays the effect
```

Known pre-effect failures become terminal failures, allowing an explicit retry
under a new id. Unreachable and pending outcomes keep the existing id. The
native readback is keyed by delivery id, so a cached reconnect response cannot
append a second line. Older callers that omit `delivery_id` retain their legacy
wire shape.

This is a narrow delivery ledger, not a background queue. An indeterminate
effect is held pending instead of being guessed successful or silently replayed.
That choice preserves at-most-once effect semantics and keeps the words on the
sending device while the outcome is unresolved.

## Factual failure and recovery actions

React uses one bounded `DictationFailure` contract for permission, model,
token, reachability, target/delivery conflict, transcription, timeout, no
speech, and unknown failures. First Words and Dictation Try it place the retained
editor before applicable Retry, Copy, Keep as Note, and Setup actions. Shared
voice-to-fill controls render the same factual cause and expose retained-audio
Retry only when a checkpoint exists.

The Apple Dictate recovery card keeps an editable text editor with Retry, Copy,
and Setup. It distinguishes rejected credentials, unreachable desktop,
known delivery conflict, indeterminate pending delivery, missing local model,
no speech, recovered draft, and recovered audio. The exhaustive real-fault
action matrix and alternate Runs-on path remain acceptance work.

## Bounded verification lanes

`pytest` now skips every `metal` test unless `--run-metal` is explicit, and CI's
ordinary end-to-end selection names `e2e and not metal`. The hardware command,
microphone/PortAudio/model prerequisites, active-target warning, and phrase-free
evidence fields are documented in the dictation guide. Web Vitest is capped at
two workers; this turned a demonstrably overcommitted host into a stable default
gate. Swift live-endpoint, download, and model proofs remain named opt-ins while
the normal package suite skips them.

## Production Web evidence

[`phase93_dictation_recovery_evidence.py`](../../../../scripts/phase93_dictation_recovery_evidence.py)
boots a real isolated `MeetingWebServer`, serves the production Web bundle, and
uses the real first-value and paired-delivery routes. Only the desktop typing
hook is an in-process recorder. Browser captures use synthetic typed text; they
are implementation evidence, not real-microphone or physical-device evidence.

| Evidence | What it proves |
|---|---|
| [First Words after relaunch](./evidence/hs-93-05/after-web-first-words-relaunch.png) | the local editor restores the exact synthetic draft and names the recovery |
| [Dictation timeout](./evidence/hs-93-05/after-web-dictation-timeout.png) | a 504 is rendered as a factual timeout; the editor and applicable Retry/Copy/Keep actions remain |
| [Dictation after relaunch](./evidence/hs-93-05/after-web-dictation-relaunch.png) | the same synthetic draft remains editable after reload |

The same runner sends one raw paired request twice with one delivery id. Both
responses succeed, the second is marked deduplicated, and the desktop hook is
called exactly once.

## Verification completed

| Lane | Result |
|---|---|
| First-value, delivery repository/routes, schema, native contract, and lane-policy Python slice | 102 passed |
| Ruff on changed recovery production/tests/evidence code | passed |
| Full Web `npm run check`, NVM Node 22.21.0 | architecture guard passed for 109 source files; typecheck passed; 29 files / 155 tests passed; production build passed |
| Full Swift package | 544 passed, 9 skipped, 0 failures |
| Flagship simulator app build | generated 147-source project; `HoldSpeakMobile` Debug iPhoneSimulator build succeeded for arm64 and x86_64 |
| API-backed production evidence runner | event-derived counters, elapsed time, one-effect reconnect, timeout retention, and two relaunch captures passed |
| Product-copy census | 3,919 candidates; 0 violations |

The flagship build retains existing deprecated-API/concurrency warnings in
unrelated app paths. Vite retains the existing mixed static/dynamic `ask.ts`
chunk warning. Neither is a build failure.

## Acceptance still required

HS-93-05 remains open. Required evidence still includes:

- a real microphone and local model on production Web, physical iPhone, and
  physical iPad, including interruption while capture is still active;
- permission denial, missing model, rejected token, unreachable hub, dead
  selected target, conflict, timeout, background/relaunch, and one exactly-once
  canary across every applicable surface;
- alternate Runs-on, Keep as Note, and action-applicability parity where the
  platform supports them;
- Secure/Normal/YOLO behavior from HS-93-07 with the same retention,
  destination, and delivery guarantees;
- owner-observed steps, decisions, elapsed time, audio route, model,
  destination, outcome, device/build provenance, and no dictated phrase.

HS-93-02 is also still open at its owner/physical evidence gate. Synthetic
typed text, simulator compilation, and source-level audio contracts do not
substitute for any of these observations.
