# HS-131-10 — model-execution inventory and blocking findings

**Generated from:** `tests/unit/test_one_path_census.py` over production
`holdspeak/**/*.py` (tests excluded).

**Census date:** 2026-08-12.
**Disposition:** **BLOCKED; FIVE-STORY AMENDMENT WAVE IN PROGRESS.** These are
findings, not adapter exceptions. The owner chartered HS-131-13 through HS-131-17
to delete or admit every family. HS-131-13 is complete in the current tree;
HS-131-10 cannot close until the remaining four amendments land and the census
returns zero findings.

## Current census result — after HS-131-13

| Bucket | Function scopes | Executable sites |
|---|---:|---:|
| `AUTHORIZED_GATEWAY` | 2 | 1 context mint |
| `CLAIM_WITNESS_MINT` | 2 | 2 witness-issuer sites |
| `GATEWAY_FACTORY_BINDING` | 1 | 1 default-factory binding |
| `ADAPTER_ALLOWLIST` | 55 | 68 |
| `ADMITTED_SEAM_CALLERS` | 15 | 24 |
| `NAMED_FINDINGS` | — | 38 |
| Unregistered | — | **0** |
| **Total** | — | **134** |

HS-131-13 reduced the checkpoint baseline from **145 to 134 executable sites**,
**48 to 38 findings**, and **11 to 8 families**. It removed the two Cadence
findings by admission, deleted the two Decisions-route findings and one dormant
Delivery finding, deleted all five `build_intel_for_target` findings, and removed
that retired factory's final non-finding adapter site. Nothing moved to an
allowlist, and zero unregistered sites remain.

The authorized gateway is exactly `InferenceRunner._attempt` and
`InferenceRunner._dispatch`; public `InferenceRunner.invoke` only orchestrates
the one permitted compatibility follow-up and names no physical target. The
one-shot issuer installation at `ExecutorPlane` module scope, witness issuance
in `ExecutorPlane.claim`, and default-factory reference in
`InferenceRunner.__init__` are classified separately, not as adapters. Every
allowlisted factory validates the opaque, runner-issued `DispatchContext`
before construction; execution leaves are reachable only through the dispatch
context carried by that admitted child. A context consumes the single-use
witness from the successful claim and binds that exact child operation, its
immutable deployment revision, destination, positive attempt ordinal, and
child warrant basis. Missing, null, duck-typed, directly constructed, copied,
wrong-operation, wrong-revision, wrong-destination, wrong-attempt, invented,
and replayed contexts refuse by name before physical work.

The census recognizes existing-client SDK calls and first-class references such
as `client.chat.completions.create`, including literal
`getattr(receiver, "model_verb")` and SDK-chain getters regardless of the
container that holds them, without classifying availability probes or unrelated
repository/store `.create` methods. Physical cardinality is counted at the cloud
SDK, llama.cpp, mesh enqueue, and Whisper backend edges—not at engine
construction.

## Exact remaining blocking ledger — 8 families, 38 pinned sites

### 1. `dormant-mir` — inventoried branch, 0 executable sites

- `holdspeak/meeting_session/session.py` — the `mir_routing_enabled=True`
  branch is dormant today but would route model work outside the admitted
  meeting-child seam if enabled.

A latent side door is still a side door; either delete it or admit every MIR
attempt under the meeting session. Owned by HS-131-17.

### 2. `dictation-dry-run` — 1 site

- `holdspeak/web/routes/dictation/_helpers.py:541` — `build_pipeline`

The route constructs a model-bearing pipeline with no authenticated speech
session admission. Owned by HS-131-15.

### 3. `dictation-command` — 1 site

- `holdspeak/commands/dictation.py:79` — `build_pipeline`

The CLI constructs the same model-bearing pipeline without an authenticated
command parent or frozen plan. Owned by HS-131-15.

### 4. `mesh-receiver` — 2 sites

- `holdspeak/commands/mesh_serve.py:132` — `build_meeting_intel_for_profile`
- `holdspeak/commands/mesh_serve.py:164` — `run_prompt`

The receiver accepts a hand-built job envelope. Nonempty warrant-shaped fields
do not authenticate the sender or prove a locally admitted child. The sole
remaining executable `LEGACY_UNCONTEXTUAL` marker is mechanically pinned to
`MeshServeWorker._engine_for_run`; it is not an adapter exception. Owned by
HS-131-16.

### 5. `plugin-default-provider` — 30 sites

Each plugin's `_cached_provider` family constructs the configured engine and
calls `_chat_completion_text` directly rather than using the host-injected
admitted dispatch handle. Owned by HS-131-14.

- `holdspeak/plugins/builtin/action_owner_enforcer.py:158` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/action_owner_enforcer.py:159` — `_chat_completion_text`
- `holdspeak/plugins/builtin/adr_drafter.py:165` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/adr_drafter.py:166` — `_chat_completion_text`
- `holdspeak/plugins/builtin/customer_signal_extractor.py:157` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/customer_signal_extractor.py:158` — `_chat_completion_text`
- `holdspeak/plugins/builtin/decision_announcement_drafter.py:123` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/decision_announcement_drafter.py:124` — `_chat_completion_text`
- `holdspeak/plugins/builtin/decision_capture.py:198` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/decision_capture.py:199` — `_chat_completion_text`
- `holdspeak/plugins/builtin/dependency_mapper.py:124` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/dependency_mapper.py:125` — `_chat_completion_text`
- `holdspeak/plugins/builtin/incident_timeline.py:125` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/incident_timeline.py:126` — `_chat_completion_text`
- `holdspeak/plugins/builtin/mermaid_architecture.py:213` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/mermaid_architecture.py:214` — `_chat_completion_text`
- `holdspeak/plugins/builtin/milestone_planner.py:150` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/milestone_planner.py:151` — `_chat_completion_text`
- `holdspeak/plugins/builtin/requirements_extractor.py:157` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/requirements_extractor.py:158` — `_chat_completion_text`
- `holdspeak/plugins/builtin/risk_heatmap.py:171` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/risk_heatmap.py:172` — `_chat_completion_text`
- `holdspeak/plugins/builtin/runbook_delta.py:149` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/runbook_delta.py:150` — `_chat_completion_text`
- `holdspeak/plugins/builtin/scope_guard.py:152` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/scope_guard.py:153` — `_chat_completion_text`
- `holdspeak/plugins/builtin/stakeholder_update_drafter.py:126` — `build_configured_meeting_intel`
- `holdspeak/plugins/builtin/stakeholder_update_drafter.py:127` — `_chat_completion_text`
- `holdspeak/plugins/segment_probe.py:158` — `build_configured_meeting_intel`
- `holdspeak/plugins/segment_probe.py:160` — `_chat_completion_text`

### 6. `legacy-uncontextual-factory` — 2 sites

- `holdspeak/intel/providers.py:241` — `MeshRelayIntel`
- `holdspeak/intel/providers.py:253` — `MeetingIntel`

`build_configured_meeting_intel()` takes no context and constructs either a
mesh or local/cloud engine, so its constructor body is a finding rather than an
allowlisted adapter. The admitted path reaches it only through the validating
`configured_meeting_intel(*, context)` wrapper. HS-131-14 owns deletion or
privatization after the last plugin caller migrates.

### 7. `legacy-live-meeting-engine` — 1 site

- `holdspeak/meeting_session/session.py:548` — `MeetingIntel`

`MeetingSession.start` constructs a current-config engine alongside the frozen
admitted plan. That parallel object is both a silent-retargeting risk and the
engine used by the bookmark finding below. Owned by HS-131-17.

### 8. `bookmark-auto-label` — 1 site

- `holdspeak/meeting_session/bookmarks.py:45` — `generate_bookmark_label`

`add_bookmark(auto_label=True)` starts a background thread that calls the engine
directly. The admitted `_admitted_bookmark_label` seam already exists; this
caller bypasses it and leaves no child receipt. Owned by HS-131-17.

## HS-131-13 disposition

The first amendment is complete in the current tree:

- **Cadence admitted:** one authenticated `cadence.next-action-draft` parent,
  one `inference.invoke` child per physical attempt, exact frozen local model
  construction, staged publication, and durable cancellation fencing.
- **Decisions duplicate deleted:** the route no longer holds an engine,
  `run_prompt` callable, or `model_generator` injection seam.
- **Dormant Delivery helper deleted:** the shipped admitted Delivery review
  service remains the sole path.
- **Legacy target factory deleted:** `build_intel_for_target` has no symbol,
  shim, caller, or marker use. The separate mesh receiver marker remains
  visibly pinned to HS-131-16.

## Owner ruling

**RULING RECEIVED 2026-08-12:** charter all five amendment stories, with design
beats for the delete-vs-admit choices in Speech, Mesh, and Meeting. The wave is
HS-131-13 through HS-131-17. Until the remaining four land, HS-131-10 remains
`blocked`; HS-131-11 and HS-131-12 remain held; none of these families may enter
`ADAPTER_ALLOWLIST`.
