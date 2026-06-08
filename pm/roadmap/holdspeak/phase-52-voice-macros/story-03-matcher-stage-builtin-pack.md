# HS-52-03 — Deterministic matcher stage + built-in pack

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-01, HS-52-02
- **Unblocks:** HS-52-04, HS-52-05, HS-52-06
- **Owner:** unassigned

## Problem
With a seam and a config in place, the dictation loop needs the deterministic command
layer itself: a stage that matches an exact spoken command and applies a predictable
action, alongside (never replacing) the LLM rewrite, byte-identical when off.

## Scope
- **In:**
  - A `spoken-command-matcher` Transducer (`holdspeak/plugins/dictation/builtin/
    spoken_command_matcher.py`) implementing the contract
    (`plugins/dictation/contracts.py:57-64`) with `requires_llm = False`.
  - Register `"spoken-command-matcher"` in `_KNOWN_DICTATION_STAGES`
    (`config.py:306`) and wire it as the FIRST stage in `build_pipeline()`
    (`assembly.py:52-112`).
  - Matching: on an **exact whole-utterance** match against a macro `phrase` (and the
    built-in pack), apply the deterministic action and short-circuit the LLM (skip the
    downstream rewrite). On no match, pass the text through unchanged.
  - A small built-in pack of deterministic commands. Finalize the set here; candidates:
    "new paragraph" / "new line" (insert newline(s)), "bullet list" (format the dictated
    items as a list), "copy that" / "copy only" (clipboard instead of typing), "send it"
    (type then Enter). Each action is deterministic; none calls the model.
  - Off by default: with `macros.enabled = False`, the stage is inert and typed output
    is byte-identical.
- **Out:** the editor UI (HS-52-04); the runtime-activity signal (HS-52-05); LLM-flavored
  commands ("make it concise" is the rewrite pipeline, not a macro).

## Acceptance criteria
- [ ] The `spoken-command-matcher` stage runs first, `requires_llm = False`, registered
      and wired; an unknown-stage config still validates per `config.py:359`.
- [ ] Exact match applies the deterministic action and short-circuits the LLM rewrite;
      no match passes text through unchanged.
- [ ] With macros off, the typed output is byte-identical to today (a test asserts it,
      mirroring the pipeline's off-by-default tests).
- [ ] The built-in pack is deterministic (no model call); each command unit-tested for
      match, no-match, and the produced text/action.
- [ ] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit: matcher match/no-match/passthrough; each built-in command; off-by-default
  byte-identical (`uv run pytest -q -k "macro or dictation or pipeline"`).

## Notes / open questions
- Whole-utterance match only in v1; no mid-sentence embedded commands (document the
  limitation in HS-52-06).
- Normalize the spoken text for matching (case, trailing punctuation from the
  transcriber) so "New paragraph." matches "new paragraph". Keep the normalization
  deterministic and documented.
