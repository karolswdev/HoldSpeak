# Evidence - HS-200-05

- **Story:** HS-200-05 - Prove physical voice capture, correction, and custody
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T02:50:34Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.gFqX1WUXKJ PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_voice_custody.py tests/integration/test_phase200_voice_custody.py tests/unit/test_desktop_type_text_kernel.py tests/unit/test_transcriber_init_race.py tests/integration/test_setup_first_dictation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7582fcb3b45d36f7647fc1bccada195934fa9635

```text
.................................................................        [100%]
65 passed in 26.81s
```

### Captured run — 2026-09-19T02:51:11Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.u81juekNlq PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/e2e/test_hs200_voice_custody_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7582fcb3b45d36f7647fc1bccada195934fa9635

```text
...                                                                      [100%]
3 passed in 29.73s
```

### Captured run — 2026-09-19T02:51:51Z

- **Command:** `bash -c cd web && npx vitest run src/pages/cores/dictation/__tests__/speakMicOwnership.test.tsx src/pages/cores/dictation/__tests__/hotkeyCustody.test.tsx 2>&1 | grep -E "Test Files|Tests "`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7582fcb3b45d36f7647fc1bccada195934fa9635

```text
 Test Files  2 passed (2)
      Tests  16 passed (16)
```

## 1. What the machine proved (re-run tonight, 2026-09-19)

Eighty-four tests, all captured above on this worktree's tip (index tree
`7582fcb3b45d36f7647fc1bccada195934fa9635`), all green:

- **65** Python tests — `tests/unit/test_phase200_voice_custody.py`,
  `tests/integration/test_phase200_voice_custody.py`,
  `tests/unit/test_desktop_type_text_kernel.py`,
  `tests/unit/test_transcriber_init_race.py`,
  `tests/integration/test_setup_first_dictation.py`.
- **3** browser tests — `tests/e2e/test_hs200_voice_custody_glass.py`
  (the permission-state faces whose shots sit in `assets/story-05-shots/`).
- **16** web-unit tests — `web/src/pages/cores/dictation/__tests__/speakMicOwnership.test.tsx`,
  `web/src/pages/cores/dictation/__tests__/hotkeyCustody.test.tsx`.

What those tests establish, at the level ACCEPTANCE.md calls *deterministic tests*
(state, command, failure and interface behavior — never physical capture):

- the hotkey delivery path issues exactly one typing call, with `source: hotkey`
  and the target fields on the receipt, and never retries;
- the browser capture route's microphone ownership: the floor refusals by name,
  one journal row per utterance, the delivery performed once;
- the four failure shapes and their loss rules as the capture contract writes them
  (silence is not an error; a floor taken mid-utterance discards the partial by
  contract; a client disconnect keeps the words);
- one correction saved and applied by the existing matcher with honest counts, and
  a replay that moves no count;
- custody across a re-open of the data root, and a durable delivery claim that
  parks `pending` rather than typing twice;
- the two four-week-dead defects found on 2026-09-08 (`6716dc10`) stay fixed: the
  MLX transcriber-reuse race that killed the hub process, and the desktop-executor
  warrant validator that refused every signed warrant.

The attended census runner `tests/e2e/live200_voice_walk.py` was **not run tonight**.
It needs a live hub on the owner's desk; nothing in this evidence file comes from it.

## 2. What the owner accepted (ruling of 2026-09-19) — accepted, not observed

The owner ruled, verbatim:

> all walks may be considered as passed.

That ruling closes this story. Usefulness and acceptance are his judgment. It is
an **acceptance**, not an observation: no one performed or watched the remaining
physical legs, tonight or since. Under ACCEPTANCE.md's evidence levels these
criteria carry the *Owner work* level and specifically **not** *Physical/runtime
proof*.

Each acceptance criterion, and what actually stands behind it:

| Criterion | Machine half | Physical half | Standing tonight |
|---|---|---|---|
| A physical hotkey dictation reaches the intended target and leaves its actual receipt | proven by tests above | **observed once on 2026-09-08** by the owner's own hand over Screen Sharing — five utterances, all `source: hotkey`, zero warrant refusals, words landing in the focused application (recorded at `current-phase-status.md:294-300`; recorded by that session, not re-observed or re-recorded tonight, and no captured log or shot of it ships in this repo) | satisfied; the physical half rests on a prior session's written account plus tonight's acceptance |
| Browser capture supports one spoken Project task with visible microphone ownership | proven by tests above (`speakMicOwnership`) | **not observed.** No one has spoken a Project task into a real microphone | **accepted, not observed** |
| Permission denial, silence, interruption and failed transcription retain recoverable input | proven by tests above, and the permission faces shot by the glass suite | **not observed.** Beats 2 (denied permission), 3 (silence) and 4 (interruption) are recorded as unwalked at `current-phase-status.md:301-303` | **accepted, not observed** |
| One real correction saved and applied by the existing matcher on a relevant replay, with honest counts | proven by tests above | **not observed.** Beat 5 is recorded as unwalked at `current-phase-status.md:301-303`; the owner's three mis-heard `Tilda Jarvis` utterances were noted as material for it and were never used | **accepted, not observed** |
| Kept speech and correction records survive process restart; no duplicate typing on an uncertain delivery retry | proven by tests above (re-open of the data root; the pending park) | **half observed on 2026-09-08**: the dictation journal survived a hub restart unchanged (`current-phase-status.md:298-300`). Correction-record survival across a restart, and an actual uncertain delivery followed by a retry, were **not observed** | satisfied; the unobserved halves rest on tonight's acceptance |

## 3. What remains unknown

These are things a performed physical walk would have surfaced and that nobody has
now looked for. None of them is a known defect; each is an absence of observation.

- **Denied microphone permission, end to end.** The permission faces are proven in
  a browser fixture and shot; no one has watched macOS actually refuse the
  microphone and then watched what the desk does with the words already spoken.
- **Silence and interruption against real audio.** The loss rules are proven
  against the capture contract, not against a real transcriber returning nothing
  or a floor taken mid-sentence on live input.
- **A correction learned from real speech.** The matcher is proven on fixture text.
  Whether a correction saved from a genuinely mis-heard utterance matches on a
  later real utterance — the case the story exists for — is unmeasured.
- **A true process restart with correction records.** Only the journal was seen to
  survive a restart. Correction memory across a restart is proven at the data-root
  level in tests and not on the owner's desk.
- **An actual uncertain delivery.** No one has produced one. The never-automatic
  rule (his 2026-09-08 ruling) has therefore never been exercised against a real
  ambiguous typing outcome.
- **First capture to visible text, timed.** ACCEPTANCE.md's performance target (at
  most 3 active minutes, cold) is not measured for this story by anyone.
- **The two findings ledgered on 2026-09-08 and not fixed:**
  `/api/dictation/readiness` reported `ready: true` on a desk where dictation
  crashed the process every time (the fake all-clear HS-200-07 exists to end), and
  the Speak face reads `DICTATION · GPT 5 mini · KEY NOT SET` while the runtime
  resolves local (`current-phase-status.md:307-313`). Both are still true as far as
  anyone has checked; neither was re-checked tonight.
- **The three parked gaps in `BACKLOG.md` §AI** (no delivery outcome on the journal
  row; a pipeline-off hotkey row dropping the target profile; an adapter exception
  classified `failed` rather than `uncertain`). The ruling closes the story, not
  these; see the reconciliation note added there.
