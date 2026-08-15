# HS-132-04 — One utterance, one pipeline

- **Project:** holdspeak
- **Phase:** 132
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-132-05
- **Owner:** unassigned

## Problem

Every sentence spoken in the Speak room is processed twice. The WS final pass
already runs `process_transcript`
(`holdspeak/web/routes/system/voice.py:512-521`), and the open-mic leg
transcribes with `pipeline=true` (`web/src/lib/openMic.ts:68`,
`speakToFill.ts:141`); the deck then delivers via `/api/dictation/remote`
with no `raw` flag (`web/src/pages/cores/dictation/useSpeakDeck.ts:152`),
which re-runs the entire DIR pipeline
(`holdspeak/web/routes/dictation/pipeline.py:806-826`). The route's own
comment at `pipeline.py:706-711` calls re-running it "a lie (the rewrite is
not idempotent)" and provides `raw: true` for exactly this case. The result:
delivered text is a rewrite of a rewrite, two journal rows per utterance,
double latency.

Separately, the documented no-pipeline speak-to-fill seam
(`holdspeak/runtime/dictation_capture.py:345-356`: "a speak-to-fill is the
user typing with their voice... No journaling") is unreachable: the WS route
unconditionally pipelines the final (`voice.py:508-521`) and every desk
MicButton uses it (AskPanel, NoteEditor, KbEditor, DeskComposer,
RecipeEditor, and ten more), so dictating a note tag runs intent routing and
KB enrichment and can deliver words the user never said. The client flag
exists (`web/src/lib/speakToFill.ts:139-157` accepts `{pipeline:false}`) and
no caller passes it.

## Scope

### In

- Speak-room delivery sends `raw: true` for text that already carries a
  pipeline receipt; exactly one journal row per utterance.
- Field mics (speak-to-fill) request `pipeline: false` end to end, including
  the WS streaming path — a field fill transcribes without intent routing,
  enrichment, rewriting, or journaling.
- The dictate-for-delivery surfaces (Speak room, remote delivery) keep the
  pipeline exactly once.

### Out

- Pipeline stage changes; DIR-01 semantics; the runtime-down degradation
  behavior (ledgered separately in the backlog).

## Acceptance criteria

- [ ] One `process_transcript` execution and one journal row per Speak-room
  utterance, proven by test.
- [ ] A field mic fill performs zero pipeline stages and writes zero journal
  rows; the field receives the transcription verbatim.
- [ ] The Speak-room delivered text equals the single pipeline pass's output
  (no rewrite-of-rewrite).

## Test plan

- Focused unit/integration tests on `useSpeakDeck` delivery payload (vitest)
  and `/api/dictation/remote` raw handling, plus a WS-route test asserting
  pipeline/no-pipeline per requested mode.
- `HOME=$(mktemp -d) uv run pytest -q tests/ -k "dictation and (remote or voice)" --tb=short` (scoped).
