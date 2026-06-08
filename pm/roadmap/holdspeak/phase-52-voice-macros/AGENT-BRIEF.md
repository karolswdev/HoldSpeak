# Phase 52 — Agent Brief (read this first)

You are picking up **Phase 52 — Voice Command Macros on a carved dispatch seam** for
HoldSpeak. This brief is self-contained: the mission, the exact code seams (mapped
against the live tree at scaffold time), the rules of the road, and a per-story
definition of success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story you're working.
If this brief disagrees with the live status docs or the codebase, the **codebase
wins** — re-verify before trusting any line or number below.

---

## 0. Mission

Today the dictation hotkey can only do one thing: transcribe speech and type it (after
an optional LLM rewrite). The user wants a **voice command launcher**: map a spoken
keyword to a real system action, and have that action fire when you speak the keyword.

Hold the dictation hotkey, say a configured keyword, release: HoldSpeak runs the
action instead of typing. Examples the user gave: open a specific website, launch a
terminal, run a shell command, type a snippet. The user maps keyword to action in the
web UI; the mapping is deterministic and entirely theirs.

This lands on a **dispatch seam carved out of the `web_runtime` god-object** (a scoped
slice of backlog candidate E), and it **reuses HoldSpeak's existing actuator system**
(the propose -> approve -> execute guarded executor from Phase 37/38) as the execution
substrate, extended with new **local action connectors**. That is the thesis:

> Carve the dictation-dispatch path out of the 2,341-line `web_runtime.py`, and on that
> clean seam route a matched voice keyword to a pre-approved actuator invocation that
> runs through the existing guarded executor and a new local connector.

One feature (backlog **B**, re-envisioned as a command launcher) with one motivated,
scoped refactor (a slice of **E**), reusing built and tested safety plumbing.

---

## 1. The one thing you must not get wrong

**Deterministic keyword -> pre-configured action. The transcription selects WHICH macro,
it never composes a command.** This is the safety model the user explicitly chose:

- **The user owns the risk; configuring is consent.** A configured macro fires directly,
  with **no per-execution approval prompt**. If the user maps "bear" to `rm -rf /`, that
  is their call. We do not nag at fire time.
- **But the blast radius is bounded to what they configured.** The spoken text is matched
  (exact, normalized, whole-utterance) against the keyword set. On a match, the macro's
  **pre-configured** action runs. The transcriber's output is never turned into a shell
  command. A mishearing can fire the wrong macro; it cannot synthesize a new one. Each
  macro's connector carries a permission manifest derived from its own configured action,
  so the executor still bounds each macro to exactly that action.
- **Off by default.** The whole capability is gated off (enabling it is an informed
  opt-in). With it off, the dictation hotkey types exactly as it does today
  (byte-identical).
- **Audit trail for free.** Every fire goes through the actuator executor, so it is
  recorded in the actuator audit log. The user can see what ran.

The structural carve (HS-52-01) is **behavior-preserving**: extracting the dictation
dispatch out of `web_runtime` must not change what gets typed in the no-macro path.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md`, **7** checkboxes; `mkdir -p .tmp` first). A story
  flipping to `done` ships its `evidence-story-{n}.md` in the same commit; **one**
  done-flip per commit. The phase-exit story needs `evidence-story-{last}.md` **and**
  `final-summary.md` in the same commit. Status line is `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates the story header, this phase
  `current-phase-status.md`, the project `README.md`, and any canon doc touched.
- **One PR per phase, merged on green CI** (Unit, Integration macOS, E2E macOS, Linux
  Smoke). Branch `phase-52-voice-macros`; at close push + PR to `main` + merge.
- **Tests actually run.** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **The web bundle is gitignored.** Edit `web/src`, `cd web && npm run build`, commit
  source only, never `holdspeak/static/_built/`. JS-injected DOM needs
  `<style is:global>`; screenshot-verify.
- **High UI/UX bar** (`ui-ux-pro-max`). The command board is the centerpiece, designed
  UI-first (`design-voice-commands-board.md`). It ships **screenshot evidence**: a
  `scripts/screenshot_voice_commands.py` (mirror `scripts/screenshot_learning_digest.py`)
  captures the board with all four macro kinds, the empty state, each per-kind editor, and
  the shell danger treatment, committed to the phase `screenshots/` folder. The new
  `/commands` route is also picked up by the `screenshots.yml` route-screenshot CI.
- **User-facing docs obey the Phase-51 guard.** The new Voice Commands guide (HS-52-06)
  must be product-tense with no roadmap vocabulary (`Phase 52` / `HS-52-xx`); run the
  `humanizer` skill over it.
- **Security posture.** This phase ships local code execution from voice. Keep it
  off-by-default, keep each macro bounded by its manifest, log every fire, and be honest
  in the docs about what it is.

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

### The dictation dispatch path (the E carve target)
- `holdspeak/web_runtime.py` is **2,341 lines** (the god-object). After a dictation
  capture: transcription (`:1588`), text processing (`text_processor.py:51-65`, called
  at `:1599`), then `_maybe_run_dictation_pipeline(text, ...)` (called `:1607`, defined
  `:1720-1825`), then the result is typed (`typer.py:type_text`).
- **The carve:** extract this orchestration into a dedicated module, e.g.
  `holdspeak/dictation_runtime.py`, with a testable entry. The voice-command **dispatch
  decision** ("is this an utterance a configured keyword? then fire the action and do not
  type; else dictate") lives at the TOP of this module, before the pipeline runs.

### The actuator system (the execution substrate to REUSE)
The actuator subsystem is purpose-built for "a pre-approved action that leaves the safe
zone." Reuse it; do not reinvent it.
- `holdspeak/plugins/actuators.py:41-133` — `ActuatorProposal` (`target`, `action`,
  `preview`, `payload`, `reversible`, `required_capabilities`).
- `holdspeak/plugins/actuator_executor.py:61-162` — `ActuatorExecutor.execute(proposal_id)`:
  only `approved` proposals run; gated by `allow_actuators` + `allowed_actuator_ids`;
  calls the injected `connector(proposal)`; transitions to `executed`/`failed` with audit.
- `holdspeak/plugins/gated_connector.py` — `build_gated_connector(manifest, plan, interpret)`
  (`:237-290`); `WriteConnectorManifest` (`:141-212`, `permission` in
  `{"shell:exec","network:outbound"}`, `allowed_argv_prefixes`, `allowed_hosts`);
  `GatedOperation.subprocess()/.outbound()` (`:82-123`).
- `holdspeak/connector_runtime.py:84-145` — `PermissionGate.run_subprocess()` /
  `.open_outbound_socket()` (the actual guarded side effect).
- Reference connectors to mirror: `plugins/builtin/followup_ticket_actuator.py:118-147`
  (`build_outbox_connector`, local file, NO manifest — the simplest reference),
  `github_issue_actuator.py:207-224` (shell `gh`, with manifest),
  `webhook_post_actuator.py:158-184` (network, with manifest).
- Persistence + audit: `holdspeak/db/actuators.py` — `record_proposal()` (`:45-138`),
  `transition_proposal()` (`:173-247`), `list_audit()` (`:249-270`). **Gotcha:** these
  are meeting-scoped (`meeting_id`, `window_id`). A voice macro fires outside a meeting,
  so HS-52-04 must give it a non-meeting context (a synthetic "voice" session/window) or
  extend the persistence to allow one. Decide and note it.
- Governance: `config.py` `MeetingConfig.allow_actuators` / `.allowed_actuators`
  (`:180-186`) and the host capability gate `plugins/host.py:_missing_capabilities`
  (`:202-209`). Voice macros are dictation-side, so add a dictation-side enable; the
  executor is still constructed to allow only the voice-macro connectors.

### Config + settings UI (the macro store + editor)
- `holdspeak/config.py` — `DictationConfig` dataclass (~`:323-399`); `CONFIG_VERSION`
  + `_coerce_config_version()` (`:45-70`) + `_coerce()` (`:24-42`) give forward-safe
  load (Phase 50). Add a `MacrosConfig` (`enabled: bool = False`, `items: list[VoiceMacro]`).
- `holdspeak/web/routes/system.py:442` (`GET /api/settings`) / `:461` (`PUT`).
- `web/src/pages/settings.astro` (234 lines) + `web/src/scripts/settings-app.js` (242).
- **List-editor precedent to reuse:** the memory-corrections curate UI,
  `web/src/pages/dictation.astro:290-356` + `dictation-app.js:1477-1621`.

### Runtime activity (so a fire is visible)
- `web_runtime.py:331-368` (`_set_runtime_activity` / `_broadcast_runtime_activity`),
  contract `runtime_activity.py:79-156`. A fired macro can surface a "command: open
  terminal" activity through this existing channel.

**No existing voice-macro code** — greenfield.

---

## 4. Per-story definition of success

- **HS-52-01 — Carve the dictation-dispatch seam (scoped E).** The dictation
  orchestration (`web_runtime.py:1720-1825` plus its direct collaborators) moves into a
  dedicated, unit-testable module (`holdspeak/dictation_runtime.py` or similar) with a
  clear entry; `web_runtime` delegates to it. Typed output byte-identical; full suite
  green with no behavioral test edits; a focused unit test drives the extracted entry.
  No feature yet. This is the seam everything lands on.
- **HS-52-02 — Macro model + config.** A `VoiceMacro` (a `keyword` + an `action`:
  a `kind` in {`open_url`, `launch_app`, `shell`, `type_text`} plus a payload) and a
  `MacrosConfig` (`enabled` default `False`, `items` list) nested under `DictationConfig`,
  loaded/saved config-version-safe, read/write through `/api/settings`, with validation.
  A test pins round-trip + off-by-default.
- **HS-52-03 — Local action connectors on the actuator framework.** New connectors built
  with `build_gated_connector` for the action kinds: `type_text` and `open_url`/
  `launch_app` (local, low-risk), and `shell` (gated). Each macro derives a per-macro
  `WriteConnectorManifest` from its own configured action, so the executor bounds it to
  exactly that command. Reuse `ActuatorProposal` + `ActuatorExecutor` + `PermissionGate`
  unchanged. Nothing executes unless the capability is enabled. Each connector
  unit-tested (allowed action runs, anything off-manifest refused, capability-off blocks).
- **HS-52-04 — Dispatch wiring.** In the carved module, on an exact whole-utterance
  keyword match, build the macro's proposal, auto-approve it (the config is the consent),
  and run it through `ActuatorExecutor` (`record_proposal` -> `transition_proposal(approved)`
  -> `execute`), then type nothing; on no match, dictate as normal. Resolve the
  non-meeting persistence context. With macros off, byte-identical. A test proves
  command-fires-on-match and byte-identical-off, plus the audit row.
- **HS-52-05 — Inspect/edit UI.** A "Voice commands" section in the settings cockpit: the
  enable switch plus a visible, editable list of macros (keyword + action kind + payload),
  add/edit/remove, persisted through `/api/settings`, reusing the corrections-curate
  pattern. What you see is exactly what fires. UI/UX bar via `ui-ux-pro-max`;
  `npm run build` clean; screenshot-verified.
- **HS-52-06 — Docs (dedicated docs story).** A "Voice commands" guide: what they are,
  the action kinds, how to add one, the off-by-default + you-own-the-risk model stated
  plainly and honestly, the deterministic keyword match (no command synthesis), and the
  audit trail. Product-tense, passes the Phase-51 guard, `humanizer` run, linked in the
  index.
- **HS-52-07 — Closeout.** A dogfood proving a configured action fires (e.g. an `echo`
  shell macro and an `open_url` macro) and that a non-keyword utterance still dictates
  byte-identical with macros off. Full suite green, `final-summary.md`, phase CLOSED, PR
  merged on green, BACKLOG candidate B flipped to shipped (E slice noted).

---

## 5. Gotchas that will bite you

- **Don't reinvent the executor.** Reuse `ActuatorExecutor` + `build_gated_connector` +
  the persistence. The only genuinely new code is the local connectors and the dispatch
  wiring. Mirror `followup_ticket_actuator.py` (the simplest reference) for shape.
- **Per-macro manifest, not a global allow-list.** Each macro's connector permits exactly
  its own configured action. This is what bounds a mishearing to firing-the-wrong-macro
  rather than running-an-arbitrary-command.
- **Actuator persistence is meeting-scoped.** `record_proposal` wants `meeting_id` /
  `window_id`. A voice fire has neither. Decide a synthetic voice context vs. relaxing the
  schema in HS-52-04; do not hack a fake meeting row silently.
- **Governance is meeting-side today** (`MeetingConfig.allow_actuators`). Voice macros are
  dictation-side; add a dictation enable and construct the executor to allow only the
  voice-macro connectors. Keep off-by-default.
- **Don't decompose the whole god-object.** HS-52-01 extracts only the dictation dispatch.
  Full E stays a backlog "watch" item.
- **Whole-utterance match in v1.** The keyword is matched against the whole transcript.
  No mid-sentence command parsing.
- **`type_text` and typing.** A `type_text` action reuses `typer.py`; make sure it does
  not double-fire the normal dictation typing (the dispatch returns early).
- **Astro scoped CSS** for JS-injected rows (`<style is:global>`); screenshot-verify.

---

## 6. Where to start

`HS-52-01` (the carve) is first: it is the seam everything lands on and the riskiest
(a behavior-preserving extraction from a god-object). Do it with the full suite green and
no output change before any feature. Then 02 (the macro store), 03 (the connectors on the
actuator framework), 04 (wire the dispatch), 05 (the editor UI), 06 (docs), 07 (closeout).
Keep it off-by-default, keep each macro bounded by its manifest, reuse the actuator
plumbing, and keep the no-macro path byte-identical. This is the phase that turns the
dictation hotkey into a voice command launcher on a cleaner seam.
