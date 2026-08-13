# HS-131-10 — model-execution inventory and blocking findings

**Generated from:** `tests/unit/test_one_path_census.py` over production
`holdspeak/**/*.py` (tests excluded).

**Census date:** 2026-08-12.
**Disposition:** **BLOCKED; FIVE-STORY AMENDMENT WAVE CHARTERED.** These are
findings, not adapter exceptions. On 2026-08-12 the owner chartered HS-131-13
through HS-131-17 to delete or admit every family. HS-131-10 cannot close until
that work lands and the census returns zero findings.

## Census result

| Bucket | Function scopes | Executable sites |
|---|---:|---:|
| `AUTHORIZED_GATEWAY` | 2 | 1 context mint |
| `CLAIM_WITNESS_MINT` | 2 | 2 witness-issuer sites |
| `GATEWAY_FACTORY_BINDING` | 1 | 1 default-factory binding |
| `ADAPTER_ALLOWLIST` | 55 | 69 |
| `ADMITTED_SEAM_CALLERS` | 15 | 24 |
| `NAMED_FINDINGS` | — | 48 |
| Unregistered | — | **0** |
| **Total** | — | **145** |

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

The census now recognizes existing-client SDK calls and first-class references
such as `client.chat.completions.create`, including literal
`getattr(receiver, "model_verb")` and SDK-chain getters regardless of the
container that holds them, without classifying availability probes or unrelated
repository/store `.create` methods. Physical cardinality is counted at the
cloud SDK, llama.cpp, mesh enqueue, and Whisper backend edges—not at engine
construction. The former MeetingIntel compatibility fallback is now two
admitted children with two terminal receipts for two physical requests, in
both text and streaming paths.

## Exact blocking ledger — 11 families, 48 pinned sites

### 1. `cadence` — 2 sites

- `holdspeak/services/cadence_service.py:22` — `build_configured_meeting_intel`
- `holdspeak/services/cadence_service.py:23` — `run_prompt`

`_cadence_llm()` constructs an engine and completes a prompt with no admitted
operation, immutable revision, or invocation receipt.

### 2. `dormant-mir` — inventoried branch, 0 executable sites

- `holdspeak/meeting_session/session.py` — the `mir_routing_enabled=True`
  branch is dormant today but would route model work outside the admitted
  meeting-child seam if enabled.

A latent side door is still a side door; either delete it or admit every MIR
attempt under the meeting session.

### 3. `dictation-dry-run` — 1 site

- `holdspeak/web/routes/dictation/_helpers.py:541` — `build_pipeline`

The route constructs a model-bearing pipeline with no authenticated speech
session admission.

### 4. `dictation-command` — 1 site

- `holdspeak/commands/dictation.py:79` — `build_pipeline`

The CLI constructs the same model-bearing pipeline without an authenticated
command parent or frozen plan.

### 5. `mesh-receiver` — 2 sites

- `holdspeak/commands/mesh_serve.py:132` — `build_meeting_intel_for_profile`
- `holdspeak/commands/mesh_serve.py:164` — `run_prompt`

The receiver accepts a hand-built job envelope. Nonempty warrant-shaped fields
do not authenticate the sender or prove a locally admitted child.

### 6. `plugin-default-provider` — 30 sites

Each plugin's `_cached_provider` family constructs the configured engine and
calls `_chat_completion_text` directly rather than using the host-injected
admitted dispatch handle.

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

### 7. `decisions-route` — 2 sites

- `holdspeak/web/routes/decisions.py:23` — `build_intel_for_target`
- `holdspeak/web/routes/decisions.py:25` — `run_prompt` (passed as a bound method)

This is a second Decisions seam outside the admitted Decision promotion
service.

### 8. `delivery-legacy-factory` — 1 site

- `holdspeak/services/delivery_service.py:142` — `build_intel_for_target`

The dormant `prepare_pr_review` path constructs an engine with no admitted
Delivery child.

### 9. `legacy-uncontextual-factory` — 7 sites

- `holdspeak/intel/providers.py:241` — `MeshRelayIntel`
- `holdspeak/intel/providers.py:253` — `MeetingIntel`
- `holdspeak/inference_targets.py:755` — `MeetingIntel`
- `holdspeak/inference_targets.py:761` — `local_pinned_meeting_intel`
- `holdspeak/inference_targets.py:765` — `configured_meeting_intel`
- `holdspeak/inference_targets.py:769` — `build_intel_for_revision`
- `holdspeak/inference_targets.py:775` — `configured_meeting_intel`

`build_configured_meeting_intel()` takes no context and constructs either a
mesh or local/cloud engine, so its constructor body is a finding rather than an
allowlisted adapter. The admitted path reaches it only through the validating
`configured_meeting_intel(*, context)` wrapper. `build_intel_for_target` is the
second legacy factory shared by the Decisions and Delivery findings. Neither is
an adapter exception. Their transitional marker is structurally pinned to the
exact finding scopes and must disappear when the last caller migrates.

### 10. `legacy-live-meeting-engine` — 1 newly discovered site

- `holdspeak/meeting_session/session.py:548` — `MeetingIntel`

`MeetingSession.start` constructs a current-config engine alongside the frozen
admitted plan. That parallel object is both a silent-retargeting risk and the
engine used by the bookmark finding below.

### 11. `bookmark-auto-label` — 1 newly discovered site

- `holdspeak/meeting_session/bookmarks.py:45` — `generate_bookmark_label`

`add_bookmark(auto_label=True)` starts a background thread that calls the
engine directly. The admitted `_admitted_bookmark_label` seam already exists;
this caller bypasses it and leaves no child receipt.

## Recommended charter-amendment wave

The eleven families form five coherent owner stories. This is the smallest
wave that keeps migrations atomic without hiding any family:

1. **Residual service admission** — migrate Cadence, the second Decisions
   route, and dormant Delivery review under authenticated domain parents and
   frozen revisions; then delete `build_intel_for_target` and its transitional
   marker.
2. **Plugin provider admission** — migrate the fourteen builtin providers plus
   `segment_probe` together onto the host-injected admitted engine/dispatch
   handle; then delete or privatize the uncontextual
   `build_configured_meeting_intel()` construction body so only the validating
   wrapper can reach it.
3. **Speech side-door admission** — give dictation dry-run and the CLI command
   explicit authenticated session parents and frozen plans, or make the chosen
   path lexical-only with no provider construction.
4. **Mesh receiver authority** — cryptographically verify the incoming warrant
   and admitted envelope, or run a node-side `InferenceRunner` that admits and
   receipts the physical work locally.
5. **Meeting residual admission** — delete or admit dormant MIR; replace the
   config-time live `MeetingIntel` with the frozen admitted plan plus a
   liveness flag; route bookmark auto-label through
   `_admitted_bookmark_label`.

## Owner ruling

**RULING RECEIVED 2026-08-12:** charter all five amendment stories, with design
beats for the delete-vs-admit choices in Speech, Mesh, and Meeting. The wave is
now HS-131-13 through HS-131-17. Until all five land, HS-131-10 remains
`blocked`; HS-131-11 and HS-131-12 remain held; none of these families may enter
`ADAPTER_ALLOWLIST`.
