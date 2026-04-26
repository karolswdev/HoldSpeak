# HS-1-06 — Step 5: Built-in stages (intent-router + kb-enricher)

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-02 (contracts), HS-1-03 (pipeline executor), HS-1-04 (LLM runtime + grammars), HS-1-05 (blocks loader)
- **Unblocks:** HS-1-07 (controller wiring assembles these into the live pipeline), HS-1-08 (CLI dry-run drives them end-to-end)
- **Owner:** unassigned

## Problem

DIR-01 §6.2 declares two built-in `Transducer`s:

- `intent-router` — calls the LLM runtime with a constrained-decoded
  prompt; returns an `IntentTag` (block_id, confidence, extras).
- `kb-enricher` — pure template substitution against the matched
  block's `inject` template; never calls the LLM.

The contracts (HS-1-02), pipeline (HS-1-03), runtime (HS-1-04), and
blocks (HS-1-05) all exist. This story stitches them into two
concrete stages whose `run()` methods turn an `Utterance` into a
`StageResult` per spec.

Per §9.1:

- `DIR-F-004` Router MUST return `IntentTag(matched=False,
  confidence=0.0)` if the model output cannot be parsed after a
  constrained-decoding retry.
- `DIR-F-005` Router MUST score against the **union** of all blocks
  loaded for the active project (or global) — i.e. the same loaded
  taxonomy, regardless of how many blocks exist.
- `DIR-F-006` `kb-enricher` MUST only act on `IntentTag.matched=true`
  with `confidence >= block.match.threshold` (or the
  `default_match_confidence` global fallback).
- `DIR-F-007` `kb-enricher` MUST **never** emit unresolved `{...}`
  placeholders into the typed text. If any placeholder is missing
  context, the stage skips injection (text passes through unchanged)
  and emits a warning.
- `DIR-R-004` `kb-enricher` MUST be pure template substitution — no
  LLM runtime calls.

## Scope

- **In:**
  - `holdspeak/plugins/dictation/builtin/__init__.py` — package
    marker (re-exports the two stage classes for convenience).
  - `holdspeak/plugins/dictation/builtin/intent_router.py`:
    - `IntentRouter` (`Transducer`).
      `id="intent-router"`, `version="0.1.0"`, `requires_llm=True`.
    - Constructor: `IntentRouter(runtime: LLMRuntime, blocks:
      LoadedBlocks, *, max_tokens: int = 128, temperature: float =
      0.0, prompt_builder: Callable[..., str] | None = None)`.
    - `run(utt, prior)` builds a prompt from `blocks` (description +
      examples + negative examples) and the utterance, calls
      `runtime.classify(prompt, schema)` where `schema =
      blocks.to_block_set()` compiled via
      `StructuredOutputSchema.from_block_set`. The returned dict is
      coerced to `IntentTag`; if anything goes sideways (runtime
      exception, JSON shape error, unknown block_id), the stage
      retries `classify` once, then on second failure returns a
      `StageResult` with `IntentTag(matched=False, block_id=None,
      confidence=0.0, raw_label=None, extras={})` and a
      structured warning. The stage **never raises** — the pipeline
      executor's error isolation is a fallback, not the primary
      contract.
    - The router's `text` field is the input text unchanged
      (router does not transform text — it only labels).
    - When `blocks.blocks == ()` the router short-circuits to a
      no-match `IntentTag` without calling the runtime (DIR-F-005's
      "scores against the union" is satisfied trivially when the
      union is empty).
  - `holdspeak/plugins/dictation/builtin/kb_enricher.py`:
    - `KbEnricher` (`Transducer`).
      `id="kb-enricher"`, `version="0.1.0"`, `requires_llm=False`.
    - Constructor: `KbEnricher(blocks: LoadedBlocks)`.
    - `run(utt, prior)` reads the most recent `IntentTag` from prior
      stage results. If absent, or `matched=False`, or below
      threshold, returns the input text unchanged with a metadata
      note explaining the no-op. Otherwise looks up the `Block` by
      `block_id`, builds the substitution context, and applies the
      template per `inject.mode` (append / prepend / replace).
    - Context resolution: a `_resolve_template(template, context)`
      helper walks each `{a.b.c}` placeholder, looks up the dotted
      path against the context dict, and substitutes the resolved
      value (string-coerced). If any placeholder is unresolved
      (missing key / `None` value), the stage **skips injection** —
      text passes through unchanged with a warning naming the
      offending placeholder (DIR-F-007).
    - Substitution context (per spec §8.3):
      `{raw_text: utt.raw_text, project: utt.project, intent:
      {extras: tag.extras, block_id: tag.block_id}}`.
  - `tests/unit/test_dictation_intent_router.py` — covers DIR-F-004
    (parse-failure retry then no-match), DIR-F-005 (taxonomy union),
    happy-path tag construction, runtime exception handling, empty
    `blocks` short-circuit, no LLM call when `requires_llm` semantics
    hold via the pipeline (verified at the pipeline level — here we
    just exercise `run()` directly).
  - `tests/unit/test_dictation_kb_enricher.py` — covers DIR-F-006
    (threshold gating using both per-block and default thresholds),
    DIR-F-007 (unresolved placeholder skip + warning), DIR-R-004 (no
    runtime is even injected — constructor takes no runtime arg),
    inject modes (append / prepend / replace), missing prior
    IntentTag → no-op, `extras` placeholder resolution.
- **Out:**
  - Controller wiring (HS-1-07).
  - CLI dry-run (HS-1-08).
  - Doctor checks (HS-1-09).
  - Network calls / cloud router (DIR-S-003 trivially satisfied — no
    network code is added here).
  - Multi-utterance state.

## Acceptance criteria

- [x] `holdspeak/plugins/dictation/builtin/intent_router.py` and
      `holdspeak/plugins/dictation/builtin/kb_enricher.py` exist.
- [x] Both stages structurally conform to the `Transducer` Protocol
      (`test_intent_router_conforms_to_transducer_protocol`,
      `test_kb_enricher_conforms_to_transducer_protocol`).
- [x] `IntentRouter.run` returns `matched=False, confidence=0.0`
      when the runtime raises on both attempts and never raises out
      (`test_runtime_exceptions_never_propagate`).
- [x] `IntentRouter` retries `classify()` exactly once on parse
      failure / unknown block_id / non-numeric confidence /
      non-dict response; second failure → no-match `IntentTag` + warning
      (`test_unknown_block_id_triggers_retry_then_no_match`,
      `test_invalid_confidence_triggers_retry`,
      `test_non_dict_response_triggers_retry`,
      `test_retry_recovers_on_second_attempt`).
- [x] Empty `blocks` short-circuits without calling the runtime
      (`test_empty_blockset_short_circuits_without_runtime_call`).
- [x] `KbEnricher` constructor takes no runtime argument
      (`test_kb_enricher_constructor_takes_no_runtime`); `requires_llm
      = False`.
- [x] `KbEnricher` no-ops on missing tag, `matched=False`, unknown
      block id, or below-threshold confidence — covered by four
      no-op tests.
- [x] `KbEnricher` honors per-block `match.threshold`, falling back
      to `default_match_confidence`
      (`test_per_block_threshold_overrides_default`,
      `test_at_or_above_threshold_applies_template`).
- [x] All three inject modes covered (append / prepend / replace).
- [x] Unresolved placeholders → injection skipped, warning naming the
      placeholder, no `{...}` ever leaks into output
      (`test_unresolved_placeholder_skips_injection`,
      `test_unresolved_when_project_is_none`,
      `test_no_unresolved_braces_ever_typed_smoke`).
- [x] `uv run pytest -q tests/unit/test_dictation_intent_router.py
      tests/unit/test_dictation_kb_enricher.py` → 29 passed.
- [x] Full regression: 877 passed, 13 skipped, 1 pre-existing
      hardware-only fail in
      `tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads`.

## Test plan

- **Unit:** the two new test files; ≥10 cases each.
- **Regression:** `uv run pytest -q tests/`.
- **Manual:** None (HS-1-08 dry-run is the manual path).

## Notes / open questions

- The router's prompt format is intentionally kept simple in HS-1-06
  (description + numbered examples + utterance + "respond with
  JSON"). It can evolve without breaking the contract — the
  constrained-decoding layer guarantees structure regardless of
  prompt phrasing.
- `_resolve_template` is implemented as a dedicated helper in
  `kb_enricher.py` rather than reusing `str.format` so that
  attribute access on real Python objects is impossible, even with
  a malicious context. The blocks loader (HS-1-05) already enforces
  that templates only contain dotted-name placeholders, so the
  resolver only has to handle that shape.
- `IntentTag.raw_label` is set to the `block_id` returned by the
  model when the dict is parseable. If the model returns
  `matched=false`, `raw_label` is set to whatever it returned (or
  `None`). Callers shouldn't rely on `raw_label` for logic — it's
  for telemetry and debugging.
