# Phase 52 — Voice Command Macros on a carved dispatch seam: final summary

**Status:** CLOSED (7/7). Opened and closed 2026-06-08 on user direction, right after
Phase 51 closed + merged (PR #38). From [backlog](../BACKLOG.md) candidate **B** (voice
macros), re-envisioned mid-phase by the user as a **voice command launcher**, paired
with a scoped slice of candidate **E** (carve the dispatch seam out of `web_runtime`).

## The thesis

Turn the dictation hotkey into a command launcher: a user maps a spoken keyword to a
real system action (open a URL, launch an app, run a shell command, type a snippet) on
a dedicated board, and the action fires when they speak the keyword while dictating.
Land it on a clean dispatch seam carved out of the 2,341-line `web_runtime` god-object,
and reuse the existing actuator guarded-execution framework rather than reinventing it.
One feature with one motivated refactor, under one thesis.

## A vision correction worth recording

The first scaffold modeled "voice macros" as deterministic text transforms inside the
dictation stream ("new paragraph" inserts a newline). The user corrected it: they want
a launcher that fires real actions. The phase was re-scaffolded around that (commit
`12ab55a`), the actuator system was mapped as the execution substrate, and the user
chose the safety model: you own the risk, configuring is consent, no per-fire prompt,
off by default. Then the user named the UI as the crux, so the board was designed
UI-first before the schema was finalized.

## What shipped, story by story

- **HS-52-01 — Carve the dictation seam (scoped E).** The inline
  `_maybe_run_dictation_pipeline` orchestration moved out of `web_runtime.py` (2,341 ->
  2,255 lines) into a standalone, unit-testable `holdspeak/dictation_runner.py`,
  byte-identical.
- **HS-52-02 — Macro model + config.** `VoiceMacro` (keyword + a deterministic action:
  `open_url` / `launch_app` / `shell` / `type_text` + one payload), with a single-source
  `preview()` and a normalized whole-utterance `matches()`. `MacrosConfig` (off by
  default), config-version-safe through `/api/settings`. Designed UI-first.
- **HS-52-03 — Local action connectors.** Reuse the Phase-38 gated-connector framework:
  the three egress kinds run bounded subprocesses behind a per-macro manifest (a
  connector built for one command refuses any other before egress); `type_text` is a
  plain local connector. No framework change.
- **HS-52-04 — Dispatch wiring.** `dispatch_voice_command` at the top of the carved
  seam: deterministic match, fire the bounded connector, type nothing, surface "command:
  <keyword>" as a runtime activity; byte-identical when off / no match.
- **HS-52-05 — The Voice Commands board (centerpiece).** A dedicated `/commands` route:
  a card-per-command grid with per-kind color edges/badges, a live "what fires" preview
  per card, the honest shell danger treatment, a per-card Test button
  (`POST /api/commands/test`), a per-kind adaptive editor with match hint + conflict
  warning, an inviting empty state. Built UI-first and screenshot-verified (4 PNGs).
- **HS-52-06 — Docs.** `docs/VOICE_COMMANDS.md`, product-tense and honest, passing the
  Phase-51 roadmap-vocabulary guard.
- **HS-52-07 — Closeout.** This summary, the dogfood, the PR.

## Exit evidence

- Dogfood (`dogfood.py` + `dogfood-transcript.txt`, RESULT: PASS): off-by-default
  returns no command (byte-identical), a non-keyword utterance is not handled, a
  configured `shell` macro really fires (an `echo` into a temp file, verified), and a
  `type_text` macro types via the writer.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` -> 2499 passed, 17
  skipped (started the phase at 2454; +45 across the phase's new tests, no regressions).
- `cd web && npm run build` clean; 0 `holdspeak/static/_built/` tracked.
- Screenshots committed in `screenshots/` (board, empty state, editor, shell danger).

## Decisions worth remembering

- **The safety model is the user's:** configured macros fire directly, no per-fire
  prompt, off by default. The blast radius is bounded because the match is deterministic
  (selects which macro, never composes a command) and each macro's connector manifest
  permits only its own configured action.
- **The non-meeting persistence wrinkle.** The actuator table is meeting-FK'd
  (`actuator_proposals.meeting_id REFERENCES meetings(id)`), so a voice fire reuses the
  guarded execution (connector + gate + bounded manifest) but is audited via the runtime
  activity + log, not that table. No fake meeting, no schema bump.
- **`dictation_runner`, not `dictation_runtime`:** the latter name is the DIR-01 LLM
  backend; the new module is distinct.
- **Screenshot-verify is not optional.** A screenshot pass caught a real
  `[hidden]`-override CSS bug that a green build would have missed.

## Scope held

- Only the dictation slice of `web_runtime` was carved; full candidate **E** (the rest
  of the god-object) remains a backlog watch item.
- Whole-utterance match only in v1; no mid-sentence command parsing.
- A persistent per-fire audit table is deferred (the actuator table is meeting-scoped).

## Next

No follow-on required. Candidate **B** is shipped; the dispatch-seam slice of **E**
landed with it. Remaining backlog: **D** (frontend density paydown), the rest of **E**,
**F** (local activity pre-briefing), **G** (privacy at decision points).
