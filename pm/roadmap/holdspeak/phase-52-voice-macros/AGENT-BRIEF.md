# Phase 52 — Agent Brief (read this first)

You are picking up **Phase 52 — Voice Macros on a carved dictation seam** for
HoldSpeak. This brief is self-contained: the mission, the exact code seams (mapped
against the live tree at scaffold time), the rules of the road, and a per-story
definition of success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story you're working.
If this brief disagrees with the live status docs or the codebase, the **codebase
wins** — re-verify before trusting any line or number below.

---

## 0. Mission

The daily-driver dictation loop is all LLM today: you speak, Whisper transcribes, and
the pipeline rewrites. There is no small, visible, deterministic command layer. A user
cannot say "new paragraph" or "send it" and get a predictable, inspectable result
without the LLM in the loop.

This phase adds a **deterministic, user-editable voice-macro grammar** alongside (never
replacing) the LLM rewrite, and it does so on a **clean seam carved out of the
`web_runtime` god-object**, not buried deeper inside it. That pairing is the thesis:

> Carve the dictation-execution path out of the 2,341-line `web_runtime.py` into a
> dedicated, testable module, then land the voice-macro grammar on that clean seam.

The structural carve (a scoped slice of backlog candidate E) earns its keep because
everything the feature needs (a new deterministic stage, a config section, a runtime
signal) lands on that exact surface. We decompose the seam the feature touches, not the
whole god-object.

This is **one feature with one motivated refactor**, under one thesis. It is **not** a
general `web_runtime` decomposition, and it does **not** change meeting capture, intel,
plugins, or synthesis.

---

## 1. The one thing you must not get wrong

**Default output stays byte-identical, and macros are deterministic.** Two invariants:

- **Off by default, flag-unset byte-identical.** The macro layer is gated
  (`dictation.macros.enabled = False` by default), exactly like the Phase-39/40
  pipeline knobs. With it off, every dictation types the same bytes it does today. The
  DIR-01 invariant holds.
- **Deterministic, not a second LLM.** A macro is an exact-match spoken command mapped
  to a **deterministic** text or control action (insert a newline, format as a list,
  copy instead of type, type-then-Enter). It is **not** an LLM-rewrite shortcut.
  "Make it concise" is an LLM operation and belongs to the existing rewrite pipeline,
  not the macro grammar. If a macro cannot be resolved without the model, it is out of
  scope. The whole point of this layer is that it is inspectable and predictable.

The structural carve (HS-52-01) is **behavior-preserving**: extracting the dictation
orchestration out of `web_runtime` must leave the typed output of every existing test
unchanged.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md`, **7** checkboxes; `mkdir -p .tmp` first; the hook
  validates and deletes it). A story flipping to `done` ships its
  `evidence-story-{n}.md` in the same commit; **one** done-flip per commit. The
  phase-exit story needs `evidence-story-{last}.md` **and** `final-summary.md` in the
  same commit. Status line is the list-item form `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates: the story header status, this
  phase `current-phase-status.md` (row + Last-updated + "Where we are"), the project
  `README.md` (phase row + Current-phase + Last-updated), and any canon doc the story
  touched.
- **One PR per phase, merged when CI green** (Unit, Integration macOS, E2E macOS, Linux
  Smoke). Work on the `phase-52-voice-macros` branch; at close, push + open a PR to
  `main` + merge with a merge commit on green. Memory `feedback_merge_phases_via_pr`.
- **Tests actually run.** Flip a story to `done` only after running the relevant tests
  and reading the output. Full suite:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **The web bundle is gitignored.** Edit `web/src`, run `cd web && npm run build` to
  verify, commit source only, never `holdspeak/static/_built/`. JS-injected DOM needs
  `<style is:global>` CSS (the Astro scoped-CSS gotcha; screenshot-verify).
- **High UI/UX bar.** The macro editor is a real editing surface, not a raw textarea.
  Reuse the existing list-editor pattern; add affordances; check overflow. Apply
  `ui-ux-pro-max`.
- **User-facing docs obey the Phase-51 guard.** The new Voice Macros guide (HS-52-06) is
  user-facing, so it must be product-tense with no roadmap vocabulary
  (`tests/unit/test_doc_drift_guard.py` will fail the build otherwise). Run the
  `humanizer` skill over it. See `docs/internal/DOCS_STYLE.md`.

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

**The dictation execution path (the E carve target):**
- `holdspeak/web_runtime.py` is **2,341 lines** (the god-object). The dictation
  orchestration is inline:
  - `web_runtime.py:1607` calls `_maybe_run_dictation_pipeline(text, ...)` after
    transcription (`:1588`) and text processing (`text_processor.py:51-65`, called at
    `:1599`).
  - `web_runtime.py:1720-1825` is `_maybe_run_dictation_pipeline()`: reads config,
    builds the pipeline (`plugins/dictation/assembly.py:build_pipeline`), injects
    corrections, runs it, journals (side-channel), returns `final_text` (`:1822`),
    which is then typed (`typer.py:type_text`).
- **The carve:** extract this orchestration (roughly `:1720-1825` plus its direct
  collaborators) into a dedicated module, e.g. `holdspeak/dictation_runtime.py`, with a
  testable entry like `run_dictation(text, *, runtime, config, ...) -> str`.
  `web_runtime` calls into it. Behavior byte-identical.

**The DIR-01 dictation pipeline (where the macro stage lands):**
- `holdspeak/plugins/dictation/pipeline.py:62-145` — `DictationPipeline`, the ordered
  stage executor. Off (`enabled=False`) returns the original text unmodified (`:63-71`).
- `holdspeak/plugins/dictation/contracts.py:57-64` — the `Transducer` protocol:
  `id`, `version`, `requires_llm: bool`, `run(utt, prior) -> StageResult`. A macro
  matcher is a Transducer with `requires_llm = False`.
- `holdspeak/config.py:306` — `_KNOWN_DICTATION_STAGES = ("intent-router",
  "project-rewriter", "kb-enricher")`. Add `"spoken-command-matcher"`.
- `holdspeak/plugins/dictation/assembly.py:52-112` — `build_pipeline()` instantiates a
  stage per `cfg.pipeline.stages` id. Wire the new stage here as the FIRST stage.
- `holdspeak/plugins/dictation/builtin/` — where built-in stages live
  (`intent_router.py`, `kb_enricher.py`, ...). Add `spoken_command_matcher.py`.

**Config (the macro persistence):**
- `holdspeak/config.py` — `DictationConfig` dataclass (~`:323-399`) with nested
  `DictationPipelineConfig`. `CONFIG_VERSION = 1` + `_coerce_config_version()`
  (`:45-70`) + `_coerce()` (`:24-42`) give forward-safe load (Phase 50). Add a
  `MacrosConfig` dataclass (`enabled: bool`, `items: list[VoiceMacro]`) nested under
  `DictationConfig`; unpack it in `Config.load()` (`:456-466`) via `_coerce`.

**Settings API + UI (inspect/edit):**
- `holdspeak/web/routes/system.py:442` (`GET /api/settings`) and `:461`
  (`PUT /api/settings`) read/write `Config`. Add a `voice macros` section to the
  validate/merge path.
- `web/src/pages/settings.astro` (234 lines) + `web/src/scripts/settings-app.js`
  (242 lines): the sectioned/searchable settings cockpit. Add a "Voice macros" section.
- **List-editor precedent to reuse:** the memory-corrections curate UI,
  `web/src/pages/dictation.astro:290-356` (form add + list) +
  `web/src/scripts/dictation-app.js:1477-1621` (render rows + delete + refresh).

**Runtime activity (visible feedback):**
- `holdspeak/runtime_activity.py:79-156` — the activity state contract.
- `web_runtime.py:331-368` — `_set_runtime_activity()` / `_broadcast_runtime_activity()`
  fan a state to desktop presence + the websocket. A matched macro can emit an activity
  ("command: new paragraph") through this existing channel; no new websocket type.

**No existing macro code** — `voice_macro` / `spoken-command` is greenfield.

---

## 4. Per-story definition of success

- **HS-52-01 — Carve the dictation-execution seam (scoped E).** The inline
  `_maybe_run_dictation_pipeline` orchestration moves out of `web_runtime.py` into a
  dedicated, unit-testable module (`holdspeak/dictation_runtime.py` or similar).
  `web_runtime` calls into it. Typed output is byte-identical: the full suite is green
  with no test changes beyond the move, and a focused test exercises the extracted unit
  directly. No feature yet. This is the structural improvement, justified by every
  story that follows landing here.
- **HS-52-02 — Macro model + config.** A `VoiceMacro` model (a `phrase` to match and a
  deterministic `action`) and a `MacrosConfig` (`enabled` default `False`, `items`
  list) nested under `DictationConfig`, loaded/saved config-version-safe, and read/write
  through `/api/settings`. A test pins load/save round-trip and the off-by-default
  shape.
- **HS-52-03 — Deterministic matcher stage + built-in pack.** A `spoken-command-matcher`
  Transducer (`requires_llm = False`) registered in `_KNOWN_DICTATION_STAGES`, wired as
  the first stage in `assembly.py`, landing on the carved seam. A small built-in pack of
  deterministic commands (finalize the set here; candidates: "new paragraph"/"new line",
  "bullet list", "copy that"/"copy only", "send it" = type-then-Enter). On an exact
  whole-utterance match it returns the deterministic transform and short-circuits the
  LLM; otherwise it passes the text through unchanged. With macros off, byte-identical.
  Matcher unit-tested (match, no-match, passthrough).
- **HS-52-04 — User-defined macros + the inspect/edit UI.** A "Voice macros" section in
  the settings cockpit: a visible, editable list (add/edit/remove a phrase + its action)
  reusing the corrections-curate pattern, persisted through `/api/settings`. No LLM
  magic; what you see is what fires. UI/UX bar via `ui-ux-pro-max`; `npm run build`
  clean; screenshot-verified.
- **HS-52-05 — Visible feedback.** A matched macro surfaces as a runtime activity
  through the existing broadcast (e.g. "command: new paragraph"), so the user sees the
  deterministic match fire. Focus-safe; off-path when macros are off.
- **HS-52-06 — Docs (dedicated docs story).** A "Voice macros" user guide: what they
  are, that they are deterministic and editable (not LLM), the built-in pack, how to add
  your own, and how they relate to the rewrite pipeline. Product-tense, passes the
  Phase-51 roadmap-vocabulary guard, `humanizer` run over it, linked into the docs
  index.
- **HS-52-07 — Closeout.** A dogfood proving both paths: a spoken command yields the
  deterministic action, and normal dictation is byte-identical with macros off (and
  unchanged-except-the-command with them on). Full suite green, `final-summary.md`,
  phase CLOSED, PR to `main` merged on green, BACKLOG candidate B flipped to shipped
  (and the scoped-E note recorded).

---

## 5. Gotchas that will bite you

- **Don't decompose the whole god-object.** HS-52-01 extracts ONLY the dictation
  orchestration. `web_runtime` keeps hotkey/device/meeting/activity. Carving more is
  scope creep and a giant risky diff; the backlog keeps full E as a separate "watch"
  item.
- **Determinism is the feature.** Resist making "make it concise" a macro. That is the
  LLM rewrite, which already exists. The macro grammar is for predictable text/control
  ops only. If you need the model, it is not a macro.
- **Whole-utterance match in v1.** Match the whole transcript against a command phrase.
  Do not parse mid-sentence embedded commands ("type this and send it") in v1; that is a
  grammar rabbit hole. Note the limitation honestly in the docs.
- **Byte-identical proof.** The carve (01) and the off-by-default gate both need a test
  that the typed output is unchanged. Reuse the dictation pipeline's existing
  off-by-default tests as the template.
- **The new doc must pass last phase's guard.** HS-52-06 is user-facing; `Phase 52`,
  `HS-52-xx` must not appear in it. The guard from Phase 51 will catch it.
- **Astro scoped CSS.** The macro list rows are JS-injected, so their CSS must be
  `<style is:global>` (memory `reference_astro_scoped_css_js_dom`); screenshot-verify
  that styles actually apply.
- **Frontend density (D rides along).** `dictation.astro` is ~2.7k lines. If the macro
  UI lands there rather than `settings.astro`, factor as you go; do not grow the page
  further without paying it down. Standing invariant, not its own story.

---

## 6. Where to start

`HS-52-01` (the carve) is first because it is the seam everything else lands on, and it
is the riskiest (a behavior-preserving extraction from a god-object). Do it with the
full suite green and no output change before adding any feature. Suggested sequence:
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07. Keep the default byte-identical, keep macros
deterministic, and keep the carve scoped to the dictation path. This is the phase that
gives the daily driver a small, visible, predictable command layer on a cleaner seam.
