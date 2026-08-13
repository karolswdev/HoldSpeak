# HS-131-10 — model-execution inventory and blocking findings

**Generated from:** `tests/unit/test_one_path_census.py` over production
`holdspeak/**/*.py` (tests excluded).

**Census date:** 2026-08-13.
**Disposition:** **BLOCKED; FIVE-STORY AMENDMENT WAVE IN PROGRESS.** These are
findings, not adapter exceptions. The owner chartered HS-131-13 through HS-131-17
to delete or admit every family. HS-131-13 and HS-131-14 are complete in the
current tree; HS-131-10 cannot close until the remaining three amendments land
and the census returns zero findings.

## Current census result — after HS-131-14

| Bucket | Function scopes | Executable sites |
|---|---:|---:|
| `AUTHORIZED_GATEWAY` | 2 | 1 context mint |
| `CLAIM_WITNESS_MINT` | 2 | 2 witness-issuer sites |
| `GATEWAY_FACTORY_BINDING` | 1 | 1 default-factory binding |
| `ADAPTER_ALLOWLIST` | 56 | 70 |
| `ADMITTED_SEAM_CALLERS` | 16 | 25 |
| `NAMED_FINDINGS` | — | 6 |
| Unregistered | — | **0** |
| **Total** | — | **105** |

HS-131-14 reduced the HS-131-13 state from **134 to 105 executable sites**,
**38 to 6 findings**, and **8 to 6 families**. It removed all thirty
`plugin-default-provider` sites, removed both `legacy-uncontextual-factory`
sites, and replaced them with one admitted single-use `PluginDispatch.chat`
seam plus one private provider-construction body dominated by exact context
validation. No builtin plugin or segment-probe scope moved to an allowlist, and
zero unregistered sites remain.

Across the amendment wave so far, the original checkpoint has moved from
**145 to 105 executable sites**, **48 to 6 findings**, and **11 to 6 families**.

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

## Exact remaining blocking ledger — 6 families, 6 pinned sites

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

### 5. `legacy-live-meeting-engine` — 1 site

- `holdspeak/meeting_session/session.py:548` — `MeetingIntel`

`MeetingSession.start` constructs a current-config engine alongside the frozen
admitted plan. That parallel object is both a silent-retargeting risk and the
engine used by the bookmark finding below. Owned by HS-131-17.

### 6. `bookmark-auto-label` — 1 site

- `holdspeak/meeting_session/bookmarks.py:45` — `generate_bookmark_label`

`add_bookmark(auto_label=True)` starts a background thread that calls the engine
directly. The admitted `_admitted_bookmark_label` seam already exists; this
caller bypasses it and leaves no child receipt. Owned by HS-131-17.

## HS-131-14 disposition

The second amendment is complete in the current tree:

- **Providers deleted from plugins:** all fourteen builtins and `segment_probe`
  consume an admitted dispatch handle and no longer construct or cache engines.
- **One physical completion per handle:** one lock elects exactly one claim;
  released, cancelled, stale, cross-child, incompatible, replayed, or
  over-cardinality handles refuse before physical work.
- **Timeout is atomic:** host timeout revokes and classifies the same handle in
  one election; a zero-claim timeout cannot dispatch late, while an in-flight
  attempt is indeterminate and cannot publish.
- **Failures and retries stay honest:** provider errors fail the admitted child;
  compatibility retry receives a distinct `_r2` child, handle, context, and
  receipt, and only the winner materializes.
- **Uncontextual factory retired:** public `build_configured_meeting_intel` is
  gone; private `_configured_engine` is reachable only after exact context and
  revision validation.
- **Pre-admission probe retired:** meeting startup remains lexical until
  HS-131-17 admits MIR routing rather than creating intelligence early.

## Owner ruling

**RULING RECEIVED 2026-08-12:** charter all five amendment stories, with design
beats for the delete-vs-admit choices in Speech, Mesh, and Meeting. The wave is
HS-131-13 through HS-131-17. Until the remaining three land, HS-131-10 remains
`blocked`; HS-131-11 and HS-131-12 remain held; none of these families may enter
`ADAPTER_ALLOWLIST`.
