# HS-52-04 — Dispatch wiring: match -> auto-approved actuator execute

- **Project:** holdspeak
- **Phase:** 52
- **Status:** done
- **Depends on:** HS-52-01, HS-52-03
- **Unblocks:** HS-52-05, HS-52-06
- **Owner:** unassigned

## Problem
The seam (HS-52-01), the store (HS-52-02), and the connectors (HS-52-03) exist; now the
dictation path has to actually decide "command or dictate" and, on a command, fire the
action through the reused executor without a per-fire prompt (config is the consent).

## Scope
- **In:**
  - In the carved module (HS-52-01), at the top, match the transcript (normalized,
    whole-utterance: case-folded, trailing punctuation stripped) against the enabled
    macros' keywords.
  - On a match: build the macro's `ActuatorProposal`, then run it through the reused
    `ActuatorExecutor` auto-approved: `db.actuators.record_proposal(...)` ->
    `transition_proposal(..., to_status="approved", actor="voice-dispatcher")` ->
    `executor.execute(proposal_id)` (the executor allows only the voice-macro connectors).
    Then **type nothing** and return.
  - On no match: fall through to the normal dictation pipeline (byte-identical).
  - Resolve the meeting-scoped persistence: a voice fire has no `meeting_id`/`window_id`,
    so give it a synthetic voice context (a stable "voice" session/window) rather than a
    fake meeting row. Decide and implement here.
  - Surface a runtime activity for a fired macro through the existing broadcast
    (`web_runtime.py:331-368`), e.g. "command: open terminal", so the fire is visible.
  - With macros off, the dispatch is inert and typed output is byte-identical.
- **Out:** the editor UI (HS-52-05).

## Acceptance criteria
- [x] An exact whole-utterance keyword match fires the macro's action through the bounded
      connector (auto-fired; the config is the consent) and types nothing.
      (`dictation_runner.dispatch_voice_command`; `web_runtime._transcribe_and_type`
      returns early on a result, never typing)
- [x] A non-keyword utterance dictates as normal; with macros off the dispatch is inert and
      the typed output is byte-identical. (`test_macros_off_returns_none`,
      `test_no_match_returns_none`; full suite's existing dictation transcription tests pass
      unchanged)
- [x] The non-meeting persistence context is resolved honestly: the actuator table is
      meeting-scoped (`actuator_proposals.meeting_id REFERENCES meetings(id)`), so a voice
      fire is **not** persisted there (no fake meeting). The guarded execution (connector +
      permission gate + bounded manifest) is fully reused; the fire is audited via the
      runtime-activity broadcast + the log. (See evidence for the reasoning.)
- [x] A fired macro emits a runtime activity ("command: <keyword>"); nothing is emitted on
      no-match / macros-off. (`test_activity_is_emitted_on_match`)
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Integration with an injected connector + a seeded macro: match-fires + audited,
  no-match-dictates, off-byte-identical (`uv run pytest -q -k "macro or dictation or
  actuator"`).

## Notes / open questions
- Auto-approval is the whole "you own the risk" model: the config is the approval, so the
  dispatcher approves its own proposal. Keep the audit trail honest (actor =
  "voice-dispatcher").
- Match is whole-utterance in v1; document the limitation in HS-52-06.
