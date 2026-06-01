# HS-16-02 Evidence — LLM Capability Gate

**Date:** 2026-06-01.
**Story:** [story-02-llm-capability-gate.md](./story-02-llm-capability-gate.md).

## Implementation Evidence

**`holdspeak/intel.py`** — new `resolve_llm_capability(meeting_config) -> bool`:
returns `True` iff `intel_enabled` is set **and** `resolve_intel_provider(...)`
resolves a provider. The check is cheap (config + file existence, no model
warmup). Any failure — including a malformed config or a raising resolver — is
caught and yields `False`, so host construction never crashes on it.

**`holdspeak/web_runtime.py`** — at the one runtime `PluginHost(...)` site
(`run_web_runtime`), the capability is resolved before construction and passed in:

```python
llm_capability_enabled = resolve_llm_capability(config.meeting)
log.info(f"intel.llm_capability enabled={llm_capability_enabled}")
plugin_host = PluginHost(
    default_timeout_seconds=0.35,
    enabled_capabilities={"llm"} if llm_capability_enabled else None,
)
```

`_get_runtime_status()` now includes `"llm_capability_enabled": bool`, so
`GET /api/runtime/status` surfaces it.

**`holdspeak/commands/doctor.py`** — the only other `PluginHost()` call is a
throwaway used solely to read the metrics-schema shape; it never executes a
plugin, so it needs no capability wiring. Documented inline as exempt.

The host already enforces capabilities at execute time
(`host.py:376` → `status="blocked"`, `error="Missing capabilities: llm"`); this
story only supplies the `enabled_capabilities` set. No host changes were needed.

## Tests

New `tests/unit/test_plugin_host_llm_capability.py` (8 cases):
- `resolve_llm_capability`: provider resolves → `True`; unresolved → `False`;
  `intel_enabled=False` → `False` (resolver not even called); resolver raises →
  `False` (non-fatal).
- `PluginHost` gate: an `["llm"]` plugin runs with the capability and is
  `blocked`/"Missing capabilities: llm" without it; the real
  `mermaid_architecture` blocks without the capability and passes the gate
  (status ≠ `blocked`) with it.

`tests/unit/test_web_runtime.py` — extended the runtime-status assertion:
`llm_capability_enabled` is present and a `bool` (and `False` for the
intel-disabled fixture).

```bash
uv run pytest -q tests/unit/test_plugin_host_llm_capability.py tests/unit/test_plugin_host.py tests/unit/test_web_runtime.py tests/unit/test_intel_cloud.py
# 33 passed in 1.04s

uv run pytest -q --ignore=tests/e2e/test_metal.py
# 1899 passed, 13 skipped in 61.81s   (was 1891; +8 cases)
```

`ruff check` on the changed files: **All checks passed!**

## Live runtime check (real self-hosted LLM)

Against the configured self-hosted endpoint (`http://192.168.1.43:8080/v1`,
`Qwen3.5-9B-UD-Q6_K_XL`, **no** `OPENAI_API_KEY` set — relying on the
self-hosted-key fix in commit `7f03008`):

```text
resolve_llm_capability(real config) -> True
```

Driving the now-unblocked `MermaidArchitecturePlugin` against that endpoint with
a short architecture transcript produced a valid, accurate diagram:

```text
summary: API Gateway routes traffic to Auth, Billing, and Notifications microservices ...
confidence_hint: 1.0
has mermaid block: True
---
flowchart TD
    API[API Gateway] --> Auth[Auth Service]
    API --> Billing[Billing Service]
    API --> Notif[Notifications Service]
    subgraph DataStores [Data Stores]
        Postgres[(PostgreSQL)]
        Redis[(Redis)]
        Queue[Worker Queue]
    end
    Auth -->|Shared DB| Postgres
    Billing -->|Shared DB| Postgres
    Notif -->|Cache/Session| Redis
    Notif -->|Async Tasks| Queue
```

This confirms the gate unblocks the real feature and that the LLM emits clean,
parseable Mermaid — de-risking HS-16-03 (body splice) and HS-16-04 (SVG render).

## Result

`mermaid_architecture` is no longer permanently `blocked`: when an intel provider
resolves, the runtime host enables the `"llm"` capability and the plugin runs;
when no provider resolves, construction still succeeds and the plugin cleanly
blocks at execute time. Phase 16 is 2/5. **Next: HS-16-03** — splice the fenced
```mermaid block into the synthesized artifact body.

**Note (carried forward, not a regression):** the local `127.0.0.1:8081` server
(Qwen3.5-9B **Q4**) leaks chain-of-thought into empty `content`; config now
points at the `.43` **Q6** endpoint, which returns clean content. Calibration
across model sizes remains HS-16-05's concern (and can be kept light per the
project's no-spike preference).
