# Phase 94 Delivery Runtime contract

**Status:** draft, normative target; not a claim about current implementation
**Contract version:** `delivery-runtime/v1-draft`
**Depends on:** Phase 93's shared Desk objects, projections, receipts, and
operation-policy decision
**Counterpart:** proposed Delivery Workbench WLA-18

## 1. Purpose

This contract defines the smallest shared platform that lets one HoldSpeak hub:

- observe delivery sources and worktrees on its own machine and paired nodes;
- join active Coder sessions to the exact Story they are working on;
- browse the evidence that proves Story and Phase completion;
- watch and steer the intended terminal from Web or native clients;
- create and end story-bound remote agent work;
- retain one honest history of attention, authority, commands, and outcomes.

Delivery Workbench remains authoritative for roadmap structure, story state,
evidence pairing, rail events, mutations, and the commit gate. HoldSpeak remains
authoritative for node pairing, live Work attempts, operation policy,
presentation, client access, and aggregate receipts. The machine that touches a
terminal remains authoritative for terminal identity and the execution audit.

## 2. Non-negotiable invariants

1. **No private Markdown parser in HoldSpeak.** Delivery state and evidence
   membership come from a versioned `dw` command.
2. **One Desk object model.** Project, Story, Coder session, Evidence, Receipt,
   Attention, node/device, and authority reuse Phase 92/93 primitives and
   projections.
3. **One policy decision.** Web, Swift, hub, and nodes do not carry independent
   Secure/Normal/YOLO matrices.
4. **One execution chokepoint per effect.** Terminal text, terminal keys, pane
   lifecycle, rail mutation, and agent launch each have one node-side executor.
5. **Immutable target identity.** A command names node, target, and target
   generation together. Changing machine never reinterprets a pane key.
6. **No blind terminal retry.** If delivery might have occurred, the outcome is
   `unknown` until queried by command ID. Client retry creates no second effect.
7. **Node owns terminal truth.** Pane verification and the execution record are
   made where tmux runs. The hub mirrors, it does not fabricate.
8. **Hub owns client authority.** The hub authenticates the person/device,
   evaluates operation policy, and records the requested effect.
9. **Watching is distinct from acting.** Read access never creates a grant,
   command, mutation, or terminal input.
10. **Evidence is manifest-bound.** A client cannot ask a node for an arbitrary
    path. Every byte belongs to a Delivery Workbench evidence manifest.
11. **Freshness is data.** Live, stale, offline, incompatible, unauthorized, and
    last-known-good are separate states.
12. **Snapshots are coherent and events replay.** Clients receive a revision and
    cursor; reconnect does not depend on having witnessed an ephemeral frame.
13. **Raw paths and secrets do not cross to clients.** Labels and opaque IDs do.
14. **Local is a node, not a special product.** The embedded local adapter
    implements the same provider/executor interfaces as a remote node.
15. **The Delivery Workbench gate remains final.** No HoldSpeak mode, grant, or
    approval can make an invalid rail transition succeed.

## 3. Identity model

All wire IDs are opaque strings. Clients compare them for equality and never
parse them.

| ID | Stability and scope |
|---|---|
| `node_id` | stable across node-process restarts; changes on re-pair/reset |
| `source_id` | stable identity of one configured clone/repository on a node |
| `worktree_id` | stable identity of one git worktree on a node |
| `project_ref` | `source_id + Delivery Workbench project slug` |
| `story_ref` | `project_ref + story ID` |
| `attempt_id` | one bounded undertaking of one primary Story |
| `session_id` | globally unique compound identity; includes node ownership |
| `target_id` | node-issued opaque terminal handle |
| `target_generation` | changes if the pane/server identity can have been recycled |
| `bundle_id` | evidence manifest anchored to source revision/content hash |
| `asset_id` | manifest-local opaque asset handle |
| `event_id` | globally unique delivery event ID |
| `command_id` | client/hub-generated UUID for one consequential command |
| `receipt_id` | durable outcome identity |

Display fields such as hostname, project title, worktree label, branch, agent,
pane title, and Story title are not identity.

### 3.1 Source identity

A node derives a repository fingerprint from credential-free canonical git
metadata and persists an opaque local source ID. A remote URL must be normalized
with user info and tokens removed before hashing or logging.

A `source_id` describes a clone. Two clones of the same upstream repository on
different nodes may share an optional `repository_fingerprint` but retain
different source IDs.

### 3.2 Worktree identity

The node resolves git directories with `git rev-parse --git-dir` and
`--git-common-dir`. It never assumes `.git` is a directory.

The descriptor includes branch, HEAD, dirty state, and Delivery Workbench
projects. It does not expose the filesystem root to Web or native.

### 3.3 Terminal identity

`pane:%N` remains a compatibility key only. A discovered terminal target is:

```json
{
  "target_id": "term_opaque",
  "target_generation": "gen_opaque",
  "node_id": "node_opaque",
  "kind": "tmux_pane",
  "label": "codex · HS-94-05",
  "session_label": "hs94-evidence",
  "worktree_id": "wt_opaque",
  "read_capability": "terminal.snapshot",
  "write_capabilities": ["terminal.text", "terminal.keys", "terminal.kill"]
}
```

The node maps this handle to its local pane and re-verifies generation before
every input. Clients never combine a node selector with a pane ID themselves.

## 4. Core records

### 4.1 Delivery Source

```json
{
  "source_id": "src_opaque",
  "node_id": "node_opaque",
  "label": "HoldSpeak",
  "repository_fingerprint": "sha256:...",
  "status": "live",
  "observed_at": "2026-07-11T16:00:00Z",
  "capabilities": {
    "dw_feed_schema": 1,
    "dw_events_schema": 2,
    "dw_evidence_schema": 1,
    "statuses": ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"],
    "verbs": ["story.status", "story.create"]
  },
  "worktree_ids": ["wt_opaque"]
}
```

Status is one of `live`, `stale`, `offline`, `incompatible`,
`unauthorized`, or `unavailable`. A last-known snapshot can remain attached to
any non-live state with its own `observed_at`.

### 4.2 Work attempt

```json
{
  "attempt_id": "attempt_opaque",
  "story_ref": {
    "source_id": "src_opaque",
    "project": "holdspeak",
    "story_id": "HS-94-05"
  },
  "node_id": "node_opaque",
  "worktree_id": "wt_opaque",
  "session_ids": ["session_opaque"],
  "primary_target_id": "term_opaque",
  "association": {
    "kind": "launch",
    "actor": "desk-owner",
    "confidence": "exact"
  },
  "state": "working",
  "started_at": "2026-07-11T16:00:00Z",
  "updated_at": "2026-07-11T16:02:00Z",
  "ended_at": null
}
```

Association kinds:

- `launch` — the Desk launched the agent from a Story;
- `rider_claim` — an agent rider explicitly claimed a Story;
- `manual` — a person attached an existing session;
- `contract` — one current contract/branch receipt identifies the Story;
- `heuristic` — legacy repo-wide correlation; never displayed as exact.

States: `starting`, `working`, `waiting`, `idle`, `ended`,
`abandoned`, `unknown`.

One attempt has one primary Story. Secondary refs may ride grounding or a
bundle, but cannot silently make a session look active on several stories.

### 4.3 Agent session

Presence list responses are minimal:

```json
{
  "session_id": "session_opaque",
  "node_id": "node_opaque",
  "attempt_id": "attempt_opaque",
  "agent": "codex",
  "model": "gpt-5",
  "state": "waiting",
  "awaiting_response": true,
  "question_preview": "Should I keep the compatibility facade?",
  "target_id": "term_opaque",
  "updated_at": "2026-07-11T16:02:00Z"
}
```

Transcript paths, raw cwd, full prompts, and full last-assistant output are not
part of presence. Explicit detail routes may return bounded content under the
same hub authorization used for terminal viewing.

### 4.4 Delivery snapshot

```json
{
  "delivery_schema": 1,
  "revision": "snapshot_opaque",
  "cursor": "event_cursor_opaque",
  "generated_at": "2026-07-11T16:02:01Z",
  "sources": [],
  "worktrees": [],
  "projects": [],
  "attempts": [],
  "sessions": [],
  "receipts": [],
  "attention": []
}
```

All collections in one response are consistent with `revision`. Slow providers
may contribute a last-known result whose source status and timestamp make the
age explicit.

## 5. Delivery Workbench provider contract

The node invokes the repository's vendored `dw` CLI. A global CLI is a fallback
only when the source advertises no vendored executable.

Required commands after the counterpart phase:

| Command | Contract |
|---|---|
| `dw capabilities --json` | versions, accepted statuses/verbs, roadmap root, optional features |
| `dw state --json` | roadmap feed; existing schema remains supported |
| `dw events --json --after <cursor>` | versioned, cursor-based rail events |
| `dw evidence manifest <project> <story> --json` | dossier membership and metadata |
| `dw evidence asset <bundle> <asset>` | bounded manifest member bytes or a resolved path for the node transport |
| `dw context <project> --compact` | compatibility/detail surface, not the Phase 94 evidence contract |

### 5.1 Capabilities

Schema compatibility is decided before reading a source. Unsupported required
schemas produce `incompatible` with found/required versions. Optional features
degrade individually.

Accepted status and mutation vocabularies come from capabilities. HoldSpeak
does not hard-code a second list.

### 5.2 Rail events

Event envelope:

```json
{
  "events_schema": 2,
  "source_cursor": "cursor_opaque",
  "events": [{
    "event_id": "event_opaque",
    "occurred_at": "2026-07-11T16:02:00Z",
    "kind": "story.status",
    "project": "holdspeak",
    "story_id": "HS-94-05",
    "worktree_hint": "opaque-or-null",
    "detail": {"from": "in-progress", "to": "done"},
    "tree": "git-tree"
  }]
}
```

The current privacy allow-list remains binding: no prompt, transcript, diff, or
arbitrary path can enter a rail event.

Delivery Workbench defines whether events live in the per-worktree git dir or
common git dir. Whichever is selected, the event includes enough opaque
worktree/source context to avoid merging parallel work into a false single
timeline.

### 5.3 Evidence manifest

```json
{
  "evidence_schema": 1,
  "bundle_id": "bundle_opaque",
  "source_revision": {
    "kind": "worktree",
    "head_sha": "abc123",
    "content_hash": "sha256:...",
    "committed": false
  },
  "project": "holdspeak",
  "phase": 94,
  "story_id": "HS-94-05",
  "status": "done",
  "summary": {
    "passing_captures": 2,
    "failing_captures": 1,
    "assets": 4
  },
  "members": [{
    "asset_id": "asset_opaque",
    "role": "evidence_markdown",
    "label": "Evidence",
    "media_type": "text/markdown",
    "bytes": 4200,
    "sha256": "sha256:...",
    "inline": true
  }],
  "captured_runs": [{
    "timestamp": "2026-07-11T16:01:00Z",
    "command": "pytest ...",
    "exit_code": 0,
    "index_tree": "tree",
    "output_asset_id": "asset_output"
  }],
  "trace": {
    "story_asset_id": "asset_story",
    "phase_status_asset_id": "asset_phase",
    "final_summary_asset_id": "asset_summary"
  }
}
```

The manifest is the sole path authority. Asset IDs are resolved only while the
source still matches the bundle's revision/hash; otherwise the node returns
`bundle_changed` and the hub requests a new manifest.

## 6. Node link

### 6.1 Topology

The node initiates an authenticated WebSocket to the hub:

```text
holdspeak node serve --hub https://hub.tailnet.ts.net --name studio-mac
```

The secret is supplied from protected config or an environment reference, never
printed in argv, logs, status, or client payloads.

The browser token and node token are distinct. A node token is scoped to one
node identity and capabilities, can be rotated/revoked, and cannot authenticate
as the human Desk owner.

### 6.2 Hello and capabilities

```json
{
  "node_protocol": 1,
  "type": "hello",
  "node_id": "node_opaque",
  "name": "studio-mac",
  "instance_id": "process_uuid",
  "versions": {
    "holdspeak": "0.x",
    "operation_policy": "operation-policy/v1"
  },
  "capabilities": [
    "delivery.sources",
    "delivery.evidence",
    "agent.sessions",
    "terminal.snapshot",
    "terminal.stream",
    "terminal.text",
    "terminal.keys",
    "terminal.factory",
    "agent.launch"
  ],
  "resume_cursor": "node_cursor_or_null"
}
```

Unknown optional capabilities are ignored. A required protocol or policy
version mismatch prevents commands and renders observation compatibility
honestly.

### 6.3 Heartbeat and liveness

- heartbeat every 5 seconds while connected;
- stale after 15 seconds without a heartbeat;
- offline after 30 seconds or explicit disconnect;
- liveness is per node and per capability;
- clock skew is measured and surfaced; TTL authority uses monotonic clocks
  node-side and hub-side;
- reconnect uses bounded exponential backoff with jitter;
- node event sequence and command receipts resume from cursors.

### 6.4 Node events

Node events carry metadata only unless a named protocol explicitly carries
content:

- source/worktree changed;
- rail cursor advanced;
- session lifecycle/question preview changed;
- terminal target added/changed/removed;
- command receipt changed;
- evidence bundle invalidated;
- node capability/readiness changed.

Terminal output and evidence assets use their own bounded message types.

## 7. Terminal observation contract

### 7.1 Subscribe

```json
{
  "type": "terminal.subscribe",
  "subscription_id": "sub_uuid",
  "target": {
    "target_id": "term_opaque",
    "target_generation": "gen_opaque"
  },
  "resume_sequence": 120
}
```

The node returns either:

- `terminal.snapshot` with current bounded screen/history, sequence, rows,
  columns, ANSI flag, and content hash;
- `terminal.delta` with the next sequence;
- `terminal.not_modified` for snapshot fallback;
- a typed absence: `target_gone`, `generation_mismatch`,
  `stream_unavailable`, or `unauthorized`.

### 7.2 Backpressure

- output has a configured byte/rate ceiling;
- the node retains a bounded replay ring;
- slow clients do not slow the terminal;
- a gap yields `resync_required` and a new snapshot;
- one node capture/stream may fan out to several hub clients;
- terminal output is never written to the hub database by default.

## 8. Command envelope

```json
{
  "command_schema": 1,
  "command_id": "uuid",
  "issued_at": "2026-07-11T16:03:00Z",
  "expires_at": "2026-07-11T16:03:30Z",
  "target": {
    "node_id": "node_opaque",
    "target_id": "term_opaque",
    "target_generation": "gen_opaque"
  },
  "operation": {
    "family": "coder_steering",
    "verb": "terminal.text"
  },
  "authority": {
    "actor": "desk-owner",
    "control_posture": "neutral",
    "decision": "allowed_by_active_grant",
    "policy_version": "operation-policy/v1",
    "grant_id": "grant_opaque"
  },
  "payload": {
    "text": "Continue with the compatibility facade.",
    "submit": true
  },
  "payload_sha256": "sha256:...",
  "expected_sequence": 7
}
```

Node processing order:

1. authenticate hub and validate protocol/policy versions;
2. return the existing receipt if `command_id` is known;
3. reject expired commands;
4. resolve target and verify generation;
5. evaluate node-side hard prerequisites and the shared policy decision;
6. serialize against the target's expected sequence;
7. execute through `coder_steering`/`coder_factory`/launcher;
8. persist the node audit and deduplication result;
9. return and later resume the receipt.

No client controls `actor`, policy version, or authority reason. The hub derives
them from the authenticated session and operation-policy result.

### 8.1 Receipt

```json
{
  "receipt_schema": 1,
  "receipt_id": "receipt_opaque",
  "command_id": "uuid",
  "node_id": "node_opaque",
  "target_id": "term_opaque",
  "target_generation": "gen_opaque",
  "state": "succeeded",
  "outcome": "delivered",
  "applied_sequence": 8,
  "executed_at": "2026-07-11T16:03:01Z",
  "payload_sha256": "sha256:...",
  "payload_head": "Continue with the compatibility facade.",
  "policy_version": "operation-policy/v1",
  "authority_basis": "active_grant",
  "node_audit_id": "audit_opaque",
  "error": null
}
```

The stored head follows the existing privacy ceiling and is suppressible by
configuration. Full steer text is not retained merely because it crossed the
node link.

### 8.2 Unknown outcome

If the connection drops after send and before receipt:

- the hub records `unknown`;
- reconnect queries the same `command_id`;
- the node returns its stored receipt if it executed;
- a node that lost its deduplication ledger across an unclean reset returns
  `indeterminate_after_node_reset`;
- the UI offers inspect/reconcile, never “Retry” as a new blind send.

## 9. Agent launch and factory

Agent launch is a typed operation, not arbitrary shell text:

```json
{
  "verb": "agent.launch",
  "agent_profile_id": "codex-default",
  "source_id": "src_opaque",
  "worktree": {
    "mode": "existing",
    "worktree_id": "wt_opaque"
  },
  "story_ref": {
    "project": "holdspeak",
    "story_id": "HS-94-05"
  },
  "session_label": "hs94-evidence"
}
```

Agent profiles are node-configured argv templates with fixed executables and
allow-listed options. A browser cannot supply an executable or shell fragment.

Launch success creates, in one logical transaction:

- terminal target;
- agent process/session identity once the rider reports it;
- Work attempt;
- launch Receipt.

If the process launches but the rider never registers, the attempt is
`starting` then `unknown`/`failed_to_register` with the terminal still
openable. No process is silently orphaned.

Remote spawn/rename/kill use the same command envelope and target handle.
Destructive actions retain Phase 93 policy behavior and node target checks.

## 10. Hub API

Names are provisional; behavior is binding.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/delivery/snapshot` | coherent cached read model |
| GET | `/api/delivery/events?after=...` | replayable deltas |
| GET | `/api/delivery/sources` | sources/worktrees/capabilities/freshness |
| POST | `/api/delivery/sources` | proposal/config flow, not raw path from an untrusted client |
| GET | `/api/delivery/stories/{ref}/evidence` | evidence manifest |
| GET | `/api/delivery/evidence/{bundle}/{asset}` | authorized/ranged asset |
| GET | `/api/delivery/sessions/{id}` | explicit session detail |
| POST | `/api/delivery/attempts` | attach/launch exact work |
| PATCH | `/api/delivery/attempts/{id}` | end/reassociate with provenance |
| POST | `/api/delivery/terminal/subscriptions` | start hub fan-out |
| POST | `/api/delivery/commands` | all consequential node commands |
| GET | `/api/delivery/commands/{id}` | reconcile outcome |
| GET | `/api/delivery/receipts` | aggregate receipts |

Compatibility `/api/missioncontrol/*` and `/api/coders/*` routes remain until
generated consumer parity shows no callers.

## 11. Collector and read model

The hub collector:

- owns one provider instance per source;
- refreshes with single-flight;
- executes blocking CLI/GitHub work off the event loop;
- bounds subprocess count globally and per node;
- hashes provider payloads and assigns a snapshot revision;
- retains last-known-good with observed time and error;
- consumes source/node event cursors to invalidate;
- performs a slow bounded poll as repair;
- projects attempts, receipts, and attention from durable hub rows;
- emits one replayable delivery cursor to clients.

Clients never cause a fresh `dw`/`gh` process merely by polling. A manual
Refresh requests collector invalidation and returns current state immediately;
completion arrives as an event.

The read model is a projection, not a new source of rail truth. It may be
discarded and rebuilt from providers plus durable attempt/receipt records.

## 12. Security and privacy

### 12.1 Authentication

- HoldSpeak bearer auth remains mandatory off loopback.
- Tailscale identity does not replace the app token.
- Node tokens are per node, scoped, rotatable, revocable, and stored outside
  repository content.
- Browser, native, and node credentials are distinct.
- Tailscale Funnel is refused/documented out of scope for the owner journey.

### 12.2 Authorization

- Project/source visibility follows the authenticated single-owner hub in v1.
- Node capability and configured-root allow-lists constrain discovery and
  factory/launch.
- Operation policy decides human interruption; authentication, target
  generation, destination binding, schema compatibility, and audit never
  weaken in YOLO.
- Rail writes still use the gated connector and Delivery Workbench gate.

### 12.3 Content

- presence is metadata-first;
- prompt/transcript content is not a delivery event;
- terminal output is ephemeral by default;
- evidence bytes are explicit, manifest-bound, capped, and content-typed;
- secrets and credentials are redacted before repo fingerprints, logs, errors,
  events, and receipts;
- node errors returned to clients are classified and bounded, not raw stack
  traces or argv environments.

## 13. Failure semantics

| Failure | Required surface truth |
|---|---|
| source CLI missing | source unavailable; last snapshot retained with age |
| schema unsupported | incompatible with found/required versions |
| worktree removed | worktree gone; attempts become detached, not deleted |
| node heartbeat lost | stale then offline; terminal freezes with last-seen |
| stream gap | resyncing; fresh snapshot, no invented output |
| command refused pre-execution | refused with reason; safe to edit/reissue as a new command |
| response lost after dispatch | outcome unknown; reconcile same command ID |
| pane recycled | generation mismatch; command refused and grant invalidated |
| node restarts | new instance; grants fail closed; targets re-enumerate |
| evidence source changed | bundle changed; preserve manifest metadata, request new bundle |
| asset node offline | asset listed but unavailable with node/last-seen |
| rail gate refuses | approved request receives failed/refused Receipt with gate rule |
| GitHub unavailable | PR/CI receipt unavailable; rail and local commit truth remain |

Empty arrays are used only for a known empty source. They never stand in for an
unavailable or incompatible source.

## 14. Compatibility rules

1. Version every new document independently.
2. Additive unknown fields are ignored.
3. Unknown enum values render `unknown(<raw>)` and do not crash.
4. Unsupported required versions fail only the affected capability.
5. v1 `feed_schema` can populate Projects/Stories while v2 events/evidence are
   absent.
6. v1 direct steering nodes can appear through a compatibility adapter labeled
   `legacy-direct`, without remote discovery claims.
7. The old local project map imports once but is not rewritten destructively.
8. Swift decoders remain tolerant; generated contract fixtures cover Python,
   TypeScript, and Swift.

## 15. Proof obligations

The phase cannot close from mocks alone. The acceptance rig contains:

- hub plus two real node processes;
- at least one node on another physical machine over Tailscale;
- standard and self-hosted Delivery Workbench layouts;
- primary checkout plus linked worktree;
- at least two simultaneous in-progress stories;
- Claude and Codex rider sessions;
- an ANSI/TUI pane with sustained output;
- evidence Markdown, passing and failing captures, PNG, JSON, and text log;
- a real branch/PR/CI receipt when GitHub is available;
- browser at desktop and iPad width;
- physical iPad native app;
- tailnet HTTPS microphone steering.

Faults injected:

- node killed and restarted;
- WebSocket severed before and after command application;
- duplicate command envelope;
- out-of-order sequence;
- pane recycled;
- worktree removed;
- source CLI timeout and schema mismatch;
- evidence asset changed mid-read;
- GitHub offline;
- hub restart with active clients;
- Secure, Normal, and YOLO policy decisions with invariants unchanged.

Close claims include measured latency, subprocess rate independent of client
count, zero duplicate terminal effects, complete local+remote Receipts, and
owner replay of the four north-star journeys.

## 16. Explicit non-goals

- general remote shell access;
- arbitrary command execution;
- replacing git, tmux, Delivery Workbench, or Tailscale;
- public internet access;
- cloud persistence;
- full terminal transcript retention;
- autonomous prioritization or agent scheduling;
- a second workflow engine;
- a second Project/Receipt/Attention/authority model;
- parsing Delivery Workbench Markdown in React, Swift, or HoldSpeak Python.
