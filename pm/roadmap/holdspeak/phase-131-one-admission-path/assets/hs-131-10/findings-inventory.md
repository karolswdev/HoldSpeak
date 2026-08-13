# HS-131-10 — model-execution inventory and blocking findings

**Generated from:** `tests/unit/test_one_path_census.py` over production
`holdspeak/**/*.py` (tests excluded).

**Census date:** 2026-08-13.
**Disposition:** **BLOCKED; FIVE-STORY AMENDMENT WAVE IN PROGRESS.** These are
findings, not adapter exceptions. The owner chartered HS-131-13 through HS-131-17
to delete or admit every family. HS-131-13 through HS-131-15 are complete in the
current tree; HS-131-10 cannot close until the remaining two amendments land and
the census returns zero findings.

## Current census result — after HS-131-15

| Bucket | Function scopes | Executable sites |
|---|---:|---:|
| `AUTHORIZED_GATEWAY` | 2 | 1 context mint |
| `CLAIM_WITNESS_MINT` | 2 | 2 witness-issuer sites |
| `GATEWAY_FACTORY_BINDING` | 1 | 1 default-factory binding |
| `ADAPTER_ALLOWLIST` | 56 | 70 |
| `ADMITTED_SEAM_CALLERS` | 18 | 27 |
| `NAMED_FINDINGS` | — | 4 |
| Unregistered | — | **0** |
| **Total** | — | **105** |

HS-131-15 preserved the 105-site total while replacing both speech findings
with admitted seams: browser rehearsal/replay/template-preview and the
authenticated CLI command each open a fresh bounded text-entry session whenever
the frozen configuration selects provider work. Provider-free configurations
remain lexical and parentless. No speech scope moved to an allowlist, and zero
unregistered sites remain.

Across the amendment wave so far, the original checkpoint has moved from
**145 to 105 executable sites**, **48 to 4 findings**, and **11 to 4 families**.

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

## Exact remaining blocking ledger — 4 families, 4 pinned sites

### 1. `dormant-mir` — inventoried branch, 0 executable sites

- `holdspeak/meeting_session/session.py` — the `mir_routing_enabled=True`
  branch is dormant today but would route model work outside the admitted
  meeting-child seam if enabled.

A latent side door is still a side door; either delete it or admit every MIR
attempt under the meeting session. Owned by HS-131-17.

### 2. `mesh-receiver` — 2 sites

- `holdspeak/commands/mesh_serve.py:132` — `build_meeting_intel_for_profile`
- `holdspeak/commands/mesh_serve.py:164` — `run_prompt`

The receiver accepts a hand-built job envelope. Nonempty warrant-shaped fields
do not authenticate the sender or prove a locally admitted child. The sole
remaining executable `LEGACY_UNCONTEXTUAL` marker is mechanically pinned to
`MeshServeWorker._engine_for_run`; it is not an adapter exception. Owned by
HS-131-16.

### 3. `legacy-live-meeting-engine` — 1 site

- `holdspeak/meeting_session/session.py:548` — `MeetingIntel`

`MeetingSession.start` constructs a current-config engine alongside the frozen
admitted plan. That parallel object is both a silent-retargeting risk and the
engine used by the bookmark finding below. Owned by HS-131-17.

### 4. `bookmark-auto-label` — 1 site

- `holdspeak/meeting_session/bookmarks.py:45` — `generate_bookmark_label`

`add_bookmark(auto_label=True)` starts a background thread that calls the engine
directly. The admitted `_admitted_bookmark_label` seam already exists; this
caller bypasses it and leaves no child receipt. Owned by HS-131-17.

## HS-131-15 disposition

The third amendment is complete in the current tree:

- **Admit only when providers exist:** browser rehearsal, replay, template
  preview, and CLI dry-run open a fresh 90-second/12-child `dictation.session`
  only when the frozen configuration selects provider work. Lexical
  configurations mint no parent, child, watcher, or terminal receipt.
- **CLI authority is authenticated:** `$HOLDSPEAK_TOKEN` is derived against the
  hub's configured bearer through the central owner authenticator. Missing or
  invalid credentials refuse before runtime construction.
- **Construction obeys the frozen revision:** provider placement, artifact,
  endpoint, model, secret slot, and egress proof come from the parent-bound plan;
  admitted construction forces warm-on-start off.
- **Fatal controls stay fatal:** liveness, revocation, revision, child-budget,
  and provider failures escape ordinary raw-text degradation without a duplicate
  model attempt.
- **Publication is one durable election:** publication/effect callbacks claim an
  exact SQLite parent slot across processes; cancellation, revocation, expiry,
  new children, and raw parent transitions serialize or defer. A failed release
  retries its exact token live without replaying the callback.
- **Content stays out of the kernel:** parent metadata contains only hashes,
  references, bounds, authority, and claim tokens; no audio, dictated text,
  prompt, completion, token stream, rewritten body, credential, or raw provider
  exception enters an operation, event, or receipt row.

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
