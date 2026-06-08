# Phase 52 — Voice Command Macros on a carved dispatch seam

**Status:** SCAFFOLDED (0/7). Opened 2026-06-08 on user direction, right after Phase 51
closed + merged (PR #38). From the [project backlog](../BACKLOG.md): candidate **B**
(voice macros) re-envisioned by the user as a **voice command launcher**, paired with a
scoped slice of candidate **E** (carve the dispatch seam out of `web_runtime`).

**Last updated:** 2026-06-08 (re-scaffolded after a vision correction: the first scaffold
modeled macros as deterministic text transforms inside the dictation stream; the user
wants a command launcher that fires real system actions — open a URL, launch a terminal,
run a shell command, type a snippet. Rebuilt the brief + 7 stories around reusing the
actuator guarded-executor framework. Seams verified against the live tree. No story
started yet.)

## The thesis — why this phase

The dictation hotkey can only transcribe-and-type. The user wants to map a spoken keyword
to a real action and have it fire on that keyword. Grounded in the live tree:

- **The dictation dispatch is buried in a god-object.** After transcription, the flow
  runs inline through `web_runtime._maybe_run_dictation_pipeline` (`web_runtime.py:1720-1825`)
  inside a 2,341-line file. The command-vs-dictate decision belongs at the top of a clean
  module, not deeper in that object.
- **HoldSpeak already has the safe execution substrate.** The actuator system
  (`plugins/actuator_executor.py`, `plugins/gated_connector.py`, `db/actuators.py`) is a
  propose -> approve -> execute guarded executor with permission manifests and an audit
  log, built in Phase 37/38 for exactly "a pre-approved action that leaves the safe zone."
  A voice keyword firing a shell command is a local-action actuator, auto-approved at
  config time.
- **Config is forward-safe** (Phase 50), so a new `macros` section evolves it cleanly.

So: carve the dispatch seam out of `web_runtime`, and on it route a matched keyword to a
pre-approved actuator invocation through the existing executor and a new local connector.

## The safety model (user's explicit choice)

The user owns the risk: configuring a macro in the web UI is the consent, so a configured
macro fires directly with **no per-execution prompt**. Bounded by two properties:

- **Deterministic match.** The spoken text (normalized, whole-utterance) selects WHICH
  macro fires. The transcriber never composes a command; a mishearing can fire the wrong
  configured macro, not synthesize a new one.
- **Per-macro manifest.** Each macro's connector permits exactly its configured action, so
  the executor bounds every macro to its own command.
- **Off by default.** Enabling the capability is an informed opt-in; off, the hotkey types
  byte-identical to today.
- **Audited.** Every fire goes through the actuator executor and is recorded.

## Goal

Turn the dictation hotkey into a voice command launcher: user-mapped spoken keywords fire
deterministic system actions (open URL, launch app, run shell command, type snippet)
through the reused actuator guarded executor, on a dispatch seam carved out of the
`web_runtime` god-object. Off by default and byte-identical when off. No change to meeting
capture, intel, plugins, or synthesis behavior.

## Scope

- **In:** carve the dispatch seam (HS-52-01); macro model + config (HS-52-02); local
  action connectors on the actuator framework (HS-52-03); dispatch wiring with
  auto-approved execution (HS-52-04); inspect/edit UI (HS-52-05); a Voice Commands guide
  (HS-52-06); closeout (HS-52-07).
- **Out:** the full `web_runtime` / `web_server` decomposition (candidate E stays a watch
  item; take only the dispatch slice); per-fire approval prompts (the user pre-approves at
  config time); mid-sentence embedded-command parsing (whole-utterance match in v1);
  rewriting the actuator framework (reuse it); any meeting/intel/plugin/synthesis change.

## Exit criteria (evidence required)

- The dictation dispatch is extracted out of `web_runtime` into a testable module; typed
  output byte-identical; full suite green. (HS-52-01)
- A `VoiceMacro` (keyword + action) + `MacrosConfig` (off by default) load/save
  config-version-safe through `/api/settings`. (HS-52-02)
- Local action connectors (open_url / launch_app / shell / type_text) on
  `build_gated_connector`, each bounded by a per-macro manifest; nothing runs unless
  enabled; unit-tested. (HS-52-03)
- On a keyword match, the macro fires through the reused `ActuatorExecutor`
  (auto-approved), types nothing, and is audited; no match dictates as normal;
  byte-identical when off. (HS-52-04)
- A visible, editable "Voice commands" section in the settings cockpit; persisted; what
  you see is what fires; `npm run build` clean; screenshot-verified. (HS-52-05)
- A product-tense Voice Commands guide (off-by-default + you-own-the-risk stated honestly)
  that passes the Phase-51 guard; `humanizer` run; linked in the index. (HS-52-06)
- A dogfood proving command-fires-on-match and byte-identical-off; full suite green;
  `final-summary.md`; phase CLOSED; PR merged; BACKLOG candidate B flipped to shipped.
  (HS-52-07)

## Invariants

- **Off by default, flag-unset byte-identical.** The capability is gated; off, the hotkey
  types exactly as today.
- **Deterministic, bounded.** Keyword selects a pre-configured action; per-macro manifest
  bounds it; the transcriber never composes a command.
- **Reuse, don't reinvent.** The actuator executor, connector framework, permission gate,
  and persistence are reused unchanged; only local connectors + dispatch wiring are new.
- **Scoped carve.** Extract only the dictation dispatch; the rest of `web_runtime` is
  untouched.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-52-01 | Carve the dictation-dispatch seam out of `web_runtime` (scoped E) | not started | none |
| HS-52-02 | Macro model + config (keyword -> action; `/api/settings`) | not started | HS-52-01 |
| HS-52-03 | Local action connectors on the actuator framework | not started | HS-52-02 |
| HS-52-04 | Dispatch wiring: match -> auto-approved actuator execute | not started | HS-52-01, HS-52-03 |
| HS-52-05 | Inspect/edit UI: the voice-commands editor | not started | HS-52-02, HS-52-04 |
| HS-52-06 | Docs: the Voice Commands guide | not started | HS-52-04, HS-52-05 |
| HS-52-07 | Closeout: dogfood + final-summary + PR | not started | HS-52-01..06 |

## Where we are

Scaffolded (re-scaffolded after a vision correction) on 2026-06-08, on the
`phase-52-voice-macros` branch. Nothing started. Start with HS-52-01 (the carve is the
seam everything lands on, and the riskiest, so do it behavior-preserving first). Read
[`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.

## Open decisions (defaults chosen; flag to change)

- **Action kinds for v1:** `open_url`, `launch_app`, `shell`, `type_text`. The user named
  open-website / open-terminal / run-command / type-into-terminal; these four cover them.
- **No per-fire approval.** Config is consent (user's explicit choice). Off by default.
- **Per-macro manifest** derives from the configured action (bounds each macro).
- **Non-meeting actuator context** (the persistence is meeting-scoped): resolve in
  HS-52-04 with a synthetic voice session/window rather than a fake meeting.
- **The E boundary is the dictation dispatch only.**
