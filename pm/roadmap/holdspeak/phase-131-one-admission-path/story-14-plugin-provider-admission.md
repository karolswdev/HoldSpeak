# HS-131-14 — Plugins receive admitted intelligence

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-02, HS-131-08
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

Fourteen builtin plugins and `segment_probe` can construct a configured provider
through `_cached_provider` and call `_chat_completion_text` directly. That
fallback bypasses the host-injected admitted meeting child, silently rereads
mutable configuration, and hides physical attempts inside plugin execution.
Plugins are consumers of intelligence, not provider adapters, and cannot enter
the fence allowlist under Constitution Articles II.2, V.4, and XI.1–3.

## Scope

### In

- Remove the default-provider construction family from all fourteen builtin
  plugins and `holdspeak/plugins/segment_probe.py`.
- Make provider-bearing plugin execution require the host-injected engine or
  narrow dispatch handle issued for the currently claimed
  `inference.invoke@1` child. The handle must retain the runner's exact opaque
  context, frozen revision, destination, warrant basis, cancellation signal,
  and attempt ordinal.
- Preserve deterministic or lexical plugin behavior that performs no model
  work. A plugin that needs intelligence but receives no admitted handle must
  refuse by name or report the existing non-model limitation; it may not create
  a provider as fallback.
- Keep each physical retry/fallback as a separately admitted child and immutable
  terminal receipt. A plugin loop may own several children but may not absorb
  them into its plugin-run receipt.
- Delete or privatize the uncontextual
  `build_configured_meeting_intel()` construction body after the last plugin
  caller migrates. The exact context-validating factory remains the only
  provider-construction entrance.
- Cover live and deferred meeting plugin execution, cancellation, missing
  injection, incompatible engines, and provider failure in the literal-spine,
  provenance, and cardinality suites.
- Remove all `plugin-default-provider` and remaining provider-construction
  finding pins from the census without adding plugin scopes to
  `ADAPTER_ALLOWLIST`.

### Out

- New plugin capabilities, prompts, output schemas, or UI.
- Turning plugins into independent authority principals.
- A generic ambient provider singleton.
- Preserving `_cached_provider` as a compatibility path.

## Acceptance criteria

- [x] No plugin constructs `MeetingIntel`, calls a configured provider factory,
  or invokes `_chat_completion_text` outside an admitted dispatch handle.
- [x] All provider-bearing plugin calls name the correct meeting/deferred parent,
  exact deployment revision, child warrant basis, attempt ordinal, and terminal
  receipt.
- [x] Missing, stale, forged, cross-child, or incompatible injected handles
  refuse before physical model work.
- [x] Cancellation, session stop, and deferred-parent closure prevent late
  plugin output from publishing.
- [x] Deterministic plugin paths remain usable without minting inference
  children.
- [x] The one-path census removes all 30 `plugin-default-provider` sites and
  related uncontextual construction sites with zero new findings, exceptions,
  or unregistered execution.

## Test plan

- Unit: parameterize all fifteen plugin modules over admitted handle, missing
  handle, wrong revision, cancellation, provider failure, and deterministic
  no-model behavior; run the one-path context/census/cardinality suites.
- Mutation: restore one `_cached_provider` plus a first-class
  `_chat_completion_text` reference and prove both exact named census failures.
- Integration: run one live and one deferred provider-bearing plugin through the
  real meeting host and inspect child, receipt, and staged projection rows.
- Manual / device: n/a; HS-131-12 performs the assembled live-model proof.

## Notes / open questions

The meeting host already owns admission and engine construction. This story
finishes that dependency-injection contract; it does not create a plugin-owned
runner or a new authority layer.
