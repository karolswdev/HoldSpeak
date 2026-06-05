# HS-39-03 — Model-assisted target detection

- **Project:** holdspeak
- **Phase:** 39
- **Status:** backlog
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

- [ ] `target_detect_llm_enabled` (default `false`) + `target_detect_llm_below`
      threshold exist on the dictation config and validate.
- [ ] With the flag off (default), target detection is **byte-identical** to
      pre-story (asserted with a fake runtime present).
- [ ] With the flag on and heuristic confidence below threshold, the LLM
      classifier is consulted and its (enum-constrained) result is used.
- [ ] With heuristic confidence at/above threshold, the LLM is **not** called
      (no needless latency).
- [ ] `target_profile_override` overrides both heuristic and LLM in all cases.
- [ ] LLM failure/unavailability degrades to the heuristic result; the typing
      path never errors on detection.
- [ ] The decision source (heuristic | llm | override) + confidence appear in
      the readiness / dry-run output.

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

- Constrain the classification output to the profile enum (reuse the
  `StructuredOutputSchema` / grammar machinery the intent router already uses,
  or a minimal enum constraint) so the fallback can't emit a non-profile
  string.
- Keep the prompt cheap (`max_tokens` small) — this fires on the *unsure* tail,
  not every utterance, but it's still on the live typing path.
- Canon: §9.8 — the runtime must not make network calls beyond the configured
  endpoint; the `openai_compatible` backend is the user's configured endpoint,
  so this respects DIR-S-003. Record if any prompt would carry sensitive
  window text — gist/redact as needed.
