# HS-131-14 — hostile verification verdict

**Verdict: RATIFY FOR STORY CLOSE.**

## What was attacked

The independent pass tested the actual primary-tree implementation against the realistic failure modes in Articles V and XI:

- missing, forged, copied, released, stale, cross-child, wrong-context, cancelled, and incompatible handles;
- provider failure and provider-dialect retry through all fourteen builtin LLM plugins;
- host timeout before physical claim, timeout during a physical call, and a timed-out worker attempting late work;
- two concurrent calls sharing one handle, two sequential calls sharing one handle, and multiple plugins offered one child handle;
- deferred child receipt/projection behavior, segment-probe pre-admission construction, and provider-fallback reintroduction mutations;
- deletion of all plugin `_cached_provider` and `intel_call` side doors without plugin allowlisting.

## Defects found and repaired

### 1. Ambient host/plugin engine state could cross children

The original host stored a mutable `_llm_engine` and temporarily swapped each plugin's `_cached_provider`. `ThreadPoolExecutor` timeout does not stop the worker, so an abandoned worker could observe a later child's engine and context.

The repair is per-invocation `PluginDispatch`: an opaque handle issued over the exact runner-bound engine/context and carried only in that worker's private context copy. No host or plugin attribute stores it.

### 2. One handle allowed several physical completions

The first implementation allowed `PluginDispatch.chat()` to run repeatedly. A plugin loop or two concurrent callers could hide several provider attempts under one child/context/receipt.

The repaired handle is single-use. One lock guards a monotonic `LIVE -> IN-FLIGHT -> SPENT` state; exactly one caller may claim the physical completion. A dispatched chain must contain exactly one plugin. Retries receive a distinct handle under the runner's separately admitted `_r2` child.

### 3. Release and physical claim raced

A worker could validate, be preempted, lose authority through host timeout, then resume and start a physical request. The first cardinality repair still read timeout state and released in separate operations.

`PluginDispatch.release() -> bool` now atomically revokes the handle and reports whether the single completion was already claimed, under the same lock used by the claim. Host timeout performs one election: `claimed = dispatch.release()`. Unclaimed means an ordinary timeout with a mechanically guaranteed zero leaves; claimed means `ProviderIndeterminate` and no publication. Release never waits for the provider.

The deterministic barrier test parks the worker after diagnostic validation and before the atomic claim, lets the host time out and revoke, then resumes the worker. The result is an ordinary timeout, `plugin_dispatch_released`, and zero physical calls. Mutating the host back to a separate `calls` read and later release makes this test fail by observing a late provider call.

## Final focused proof

The independent verifier read the coherent patch and returned `RATIFY` after:

```text
159 passed in 1.73s
177 passed in 79.61s
164 passed in 2.27s
```

It also mechanically confirmed all fourteen builtin handlers re-raise `PLUGIN_INTEL_SIGNALS` before broad exception handling, and found no executable provider-construction fallback in the plugin modules, segment probe, or meeting startup glue.

The orchestrator independently reran the primary-tree hostile suite:

```text
159 passed in 1.74s
```

and a wider plugin/one-path sweep:

```text
566 passed in 79.56s
```

The Delivery Workbench capture after the full-gate regression repair closed with:

```text
811 passed in 106.10s
```

## Recorded observations, not blockers

- Python private helpers remain importable by convention. The charter explicitly permits a private, dominated construction body; the executable fence rejects any new product caller. No current uncensused caller was found.
- Segment-probe MIR admission is owned by HS-131-17. Until then meeting startup leaves the probe absent and follows the existing lexical route; it performs no pre-admission model work.
- Broader Phase-131 reviewers surfaced inherited service budget/cancellation and speech-session observations outside this diff. They are separately ledgered and are not represented as HS-131-14 fixes or regressions.

No current-diff realistic blocker remains.
