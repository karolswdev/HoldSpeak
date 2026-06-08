# Phase 52 — Voice Macros on a carved dictation seam

**Status:** SCAFFOLDED (0/7). Opened 2026-06-08 on user direction, right after Phase 51
closed + merged (PR #38). From the [project backlog](../BACKLOG.md): candidate **B**
(voice macros, the strong north-star bet) paired with a scoped slice of candidate **E**
(carve the routing/dispatch seam the macros land on, not the whole `web_runtime`
decomposition). The user asked to ship a meaningful codebase improvement together with a
feature, under one thesis.

**Last updated:** 2026-06-08 (phase scaffolded: AGENT-BRIEF + this status doc + 7 story
files written; seams verified against the live tree; BACKLOG candidates B and E noted.
No story started yet.)

## The thesis — why this phase

The daily-driver dictation loop is all LLM. There is no small, visible, deterministic
command layer: a user cannot say "new paragraph" or "send it" and get a predictable,
inspectable result without the model in the loop. Grounded in the live tree:

- **The dictation orchestration is buried in a god-object.**
  `web_runtime.py:1720-1825` (`_maybe_run_dictation_pipeline`) runs inline inside a
  2,341-line file. A new deterministic stage, its config, and its runtime signal would
  all land deeper in that object.
- **The pipeline is already a clean staged executor.**
  `plugins/dictation/pipeline.py` runs ordered `Transducer` stages
  (`contracts.py:57-64`); a deterministic `spoken-command-matcher` with
  `requires_llm = False` slots in as the first stage.
- **Config is forward-safe** (Phase 50 `config_version` + coercion), so a new
  `macros` section evolves the config without dropping fields.

So: carve the dictation-execution path out of `web_runtime` into a dedicated, testable
module, then land the voice-macro grammar on the clean seam. The refactor is motivated
by the feature, not done for its own sake.

## Goal

Give the daily-driver dictation loop a deterministic, user-editable voice-macro grammar
(a small built-in pack plus user-defined phrases), inspectable and editable in the web
UI, running alongside (never replacing) the LLM rewrite, on a dictation-execution seam
carved out of the `web_runtime` god-object. Off by default and byte-identical when off;
deterministic, never a second LLM. No change to meeting capture, intel, plugins, or
synthesis.

## Scope

- **In:** carve the dictation-execution seam (HS-52-01); macro model + config
  (HS-52-02); the deterministic matcher stage + built-in pack (HS-52-03); user-defined
  macros + inspect/edit UI (HS-52-04); visible feedback via runtime activity (HS-52-05);
  a Voice Macros guide (HS-52-06); closeout (HS-52-07).
- **Out:** the full `web_runtime` / `web_server` decomposition (candidate E stays a
  "watch" item; we take only the dictation slice); LLM-flavored macros ("make it
  concise" is the rewrite pipeline, not a macro); mid-sentence embedded-command parsing
  (whole-utterance match in v1); any meeting/intel/plugin/synthesis change.

## Exit criteria (evidence required)

- The dictation orchestration is extracted out of `web_runtime` into a testable module;
  typed output byte-identical; full suite green. (HS-52-01)
- A `VoiceMacro` model + `MacrosConfig` (off by default) load/save config-version-safe
  through `/api/settings`. (HS-52-02)
- A `spoken-command-matcher` Transducer (`requires_llm = False`) lands as the first
  stage; a built-in pack of deterministic commands; byte-identical with macros off;
  matcher unit-tested. (HS-52-03)
- A visible, editable "Voice macros" section in the settings cockpit; persisted; no LLM
  magic; `npm run build` clean; screenshot-verified. (HS-52-04)
- A matched macro surfaces as a runtime activity through the existing broadcast;
  focus-safe. (HS-52-05)
- A product-tense Voice Macros guide that passes the Phase-51 roadmap-vocabulary guard;
  `humanizer` run; linked in the index. (HS-52-06)
- A dogfood proving command -> deterministic action and normal text -> byte-identical;
  full suite green; `final-summary.md`; phase CLOSED; PR merged; BACKLOG candidate B
  flipped to shipped. (HS-52-07)

## Invariants

- **Off by default, flag-unset byte-identical.** `dictation.macros.enabled = False`
  default; typed output unchanged when off.
- **Deterministic, not a second LLM.** A macro maps an exact spoken command to a
  deterministic text/control action. If it needs the model, it is not a macro.
- **Scoped carve.** Extract only the dictation-execution path; the rest of `web_runtime`
  is untouched.
- **Behavior-preserving elsewhere.** No meeting capture, intel, plugin, or synthesis
  change.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-52-01 | Carve the dictation-execution seam out of `web_runtime` (scoped E) | not started | none |
| HS-52-02 | Macro model + config (config-version-safe, `/api/settings`) | not started | HS-52-01 |
| HS-52-03 | Deterministic matcher stage + built-in pack | not started | HS-52-01, HS-52-02 |
| HS-52-04 | User-defined macros + inspect/edit UI | not started | HS-52-02, HS-52-03 |
| HS-52-05 | Visible feedback: matched macro as runtime activity | not started | HS-52-03 |
| HS-52-06 | Docs: the Voice Macros guide | not started | HS-52-03, HS-52-04 |
| HS-52-07 | Closeout: dogfood + final-summary + PR | not started | HS-52-01..06 |

## Where we are

Scaffolded on 2026-06-08, on the `phase-52-voice-macros` branch. Nothing started. Start
with HS-52-01 (the carve is the seam everything lands on, and the riskiest, so do it
behavior-preserving first). Read [`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.

## Open decisions (defaults chosen; flag to change)

- **Deterministic action model only.** Built-in macros do text/format/control ops
  (newline, list formatting, copy-instead-of-type, type-then-Enter). LLM shortcuts are
  out. Default chosen; finalize the exact built-in set in HS-52-03.
- **Whole-utterance match in v1.** No mid-sentence command parsing.
- **Off by default.** The gate is `dictation.macros.enabled`.
- **The E boundary is the dictation path only.** The new module owns the orchestration
  currently at `web_runtime.py:1720-1825`, nothing more.
