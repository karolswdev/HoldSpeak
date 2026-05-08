# HS-16-02 — LLM capability gate wired at host instantiation

- **Project:** holdspeak
- **Phase:** 16
- **Status:** backlog
- **Depends on:** HS-16-01
- **Unblocks:** HS-16-05
- **Owner:** unassigned

## Problem

`MermaidArchitecturePlugin` (HS-16-01) declares
`required_capabilities=["llm"]`. The plugin host already enforces
capabilities at execute time
(`holdspeak/plugins/host.py:196-203,376-397`): if the host's
`enabled_capabilities` set is missing a required capability, the
plugin returns `status="blocked"` with a structured error and is not
called.

What's missing is the wiring that turns on the `"llm"` capability
when an intel provider is actually configured. Today, the host is
constructed without `enabled_capabilities` populated — the new
plugin would always be blocked. Conversely, if we hardcode `"llm"`
on, an install with no LLM configured would crash at
`run()` time inside the plugin.

This story finds the host instantiation site, plumbs through the
intel-provider resolution, and adds `"llm"` to
`enabled_capabilities` iff a provider resolves successfully.

## Scope

- **In:**
  - Locate every `PluginHost(...)` constructor call in the codebase
    (`holdspeak/web_runtime.py`, `holdspeak/controller.py`,
    `holdspeak/meeting_session.py`, anywhere else found by
    `rg "PluginHost\("`).
  - At each site, before constructing the host, attempt
    `resolve_intel_provider(...)` from the existing config. If it
    returns a usable provider, include `"llm"` in the host's
    `enabled_capabilities`. If it raises or returns `None`, omit it.
  - Catch the resolution exception narrowly — failure to resolve
    is **not** a fatal startup error; the host still constructs
    without the capability and `mermaid_architecture` cleanly
    blocks at execute time.
  - Surface the resolved state in
    `/api/runtime/status` so the user / web UI can see whether
    LLM-backed plugins are currently enabled. Add a new field
    `llm_capability_enabled: bool` next to the existing intel
    runtime status fields.
  - Unit test: new
    `tests/unit/test_plugin_host_llm_capability.py` with two
    cases:
    1. Intel provider resolves → capability set contains `"llm"`
       → executing `mermaid_architecture` does not return
       `status="blocked"` for capability reasons (it may still
       defer-queue or succeed; the test isolates the capability
       check by registering a trivial plugin with the same
       capability declaration).
    2. Intel provider fails to resolve → capability set does not
       contain `"llm"` → executing `mermaid_architecture` returns
       `PluginRunResult(status="blocked", error=~"Missing
       capabilities: llm")`.
  - Integration test extension (no new file): existing
    `test_runtime_status` (or the closest equivalent) gains an
    assertion that `llm_capability_enabled` is present and is a
    `bool`.

- **Out:**
  - Per-plugin capability declarations beyond `"llm"`. The
    capability-gate machinery already exists; only the LLM gate
    is needed for this phase.
  - UI surface for "LLM disabled — diagram artifacts won't be
    generated." A status field is enough; the UI follow-up is a
    separate story if it's ever needed.
  - Switching providers at runtime (the user changes intel config
    while HoldSpeak is running). The host's
    `enabled_capabilities` is set at construction; runtime swap
    is a separate problem that touches more than just this
    capability.

## Acceptance criteria

- [ ] Every `PluginHost(...)` instantiation site adds `"llm"` to
  `enabled_capabilities` iff `resolve_intel_provider(...)`
  returns a usable provider.
- [ ] When the provider can't resolve, host construction does not
  raise — the host is built without the capability.
- [ ] `GET /api/runtime/status` includes `llm_capability_enabled:
  bool`.
- [ ] `tests/unit/test_plugin_host_llm_capability.py` runs ≥ 2
  cases green.
- [ ] No regression: existing intel-runtime tests
  (`tests/integration/test_intel_runtime*.py` if present, plus
  `tests/unit/test_plugin_host*.py`) stay green.

## Test plan

- Unit:
  `uv run pytest -q tests/unit/test_plugin_host_llm_capability.py
  tests/unit/test_plugin_host.py`.
- Integration:
  `uv run pytest -q tests/integration/` (sweep; specifically
  whatever covers `/api/runtime/status` today).
- Manual: with an OpenAI key configured, hit
  `/api/runtime/status` — expect `"llm_capability_enabled":
  true`. Without one, expect `false`.

## Notes / open questions

- If `resolve_intel_provider` does I/O (e.g., the local-llama-cpp
  path tries to load a model file), this test path could be slow
  / flaky. Keep the resolution lazy / cheap at host-construction
  time — only check whether a provider *would* resolve, not
  actually warm a model. The existing
  `get_intel_runtime_status(...)` may be the right cheaper check.
- A future phase might split the capability further (`llm_local`
  vs `llm_cloud`) so plugins can declare which they tolerate. Out
  of scope here; one capability is enough to unblock HS-16-01.
- Decide carefully whether to log a one-line warning at startup
  when the capability is disabled (helps the user notice
  misconfiguration) vs staying silent (avoids log noise on
  intentional local-only setups). Default: structured-log
  `intel.llm_capability` with `enabled: bool` once at startup,
  no repeats.
