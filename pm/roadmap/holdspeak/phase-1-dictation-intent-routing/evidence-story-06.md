# Evidence — HS-1-06 (Built-in stages)

**Story:** [story-06-builtin-stages.md](./story-06-builtin-stages.md)
**Date:** 2026-04-25
**Status flipped:** in-progress → done

## What shipped

- `holdspeak/plugins/dictation/builtin/__init__.py` — package marker
  re-exporting `IntentRouter` and `KbEnricher`.
- `holdspeak/plugins/dictation/builtin/intent_router.py` —
  LLM-driven router. Builds a prompt from the loaded blocks
  (description + examples + counter-examples + extras-schema hints +
  utterance), calls `runtime.classify(prompt, schema)`, and coerces
  the dict into an `IntentTag`. Validates that `block_id` is in the
  taxonomy and `confidence ∈ [0.0, 1.0]`. On any failure (exception,
  bad shape, unknown block id, non-numeric confidence, non-dict
  return), retries `classify()` exactly once and returns
  `IntentTag(matched=False, confidence=0.0)` if the retry also fails.
  Empty `blocks` short-circuits without calling the runtime. The
  stage **never raises** out of `run()`.
- `holdspeak/plugins/dictation/builtin/kb_enricher.py` — pure
  template substitution. Constructor takes no runtime
  (`DIR-R-004`). Reads the most recent `IntentTag` from prior
  results; gates on `matched` + `confidence >= threshold`
  (per-block `match.threshold` falling back to
  `default_match_confidence`); resolves the block's `inject.template`
  against a context built from the utterance + intent extras, then
  applies the configured `inject.mode` (append / prepend / replace).
  Custom `_resolve_template` walks `{a.b.c}` placeholders against
  dict-like context only — `str.format` is never used, so no
  attribute or item access on Python objects is reachable. Any
  unresolved placeholder skips injection entirely and emits a
  warning naming the offending name (DIR-F-007).
- `tests/unit/test_dictation_intent_router.py` — 11 cases.
- `tests/unit/test_dictation_kb_enricher.py` — 18 cases.

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-F-004` Garbled output → matched=false after retry | `test_unknown_block_id_triggers_retry_then_no_match`, `test_invalid_confidence_triggers_retry`, `test_non_dict_response_triggers_retry`, `test_runtime_exceptions_never_propagate` |
| `DIR-F-005` Router scores against full taxonomy union | `test_happy_path_returns_intent_tag` (asserts `metadata.taxonomy_size == 2`), `test_prompt_includes_block_descriptions_and_examples` |
| `DIR-F-006` kb-enricher only acts above threshold | `test_below_default_threshold_no_op`, `test_per_block_threshold_overrides_default`, `test_at_or_above_threshold_applies_template`, `test_no_intent_tag_no_op`, `test_unmatched_intent_no_op`, `test_unknown_block_id_no_op` |
| `DIR-F-007` No unresolved `{...}` ever typed | `test_unresolved_placeholder_skips_injection`, `test_unresolved_when_project_is_none`, `test_no_unresolved_braces_ever_typed_smoke` |
| `DIR-R-004` kb-enricher is pure substitution (no runtime) | `test_kb_enricher_constructor_takes_no_runtime` (asserts the constructor signature has no `runtime`/`llm` parameter), `requires_llm == False` |

## Test output

### Targeted (built-in stages)

```
$ uv run pytest -q tests/unit/test_dictation_intent_router.py tests/unit/test_dictation_kb_enricher.py
.............................                                            [100%]
29 passed in 0.05s
```

### Full regression

```
$ uv run pytest -q tests/ --timeout=30
...
1 failed, 877 passed, 13 skipped, 3 warnings in 21.80s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

Pre-existing hardware-only Whisper-loader failure, unrelated. Pass
delta: 848 → 877 (+29 new unit cases).

## Files in this commit

- `holdspeak/plugins/dictation/builtin/__init__.py` (new)
- `holdspeak/plugins/dictation/builtin/intent_router.py` (new)
- `holdspeak/plugins/dictation/builtin/kb_enricher.py` (new)
- `tests/unit/test_dictation_intent_router.py` (new)
- `tests/unit/test_dictation_kb_enricher.py` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-06-builtin-stages.md` (new — story authored, status flipped to done in same commit)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-06.md` (this file)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- The router uses `time.perf_counter` directly for `elapsed_ms`. It
  doesn't take a clock injection because the timing is informational
  metadata; the deterministic clock seam lives at the pipeline level
  (HS-1-03) where total-elapsed is observed.
- The kb-enricher's `_lookup` treats `None` values as unresolved.
  This is deliberate: a block template referencing
  `{project.kb.task_focus}` should not silently inject the literal
  string `"None"` when the KB has no current task. This is a
  conservative DIR-F-007 reading; a future opt-in `null_as_blank`
  flag could relax it.
- The router doesn't currently parse `extras` against the per-block
  schema (it accepts the runtime-returned dict as-is, since the
  constrained-decoding layer is responsible for shape). If runtime
  drift ever produces extras outside the enum, the GBNF / outlines
  artifact compiled from the same `BlockSet` is the fix point — not
  a runtime-side schema check.
