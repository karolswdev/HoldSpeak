# Real-metal proof — CAD-7 LLM next-action on `.43`

**Date:** 2026-06-28. **Endpoint:** `http://192.168.1.43:8080/v1/chat/completions`.
**Model:** `Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf` (self-hosted llama.cpp).
**Method:** control (deterministic `generate_next_action`) vs treatment (`generate_llm_next_action`
with the live `.43` model), same loop. Run with the sandbox disabled (LAN unreachable otherwise,
[[reference_lan_llm_endpoint]]).

## Loop

`Add a watchdog around meeting intel queue failures` · owner Karol · due 2026-06-30 · project holdspeak.

## CONTROL (deterministic, no model)

```
kind: create_issue | by: deterministic
title: File an issue: Add a watchdog around meeting intel queue failures
```

(The deterministic body is a templated stub: title + owner/due/source.)

## TREATMENT (LLM on .43, real metal)

```
kind: create_issue | by: llm
title: Add watchdog for meeting intel queue failures
body:
  ## Context
  From the Platform sync: we need a watchdog around meeting intel queue failures.

  ## Objective
  Implement a monitoring mechanism to detect and alert on failures in the meeting intel queue.

  ## Requirements
  - Detect queue processing failures
  - Alert relevant stakeholders
  - Provide visibility into failure rates

  ## Notes
  This is a new feature request; no existing implementation details were provided.
```

## Verdict

**LLM-drafted (treatment differs, validated).** The model returned a genuine, structured issue body
that **passed the schema validation** (`kind ∈ allow-list`, non-empty title) and was accepted as a
`generated_by="llm"` action. The treatment is materially better than the control stub — a real,
ready-to-approve draft — proving the feature on real metal, not just plumbing
([[feedback_prefer_real_metal_proof]]). The `reversible` safety flag stayed deterministic (the model
cannot relax it). Fail-closed behavior (invalid JSON / off-contract / endpoint down → the control
action) is locked by the hermetic tests in `tests/unit/test_cadence_llm_action.py`.
