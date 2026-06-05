# HS-39-03 — Model-assisted target detection

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** none
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Target-profile detection is heuristic + OS hints
(`holdspeak/target_profile.py`: macOS osascript, Linux x11) returning a
confidence ~0.74–0.92. Phase 19 flagged automatic detection as **still
experimental** on constrained Linux/Wayland and agent-CLI setups, where active
window inference is unreliable. Manual override exists but is a per-session
chore. There is no fallback that *reasons* about the target when the heuristic
is unsure.

## Scope

- In:
  - An **opt-in** model-assisted fallback in target resolution: when the
    heuristic confidence is below a configurable threshold (e.g.
    `target_detect_llm_below: float`), call the LLM runtime to classify the
    target profile from the available signals (window/app hints + recent agent
    context), constrained to the known profile enum.
  - A default-off flag (`target_detect_llm_enabled: bool = False`) on the
    dictation config.
  - Manual override (`target_profile_override`) **always wins** over both the
    heuristic and the LLM fallback.
  - Graceful degradation: any runtime failure/unavailability falls back to the
    heuristic result (never errors the typing path).
  - The dry-run / readiness surface shows which detector decided (heuristic
    vs llm vs override) + the confidence.
- Out:
  - Per-app automation rules / learned per-app mappings (Phase 19 decision
    upheld; correction memory HS-39-02 covers the learning angle).
  - Replacing the heuristic — the LLM is a *fallback*, not the primary.
  - New profile enum values.

## Acceptance criteria

- [x] `target_detect_llm_enabled` (default `false`) + `target_detect_llm_below`
      (default `0.8`, validated `[0.0, 1.0]`) exist on the dictation config. —
      `config.py`, `test_target_detect_llm_defaults`,
      `test_target_detect_llm_below_out_of_range_rejected`.
- [x] With the flag off (default), detection is **byte-identical** (same object
      returned even with a fake runtime present). —
      `test_model_assisted_disabled_is_noop`.
- [x] Flag on + heuristic confidence below threshold ⇒ the LLM is consulted and
      its enum-validated result is used (source `llm`, confidence 0.7). —
      `test_model_assisted_fires_below_threshold`.
- [x] Heuristic confidence at/above threshold ⇒ the LLM is **not** called. —
      `test_model_assisted_skips_at_or_above_threshold`.
- [x] `target_profile_override` (and a user `correction`) outrank the LLM. —
      `test_model_assisted_override_always_wins`,
      `test_model_assisted_skips_user_correction`.
- [x] LLM failure / no-runtime / unparseable output degrades to the heuristic;
      detection never raises. — `test_model_assisted_degrades_on_runtime_error`,
      `test_model_assisted_no_runtime_is_noop`,
      `test_model_assisted_ignores_unparseable_choice`.
- [x] The decision source (`heuristic`→`hints` | `llm` | `override` |
      `correction`) + confidence are on `TargetProfile.to_dict()`, which the
      dry-run returns as `target` (so a `llm`-sourced result is visible).

## Test plan

- Unit: `tests/unit/test_target_profile.py` (or new
  `test_target_profile_llm.py`) — flag-off byte-identical, below-threshold
  calls LLM, at-threshold skips LLM, override wins, failure degrades.
- Integration: `tests/integration/test_web_dictation_*api.py` — readiness/
  dry-run reports the decision source.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: optional — confirm on the reference Mac that a genuinely
  ambiguous window triggers the fallback and resolves sensibly. Not a gate.

## Notes / open questions

- **Enum constraint — resolved at parse, not decode.** The runtime's
  constrained `classify` is block/extras-shaped (coupled to `BlockSet`), so
  reusing it for a target enum was awkward. The fallback uses the freeform
  `rewrite` seam and **validates** the answer against the profile enum
  (`_parse_target_choice`), degrading to the heuristic on anything invalid —
  the model can never produce a non-profile result downstream. Decode-time
  constraint via a generic enum schema is a possible later refinement.
- **Ordering:** detect → `apply_target_correction` → `apply_model_assisted_target`.
  A user correction (confidence 0.95, source `correction`) is therefore not
  overridden by the model, and the model only fires on a genuinely
  low-confidence heuristic.
- Keep the prompt cheap (`max_tokens` small) — this fires on the *unsure* tail,
  not every utterance, but it's still on the live typing path.
- Canon: §9.8 — the runtime must not make network calls beyond the configured
  endpoint; the `openai_compatible` backend is the user's configured endpoint,
  so this respects DIR-S-003. Record if any prompt would carry sensitive
  window text — gist/redact as needed.
