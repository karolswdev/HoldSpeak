# HS-151-01 — The honest dispatch (structured output + the wiring recipe)

- **Project:** holdspeak
- **Phase:** 151
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-151-03
- **Owner:** unassigned

## Problem

Cloud intel dispatch (holdspeak/intel/engine.py:294-303) sends no
request-level response_format — it trusts the prompt's "return
ONLY JSON" plea. Probe 2 (assets/metal-probes.md) proved the
owner's REAL resident server (llama.cpp with a server-level
--json-schema pin) swallows that plea and returns {"line": ...}:
production intel against the real box parses NOTHING. Separately,
the modern wiring (profile + meeting.deferred_analysis assignment)
has no fresh-HOME recipe — the P55 harness kwargs are dead.

## Scope

### In

1. The cloud branch of `_chat_completion_text` sends request-level
   `response_format: {type: "json_schema", json_schema: ...}`
   derived from the intel shape (topics / action_items{task,
   owner, due} / summary — read the shape from parsing.py, keep
   ONE source of truth). Local provider untouched. Honest
   degradation: an endpoint that 400s on response_format retries
   ONCE without it — COUNSEL M1: via a NAMED signal and a SECOND
   admitted child (the ProviderCompatibilityRetry pattern,
   runtime_openai_compatible.py:159-162 is the model); never two
   physical requests under one receipt. COUNSEL M2: the schema is
   ONE constant in parsing.py — the prompt stringifies it, the
   response_format wraps it, the adapter references it. COUNSEL
   M4: the constant carries the named-owner shape
   (owner: string|null) from the start.
2. A schema-pinned-server regression pin: a stub OpenAI-compatible
   server that mimics the pin (returns {"line"} for bare requests,
   honors request-level json_schema) — the test reproduces the
   defect against the old dispatch shape and proves the fix.
3. The wiring recipe: a small `scripts/wire_metal_intel.py`
   (stdlib + product imports) that, against a target HOME, creates
   the openAICompatible profile (base_url configurable, default
   http://192.168.1.43:8080/v1) and the meeting.deferred_analysis
   assignment through the REAL adoption service — the exact
   composition every 151 rig and the attended leg reuse. Idempotent,
   prints what it did.

### Out

- Any change to the local GGUF provider or the prompt (story 02).
- Touching the resident 8080 server's configuration.

## Acceptance criteria

1. The pin test proves both directions (old shape fails against
   the stub pin; new shape succeeds; 400-fallback fires once with
   a receipt).
2. `wire_metal_intel.py` on a fresh HOME yields a board-ready
   binding: `process_next_intel_job` reaches the endpoint (proven
   in story 03; here a dry resolve through the binder suffices).
3. Focused suites green; no census/guard drift unaccounted.

## Test plan

New unit file for the dispatch + stub server; binder resolve test;
focused runs only (workers) — the orchestrator runs the wider net.
