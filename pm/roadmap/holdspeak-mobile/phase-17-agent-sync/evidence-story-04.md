# Evidence — HSM-17-04: answer the coder (spoken / typed / dropped-context)

**Date:** 2026-07-04. **Proof style:** live end-to-end — a real Claude Code
session driven to a plain-text clarifying question, answered over the exact
wire calls the desk's Send button issues, the grounded reply acknowledged by
the coder, and the iPad desk flipping the primitive back to `working` without
a manual refresh. Plus a REAL TRANSPORT BUG found and fixed by the proof.

## What shipped

- **`CoderAnswer` (RuntimeCore/Companion)** — the one flow all three input
  modes converge on: `compose(reply:groundingTitle:grounding:)` assembles the
  reply + visible cited grounding into one payload; `send(...)` does
  select-then-send (the HSM-13-03 server-side-truth targeting: `POST
  /api/coders/select {agent, session_id}` → `POST /api/dictation/remote`);
  `approve(...)` sends the literal dialog keystroke `"1"` verbatim
  (`raw: true` — the hub pipeline must not rewrite a keystroke). A failed
  select never sends. 9 unit tests.
- **The composer (`DioCoderAnswer`)** — typed + **spoken** (`VoiceFillMic`,
  the app-wide speak-to-fill mic, on-device WhisperKit) + **dropped-context**:
  a `CoderGrounding` block (cited by source title, editable, removable) rides
  under the reply; the send button goes live when either part is non-empty;
  the **egress badge** (`Local + your desktop`) sits on the send row.
- **The keystone gesture, pointed at a coder** — in `drop(...)`, a content
  primitive dropped onto a WAITING coder opens the composer with the dropped
  primitive's `routableText` as grounding (instead of the KB routing cable).
  Nothing sends until the human sends.
- **The real inject** — `answerCoder`/`approveCoder` in the stage replace the
  optimistic stubs: demo mode (`HS_DESK_CODER`) stays offline-optimistic; live
  mode requires pairing, rides `CoderAnswer`, resolves the primitive only on
  `delivered: true`, and on any failure the question STAYS on the desk with an
  honest toast ("Desktop unreachable — question kept").

## THE TRANSPORT BUG (found live, fixed here)

The first inject reported `delivered: true` while the reply sat **unsubmitted**
in the coder's composer: `tmux_transport.send_text_to_pane` sent the named
`Enter` key as a second `send-keys` call, and current Claude Code TUIs
(observed on 2.1.201) drop a lone named-Enter — but submit on a **literal
`\r` byte**. Verified live both ways on the blocked session. Fix: the submit
is now `send-keys -l "\r"`. This also explains the session-long tmux quirk
("text + Enter in one call works, lone Enter doesn't"). The Phase-13 gate
predates this TUI behavior. Test updated (`test_tmux_transport.py`); the
remote-dictation batteries 140 green.

## The recorded live arc (session `cc9465ba`, screenshots/)

1. A live claude in tmux asked, in plain text: *"What does 'hs17' refer to,
   and what exactly is the proof meant to demonstrate?"* → the registry read
   `waiting` with the question captured verbatim.
2. **`hsm-17-04-before-waiting.png`** — the sim desk (paired to the live hub)
   showing "Claude · proof-repo" in the waiting accent.
3. The exact `CoderAnswer.send` wire calls: select → remote with the composed
   grounded payload (reply + `---` + "Context (from Phase 17 evidence): …").
   Response: `success: true, delivered: true`.
4. The coder **acknowledged both the reply and the grounding**: *"Got it. I'll
   write the README now as a proof walkthrough for hs17, mentioning the iPad
   desk and the Phase 17 evidence chain."* — and resumed working.
5. **`hsm-17-04-after-working.png`** — the desk flipped the primitive back to
   cobalt `working` on the next poll. No manual refresh.

## Honest notes

- Claude's `AskUserQuestion` **selector dialogs ignore typed text** (arrow-key
  navigation only): an injected text answer is delivered to the pane but not
  consumed; the trailing `\r` selects the highlighted option. Digit-keyed
  permission dialogs accept the raw `"1"` approve keystroke. Recorded as a
  follow-on for the 17-01 event taxonomy (the approval card should know the
  options) — the composer flow targets plain-text questions, the canonical
  Phase-13 shape, which is what this proof drove.
- The composer's spoken input (mic) and the on-glass drop gesture render in
  the build but need fingers: they are walked in HSM-17-06 with the rest of
  the phase's device beats.

## Tests + builds

- Swift: `CoderAnswerTests` (9: compose shapes, select-then-send order against
  the exact session, grounding in the one payload, failed-select-never-sends,
  send-failure surfaces, raw approve keystroke). Full SPM suite **458/8/0**;
  simulator app build **SUCCEEDED**.
- Python: `test_tmux_transport.py` updated for the literal-`\r` submit;
  `-k "tmux or remote_dictation or agent"` — **140 passed**.
