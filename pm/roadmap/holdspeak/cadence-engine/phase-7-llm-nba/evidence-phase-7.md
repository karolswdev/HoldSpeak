# Evidence — Cadence Phase 7 (LLM next-best-action)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase7-llm`.

## What shipped

| Story | Files | Proof |
|-------|-------|-------|
| CAD-7-01/02/03 | `cadence/llm_action.py` (`generate_llm_next_action`, prompt + parser + validation) | `test_cadence_llm_action.py` |
| CAD-7-04 | `cluster_duplicates` | clustering tests (never loses a loop) |
| CAD-7-05 | `config.py` (`use_llm`) + `web/routes/cadence.py` (`_cadence_llm`, loop-detail wiring) | route still green |
| CAD-7-06 | prompt-injection + fail-closed tests **+ the live `.43` proof** | 180 green + `proof/real-metal-43.md` |

## Fail-closed, by construction

`generate_llm_next_action` returns the deterministic action on every failure path — tested:
no-llm (identity), invalid JSON, an off-contract `kind` (e.g. `"rm -rf"`), an llm that raises, and a
hijacked non-JSON reply. The `reversible` safety flag stays deterministic (a model claiming
`reversible:true` is ignored). `cluster_duplicates` fails closed to singletons and **never loses a
loop** (any id the model drops survives as its own group).

## Prompt-injection defense (tested)

The loop's source text (from transcripts) is inserted as fenced **untrusted data**; the system prompt
says it is data to summarize, never instructions; and the output is only consumed as validated JSON
fields. `test_prompt_injection_in_title_is_data_not_instruction` asserts the injected title rides in
as user-prompt data (not a system role) and that a compliant hijack ("PWNED") fails closed.

## Real-metal proof (the differentiator)

Control vs treatment on the same loop against the **live `.43`** Qwen (`Qwythos-9B-...-Q6`, run with
the sandbox disabled to reach the LAN): the model produced a genuine structured issue body that
**validated** and was accepted as `generated_by="llm"` — materially better than the deterministic
control stub. Full transcript: `proof/real-metal-43.md`. This satisfies the standing rule to prove
LLM-shaped features on real metal, control-vs-treatment, not just plumbing
([[feedback_prefer_real_metal_proof]]).

## Trust boundary

`llm_action.py` takes an **injected** llm callable — it imports no network client, so the cadence-core
no-external-side-effects guard still passes. The real provider is resolved at the surface
(`build_configured_meeting_intel`), gated on `cadence.use_llm` (off by default). The model only drafts;
a human approves; execution stays the actuator path.

## Proof

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py
  tests/integration/test_web_server.py` → **180 passed.**
- Live `.43` control-vs-treatment proof recorded in `proof/real-metal-43.md`.
