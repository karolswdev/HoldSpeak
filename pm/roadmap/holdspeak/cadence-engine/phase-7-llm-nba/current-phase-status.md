# Cadence Phase 7 — LLM next-best-action

**Status:** done (built + tested + **real-metal proven on `.43`**). **Start here:** `../README.md`.
Builds on Phases 1–6 (merged).

**Last updated:** 2026-06-28 (Phase 7 shipped: the structured-JSON LLM next-action generator,
fail-closed, gated, with a control-vs-treatment proof on the live `.43` Qwen).

## Objective

Upgrade the prepared next-action from a deterministic *stub* to a *drafted* one — a real issue body,
a Slack update, a smart agent reply — using the configured LLM. The model only **drafts** text a
human then approves; it never executes. The output is structured JSON, validated, and **fail-closed**
to the deterministic action on any failure.

## What shipped

- **`cadence/llm_action.py`**: `generate_llm_next_action(loop, *, llm)` — builds a safe prompt (the
  loop's source text inserted as fenced **untrusted data**, never instructions), calls the injected
  `llm`, parses + validates the JSON (kind ∈ allow-list, non-empty title), and **fails closed** to
  `generate_next_action` on no-llm / invalid JSON / off-contract / any error. The `reversible` safety
  flag stays deterministic (the model can't relax it). `cluster_duplicates` groups same-work loops
  (fail-closed to singletons; never loses a loop). `next_action_for` is the capability-gated entry.
- **The gate**: `CadenceConfig.use_llm = False` (off by default). The web **loop-detail** route
  resolves the user's configured provider (`build_configured_meeting_intel().run_prompt`) into the
  `llm` only when the gate is on; the loop list + brief stay deterministic (one model call per
  inspected loop, not per list).
- **Prompt-injection defense** is structural: source text is data inside a fence, the system prompt
  says so, and the output is only ever consumed as validated JSON fields — a hijacked non-JSON reply
  fails closed (tested).

## Real-metal proof (the differentiator)

Control (deterministic) vs treatment (LLM) on the same loop, against the live `.43` Qwen
(`Qwythos-9B-...-Q6`): the model returned a genuine structured issue body (Context / Objective /
Requirements / Notes) that **validated** and was accepted as `generated_by="llm"`, materially better
than the control stub. Transcript: `proof/real-metal-43.md`
([[feedback_prefer_real_metal_proof]] — proven on metal, not plumbing).

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-7-01 | Structured-JSON prompt contract + parser | done |
| CAD-7-02 | `generate_llm_next_action` (fail-closed validation) | done |
| CAD-7-03 | Issue / Slack / agent-reply drafting (via the contract) | done |
| CAD-7-04 | `cluster_duplicates` (never loses a loop) | done |
| CAD-7-05 | The capability gate (`use_llm`) + the loop-detail wiring | done |
| CAD-7-06 | Prompt-injection + fail-closed tests **+ the real-metal `.43` proof** | done |

## Exit criteria

- An LLM-drafted next action validates and is accepted; every failure path (no llm / invalid / off
  contract / error) falls back to the deterministic action; the injected source text is data.
- Off by default (`use_llm`); the deterministic baseline needs no model.
- `uv run pytest -q` green (180 cadence/web tests) + the live `.43` control-vs-treatment proof.
  **Next: Phase 8 (hardening + dogfood) closes the program.**
