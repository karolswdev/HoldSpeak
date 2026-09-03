# Project Rooms — interview-led setup and universal Watches SRS

Document ID: `SRS-PRJ-SETUP-WATCH`
Status: Draft for implementation planning
Version: 0.1
Date: 2026-08-30
Parents: `SRS_SYSTEM.md`, `SRS_DOMAIN_DRIVER.md`

## 1. Product and architecture decision

Creating a Project MUST be an interview that installs an operating system for an outcome, not a CRUD form that opens an empty dashboard.

The primary promise is:

> Tell HoldSpeak what outcome matters and what you want noticed. HoldSpeak finds the capabilities already available, helps install concrete working Watches, proves they observe the intended work, and assigns the Steward to maintain the Project and act when conditions occur.

The interview is a compiler:

```text
OUTCOME + WATCH INTENT + PROVIDER SCOPE + TESTED QUERY
        + CONDITION + CADENCE + YOLO ACTIONS
        = LIVING PROJECT
```

This sharpens the roles of the first-class citizens:

- **Interview** constructs the Project's inspectable operating contract.
- **Watch** defines what should be observed and what normalized conditions matter.
- **Delta** turns Watch observations and native evidence into semantic change.
- **Steward** performs configured Project actions and deeper interpretation.
- **Project Room** shows truth, Watches, activity, repair, and control.
- **Update Factory** communicates what was learned and accomplished.
- **MCP** drives the same setup/Watch contracts and may back a provider adapter; it is not the authority.

A Blank Project is an escape hatch. It is not the flagship creation experience.

## 2. Existing-system ruling

This design MUST graduate the current automation substrate:

- `connector_watches` already stores typed Watch identity, provider query, latest snapshot (baseline), error, and enabled state; the cadence interval is embedded in query_json (refresh_interval_minutes), and freshness is inferred from last_success_at;
- `ReactionService` already previews, baselines, refreshes due Watches, emits semantic service events, isolates source failures, and routes events to matching Reactions;
- `GitHubWatchSource` already performs a live `gh pr list` snapshot;
- semantic diffs already cover GitHub PR review/check/head/state/merge changes and Jira assignment/status/priority/due/resolution changes;
- `connector_reactions` already maps Watch events to Workbench items/runs;
- Web and MCP already expose basic Watch/Reaction operations.

The implementation MUST NOT create a competing Project-only Watch root. `connector_watches` becomes the physical persistence seam for `WatchSpec@1`. A transport-neutral `WatchService` becomes the universal application façade; `ReactionService` delegates or is incrementally absorbed behind compatibility tests.

The Project Steward remains the durable Project action conductor. Existing Workbench Reactions remain a valid action target and compatibility path, not the universal Steward runtime.

## 3. Universal language and boundaries

### 3.1 Watch versus provider

A Watch is HoldSpeak-owned durable intent:

```text
what to observe
where to observe it
when to evaluate
which normalized condition matters
what HoldSpeak should do
which Project it serves
```

A provider adapter supplies capabilities:

```text
connect or identify an owner action needed
report connection state
discover capabilities and scopes
enumerate provider resources
validate and test a proposed Watch
read normalized snapshots/events
optionally execute a provider effect
```

A Watch MUST NOT store tokens, cookies, CLI environment, provider executable commands, arbitrary model-authored code, or credentials. It stores an opaque connection ref, stable provider resource identities, a versioned specification, and non-secret discovery display metadata.

### 3.2 Provider transport

Provider transport is one of:

```text
mcp_app | connector_pack | local_domain
```

The provider transport is replaceable beneath `WatchProviderAdapter`. Project, Watch, Delta, and Steward services MUST NOT call GitHub, Jira, an MCP tool, or a CLI directly.

An external GitHub/Jira MCP app is therefore a preferred future connection/discovery backend, not a V0 architectural dependency. HoldSpeak is currently an MCP server, not a general external MCP client. The fastest truthful V0 GitHub path is the existing local `gh` connector plus missing auth/repository discovery capabilities. If an MCP/app provider becomes available, it MUST implement the same adapter and produce equivalent normalized observations.

HoldSpeak's own MCP surface MUST expose setup and Watch operations so external drivers can install and operate the same contracts.

### 3.3 Watch, Delta, and action separation

- A Watch observes provider/native state and evaluates a closed condition.
- A match emits/persists a typed evaluation; it does not silently mutate Project truth.
- A Watch rule invokes one or more registered actions.
- Project-owned actions call `ProjectService`/`ProjectStewardService`.
- Door, Workbench, Cadence, or provider effects call their canonical application services/adapters.
- Delta consumes normalized observations/evaluations and preserves provenance.

## 4. Interview experience

### 4.1 Universal questions

No more than two questions may precede concrete Watch recommendations:

1. **What outcome are you trying to create or protect?**
2. **What would you want HoldSpeak to notice without being asked?**

The owner may type, dictate, choose suggestions, or combine them. The original answer MUST be retained separately from the editable normalized outcome/intent.

Suggested signals include:

- work becomes blocked;
- a commitment becomes overdue or loses ownership;
- a decision changes or needs review;
- delivery moves, stalls, or reaches completion;
- a critical check fails;
- scope, priority, or due date changes;
- evidence goes quiet;
- a success condition is reached.

After the first Watch is specified, setup asks:

3. **When this happens, what should HoldSpeak do?**
4. **How closely should HoldSpeak watch this?**

V0 action choices:

- put it in Project attention;
- draft the next Project update;
- create/update canonical Follow-through;
- run the Project Steward;
- add/run a selected Workbench/Agent collaborator;
- combine implemented actions.

Cadence presets:

- active work — every 15 minutes;
- normal — every 35 minutes;
- daily;
- weekdays;
- custom bounded interval.

The exact next run time is shown before activation.

### 4.2 Structured, not unbounded chat

At wide widths the setup composes a guided question plane with a live Project brief:

```text
┌ Guided question plane ─────────┬ Live Project brief ────────┐
│ One consequential question     │ Outcome                     │
│ Suggestions / provider results │ Watches and exact scope     │
│ Voice or keyboard answer       │ Cadence / YOLO / test state │
└────────────────────────────────┴─────────────────────────────┘
```

Previous answers collapse into editable rows. The durable structured proposal is always visible. Conversational language assists compilation; it is never the only stored action contract.

### 4.3 Interview requirements

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| INT-001 | MUST/V0 | Primary Create Project MUST open a durable setup session, not an empty active Project or generic metadata form. | T,D |
| INT-002 | MUST/V0 | Outcome and at least one watch intent MUST precede external provider recommendations; Blank remains explicitly available. | T,D |
| INT-003 | MUST/V0 | Setup MUST NOT present more than two universal questions before concrete recommendation cards appear. | T,U |
| INT-004 | MUST/V0 | Answers MUST support text and voice, preserve the original, and expose the normalized outcome/intent for direct editing. | T,D |
| INT-005 | MUST/V0 | A setup session MUST autosave, survive reload/window close, and resume at its prior stage. | T,D |
| INT-006 | MUST/V0 | Abandoning setup MUST NOT leave a hollow active Project. | T |
| INT-007 | MUST/V0 | Recommendations MUST be conditioned on outcome, intent, existing Project/native evidence, and a live provider inventory. | T,I |
| INT-008 | MUST/V0 | Each recommendation MUST name source, discovered or missing scope, subject, conditions, action, cadence, readiness, and rationale. | T,D |
| INT-009 | MUST/V0 | Selecting a recommendation MUST enter one bounded provider clarification flow without losing interview state. | T,D |
| INT-010 | MUST/V0 | The interview MUST fall back to deterministic selections/forms when inference is unavailable. | T,D |
| INT-011 | MUST/V0 | The live brief MUST distinguish mentioned, proposed, tested, disabled, and active Watches. | T,D |
| INT-012 | MUST/V0 | Setup MUST remain editable later from `Project Info → Watches` using the same machinery. | T,D |

## 5. Setup lifecycle and activation

Setup session state:

```text
active(outcome → signals → providers → scopes → proposals → test → review)
  → completed | abandoned | expired
```

Watch proposal/test state:

```text
proposed → selected → testing → passed | partial | failed
passed → ready_to_activate → active
```

Activation flow:

```text
DISCOVER → CLARIFY → COMPILE → TEST → PREVIEW → BASELINE → ACTIVATE
```

At least one Watch MUST pass a real, bounded, non-mutating read before the flagship activation flow completes. A Blank/local-manual Project MAY explicitly activate without an external Watch.

Test shows current entities and present-state conditions; it performs no configured action and persists no active baseline. Activation establishes the baseline without emitting historical transitions as new events. Present-state concerns may be materialized by the explicit `Run initial assessment` command.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| ACT-001 | MUST/V0 | Final review MUST show outcome, exact Watch specs, scopes, cadence, actions, YOLO, test results, and first-run behavior. | T,D |
| ACT-002 | MUST/V0 | A zero-match test MAY pass when the provider read succeeds and MUST say `Test passed · 0 current matches`. | T,D |
| ACT-003 | MUST/V0 | Failed optional Watches MAY be repaired, removed, or saved disabled; they MUST NOT appear active/tested. | T,D |
| ACT-004 | MUST/V0 | Finalization MUST atomically create/update Project, selected Watch specs, source bindings, rules, Steward policy, setup revision, baseline, and next evaluation—or retain a recoverable setup draft. | T |
| ACT-005 | MUST/V0 | Baseline establishment MUST NOT emit all existing entities as new transition events. | T |
| ACT-006 | MUST/V0 | After activation, Now MUST show what is watched, current matching state, next evaluation, configured response, and `Run initial assessment`. | T,D |
| ACT-007 | MUST/V0 | Initial assessment MUST evaluate active Watches and may execute configured YOLO actions while showing progress and durable results. | T,D |
| ACT-008 | MUST/V0 | Changing provider scope, material query, conditions, actions, or trigger MUST create a new revision and require retest before replacing the active revision/baseline. | T,D |
| ACT-009 | MUST/V0 | Removing/retiring a Watch MUST stop future evaluation while retaining observations, evaluations, effects, and resulting Project history. | T |

## 6. Provider inventory and discovery

Logical inventory:

```text
ProviderCapability
  provider_id
  transport: mcp_app | connector_pack | local_domain
  display_name
  connection_state
  discovery_state
  recovery_action?
  discover/read/subscribe/effect capabilities
  subject schemas and query dimensions
  normalized event kinds
  discovered scope cursor
  capability revision and checked time
```

Connection states:

```text
disconnected | connecting | owner_action_required | connected
degraded | expired | revoked | unavailable
```

Discovery states:

```text
unknown | discovering | ready | partial | failed | stale
```

Web-friendly readiness may project these as `checking`, `ready`, `connection_required`, `capability_missing`, `partial`, `unavailable`, or `failed`.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PROV-001 | MUST/V0 | Each provider adapter MUST publish a versioned capability manifest distinguishing discover, read, subscribe, and effect capabilities. | T,I |
| PROV-002 | MUST/V0 | Connection state, capability discovery state, Watch test state, and action capability MUST remain separate. | T,D |
| PROV-003 | MUST/V0 | The server-side provider adapter MUST report readiness; Web/model inference MUST NOT guess from buttons, installed binaries, or prose. | T |
| PROV-004 | MUST/V0 | Setup MUST persist only an opaque provider connection ref and non-secret capability/resource metadata. | T,I |
| PROV-005 | MUST/V0 | Authentication/recovery MUST use the provider-owned interaction and resume the exact setup step afterward. | T,D |
| PROV-006 | MUST/V0 | Discovery MUST be searchable, bounded/paginated, stable-ID based, and tolerant of partial pages/errors. | T,D |
| PROV-007 | MUST/V0 | Read capability MUST never be displayed as write/action capability. Partial capability MUST remain usable. | T,D |
| PROV-008 | MUST/V0 | Arbitrary MCP/app tools MUST NOT become installable Watches without an adapter that defines identity, normalization, query/test, cursor/baseline, and conditions. | T,I |
| PROV-009 | MUST/V0 | Provider failures MUST use typed codes including unavailable, authentication_required, capability_missing, scope_denied, rate_limited, and query_invalid. | T |
| PROV-010 | MUST/V0 | Capability loss MUST invalidate affected tests and move active Watches to attention without deleting intent or last-known-good baseline. | T,D |
| PROV-011 | MUST/V0 | Suggestions MUST never invent a repository, Jira Project, site, or other provider scope identity. | T,I |
| PROV-012 | SHOULD/V1 | One provider connection SHOULD serve multiple Projects and Watches. | T,I |

## 7. `WatchSpec@1`

Illustrative normative shape:

```json
{
  "schema": "WatchSpec@1",
  "id": "watch_...",
  "project_id": "project_...",
  "name": "Failing checks on transformation repositories",
  "intent": "Surface delivery risk before the weekly review",
  "provider": {
    "id": "github",
    "transport": "connector_pack",
    "connection_ref": "provider-connection:...",
    "capability_revision": "sha256:..."
  },
  "subject": {
    "kind": "pull_request",
    "scope": {"repositories": ["everdriven/platform"]},
    "query": {"state": "open", "base": "main"}
  },
  "trigger": {
    "kind": "poll",
    "schedule": {"every_minutes": 35, "timezone": "America/Denver"}
  },
  "rules": [{
    "condition": {
      "schema": "WatchCondition@1",
      "operator": "any",
      "clauses": [
        {"field": "checks", "comparison": "changed_to", "value": "failure"}
      ]
    },
    "actions": [
      {"schema": "WatchAction@1", "kind": "project.observe"},
      {"schema": "WatchAction@1", "kind": "project.steward.run_once"}
    ]
  }],
  "mode": "yolo",
  "state": "active",
  "revision": 3
}
```

### 7.1 Trigger contract

Closed trigger kinds:

- `manual` — explicit Web/Thread/MCP/Steward evaluation;
- `poll` — V0 bounded `every_minutes` scheduler;
- `event` — normalized provider subscription delivery;
- `cadence` — time-relative/negative-space evaluation such as “nothing moved.”

The Watch `cadence` trigger is not the existing Cadence domain. It is a Watch evaluation schedule. A Watch action MAY create/update a canonical Cadence loop.

### 7.2 Condition contract

`WatchCondition@1` is a closed declarative expression tree. It MUST NOT contain Python, shell, JavaScript, SQL, or a model prompt.

Logical operators:

```text
all | any | not
```

Comparisons:

```text
equals | not_equals | in | not_in | exists | missing
changed | changed_from | changed_to
greater_than | less_than | older_than | newer_than | contains
```

Fields address the normalized subject schema, never raw provider payload presentation. Evaluation returns `matched | not_matched | indeterminate`. A missing required field produces `indeterminate`.

### 7.3 Action contract

Initial closed actions:

```text
project.observe
project.propose
project.steward.run_once
project.update.draft
door.add_item
workbench.add_item
workbench.run
cadence.upsert_loop
```

Later provider effects include explicit adapter capabilities such as `github.pull_request.comment` or `jira.issue.transition`.

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| WAT-001 | MUST/V0 | Plain-language intent MUST be preserved separately from compiled provider scope/query, conditions, triggers, and actions. | T,I |
| WAT-002 | MUST/V0 | The selected provider adapter MUST validate and test the compiled specification against current provider state. | T |
| WAT-003 | MUST/V0 | Watch revision, provider capability revision, source revision, normalized subject refs, evaluation, and effects MUST remain traceable. | T,I |
| WAT-004 | MUST/V0 | Actions may render arguments only from allowlisted normalized fields. | T |
| WAT-005 | MUST/V0 | Each effect MUST use a deterministic idempotency key and a durable receipt/result. | T |
| WAT-006 | MUST/V0 | Repeated identical observations MUST NOT repeat effects unless an explicit reminder policy is due. | T |
| WAT-007 | MUST/V0 | Unknown effect outcome MUST become indeterminate and MUST NOT be replayed blindly. | T |
| WAT-008 | MUST/V0 | Watch→Steward→event recursion MUST be causally bounded. | T |
| WAT-009 | MUST/V0 | One entity transition MAY trigger multiple independent actions; one failing action MUST NOT erase successful independent effects. | T |
| WAT-010 | MUST/V0 | Multiple Watch matches at one Project observation watermark MUST deduplicate to at most one requested Steward run. | T |

## 8. Provider clarification flows

### 8.1 GitHub PR V0

Setup MUST:

1. probe the available GitHub provider and actual authenticated readiness;
2. discover or accept an exact `owner/repository` scope;
3. propose precise PR Watches from outcome/intent/current evidence;
4. clarify population, conditions, actions, and cadence;
5. perform a live test and show current-state concerns;
6. baseline and activate selected Watches.

V0 conditions:

- PR opened;
- review requested / review decision changed;
- checks changed, especially to failure/recovery;
- PR head changed;
- PR merged/state changed;
- open PR has no activity for a configured duration.

V0 filters:

- open/all state;
- base branch;
- author/excluded author;
- label/draft inclusion;
- bounded provider search.

Recommended templates:

- `watch.github.review_queue`;
- `watch.github.ci_health`;
- `watch.github.merge_flow`;
- `watch.github.delivery_drift`;
- `watch.github.release_readiness`.

The live test MUST show provider/connection, repository, normalized query, entity count, up to five representative PRs, present matched conditions, supported future transitions, observation time, duration, and typed error/partial state.

The existing `GitHubWatchSource` is the V0 snapshot fallback. It does not presently enumerate repositories or prove authentication separately from binary presence; those provider capabilities are implementation requirements. If enumeration is unavailable, typed `owner/repository` plus a real validation read is an acceptable V0 fallback.

### 8.2 Jira issue parity

Setup MUST eventually:

1. discover connection/site, Projects, issue types, and status categories;
2. select one or more Projects/types;
3. build a constrained population by status, priority, assignee, component, label, sprint, or advanced JQL;
4. select conditions and actions;
5. test current issues, baseline, and schedule.

V0 conditions:

- issue discovered;
- status/assignment/priority/due date changed;
- entered a configured blocked state;
- due soon/overdue;
- resolution appeared;
- no activity for a configured duration.

Recommended templates:

- `watch.jira.blockers`;
- `watch.jira.delivery_flow`;
- `watch.jira.due_risk`;
- `watch.jira.scope_intake`;
- `watch.jira.transformation`.

The V0 Jira transport is the Atlassian CLI (`acli`), the same
relationship `gh` has with GitHub. `acli` is an external prerequisite
(`brew tap atlassian/homebrew-acli && brew install acli`); the owner
authenticates via `acli jira auth login` and HoldSpeak never stores
credentials.

A connection is identified by **(site, email)**, which is acli's own
identity for `auth switch --site --email`. One owner may hold many
connections across many `*.atlassian.net` sites or multiple accounts on
one site. Each combination is one row in `watch_provider_connections`
with `provider_id="jira"` and `external_connection_ref="site|email"`.

acli keeps ONE current account globally, so every HoldSpeak call
follows the **switch-and-verify law**: `auth switch --site S --email E`,
then the command, then `auth status` read-back, all under one
process-wide lock. A read-back naming a different site or email is a
typed error (`degraded`), never a silent wrong read.

Issue types are **enumerated** from `project view --key K --json`
(the `issueTypes` array). Statuses are **observed** from a bounded
`workitem search --fields key,status` population, labeled `observed`;
Jira's three status categories (`new`, `indeterminate`, `done`) are
fixed and labeled `static`.

**The search field cap:** `workitem search --fields` accepts only
issuetype, key, assignee, priority, status, summary, labels, reporter,
creator, description. Fields such as duedate, resolution, and updated
are refused. `workitem view KEY --fields ... --json` accepts all fields.
The JiraWatchSource therefore fetches the population by one JQL search,
then enriches each entity with one bounded `workitem view --fields
duedate,resolution,updated,statuscategorychangedate` call, capped by
the watch limit (N+1 calls per evaluation, N = number of items).

Read verbs only; no Jira write effects ship in this slice (V0-E).

A fixture MUST NOT be used to claim readiness.

Ratified 2026-09-03 by the owner: acli transport; multi-account,
multi-site focus.

### 8.3 HoldSpeak-native Watches

At least one provider-free family MUST ship with the setup flow:

- Meetings associated with the Project;
- linked Decisions and review due;
- Door/follow-through commitments, ownership, overdue/stale state;
- linked Notes/Artifacts/Threads and evidence silence/conflict;
- update/review due.

Native tests show real Desk objects with the existing citation/source-opening behavior. This preserves a useful setup path if external providers are absent.

## 9. Persistence amendments

### 9.1 Setup

`project_setup_sessions`:

```text
id, state, stage, draft_schema, draft_json, project_id nullable,
created_at, updated_at, completed_at, expires_at
```

`project_setup_answers` (append-only):

```text
id, session_id, question_id, answer_schema, answer_json,
revision, created_at
UNIQUE(session_id, question_id, revision)
```

`watch_setup_proposals`:

```text
id, session_id, provider_id, connection_id nullable,
spec_schema, spec_json, rationale_json, state,
test_state, test_result_json, created_at, updated_at
```

### 9.2 Provider connection metadata

`watch_provider_connections`:

```text
id, provider_id, transport, external_connection_ref, state,
capability_manifest_json, capability_revision, discovery_state,
last_checked_at, last_connected_at, last_error_code,
last_error_detail, created_at, updated_at
```

No credential material is permitted.

### 9.3 Graduate `connector_watches`

Keep current columns/IDs. Add:

```text
schema_version, project_id, intent, provider_connection_id,
subject_kind, trigger_kind, trigger_json,
mode, state, revision, baseline_state, test_state,
test_result_json, last_test_at, next_evaluation_at, last_evaluated_at
```

Keep `query_json` as the provider subject scope/query and `snapshot_json` as latest baseline cache. Existing Watches migrate to `WatchSpec@1`, `intent="Legacy automation watch"`, nullable Project, existing poll cadence, and attached Reactions unchanged.

`project_sources` binds a Project to `watch:<watch_id>` and stores Project-specific semantic role/materiality. It MUST NOT copy the Watch query, cadence, baseline, or provider connection.

### 9.4 Rules, evaluations, and effects

`watch_rules`:

```text
id, watch_id, ordinal, condition_schema, condition_json,
action_schema, action_json, enabled, revision, created_at, updated_at
UNIQUE(watch_id, ordinal)
```

`watch_evaluations`:

```text
id, watch_id, watch_revision, provider_capability_revision,
source_revision, trigger_kind, state, matched_rule_ids_json,
observation_ids_json, started_at, completed_at, error_code, error_detail
UNIQUE(watch_id, watch_revision, source_revision)
```

`watch_effects`:

```text
id, evaluation_id, rule_id, action_kind, target_ref,
idempotency_key UNIQUE, arguments_sha256, state,
operation_id, receipt_id, result_ref, verification_state,
error_code, error_detail, created_at, completed_at
```

## 10. Application contracts

Recommended services:

- `ProjectSetupService` — durable interview, suggestions, provider subflows, atomic finalization;
- `WatchService` — specification/lifecycle/test/baseline/list/read façade;
- `WatchProviderRegistry` — provider capability/connection/discovery adapter registry;
- `WatchEvaluationService` — normalization, condition evaluation, effects, receipts, due work;
- `ProjectService` — final Project creation and Project application façade;
- `ProjectStewardService` — durable Project-level reasoning/action runs requested by Watch rules.

`ProjectSetupService.finalize()` MUST call one `ProjectService.create_from_setup()` transaction. Existing `ReactionService` operations MUST delegate to the new Watch boundaries or remain compatibility adapters without creating a second lifecycle.

Required command/read methods include:

```text
start/get/answer/suggest/finalize/abandon setup
begin connection / connection status / capabilities / discover
propose/test Watch proposal
list/get/update/test/baseline/evaluate/pause/retire Watch
list Watch evaluations/effects
```

HTTP paths SHOULD follow:

```text
/api/project-setups/{session_id}/...
/api/provider-connections/{connection_id}/...
/api/projects/{project_id}/watches
/api/watches/{watch_id}/test|baseline|evaluate|pause|retire
/api/watches/{watch_id}/evaluations|effects
```

Every command MUST use the common command ID, expected revision where applicable, structured result, typed error, and atomic event contract.

## 11. Provider adapter contract

```python
class WatchProviderAdapter(Protocol):
    provider_id: str
    transport: Literal["mcp_app", "connector_pack", "local_domain"]

    def manifest(self) -> ProviderCapabilityManifest: ...
    def connection_status(self, principal, connection_ref) -> ProviderConnectionStatus: ...
    def begin_connection(self, principal, requested_capabilities, return_context): ...
    def discover(self, principal, connection_ref, capability, query, cursor): ...
    def validate_watch(self, principal, connection_ref, spec) -> WatchValidationResult: ...
    def snapshot(self, principal, connection_ref, spec, cursor) -> ProviderSnapshot: ...
    def execute_effect(self, principal, connection_ref, effect, idempotency_key): ...
```

`execute_effect` is optional. The manifest is authoritative about its absence.

## 12. Scheduling and action execution

- The conductor invokes `WatchService.evaluate_due()` within its own failure boundary.
- `next_evaluation_at`, not an in-memory map, is the restart-safe cursor.
- Evaluation claims a Watch with compare-and-set semantics.
- Identical provider reads MAY be shared only when connection, subject kind, scope, and query hashes match; each Watch evaluates independently.
- Poll and event delivery of the same source revision deduplicate at `watch_evaluations`.
- Source failures retain last-known-good baseline and create degraded freshness.
- Watch edits increment revision; material edits stale test/baseline.
- `project.steward.run_once` requests deduplicate by Project and observation watermark.
- A YOLO action executes without per-event confirmation, but remains validated, idempotent, verified when possible, and receipted.

## 13. Web behavior

V0 remains inside the existing singleton `ProjectMemoryCore` application/scope. The visible label becomes Project Room; route/action IDs remain compatible. The core becomes a thin compatibility host for an extracted `ProjectRoomCore`.

Provider UI uses one functional vocabulary regardless of backend:

```text
Check connection → Discover → Test → Activate
```

Keyboard requirements:

- Enter submits a one-line answer; Shift+Enter inserts a newline;
- Cmd/Ctrl+Enter accepts a structured proposal or final activation;
- Escape returns one interview level;
- Up/Down traverses suggestions/discovery; Space toggles selection;
- Cmd/Ctrl+K opens Project-scoped setup commands;
- voice fills but never auto-submits/activates.

At narrow widths, the live brief follows the question plane in DOM order. Progress, questions, provider readiness, discovery/selection counts, tests, and actions must have accessible names and announcements. Suggestions are controls, not clickable prose. Color is never the only provider state signal.

## 14. MCP driver additions

Expose structured tools/resources over the same setup/Watch services:

```text
project.setup.start|get|answer|suggest_watches|finalize
provider.list|connection.begin|connection.status|capabilities|discover
project.watch.list|get|propose|test|activate|update|evaluate|pause|retire
project.watch.evaluations|effects
```

Provider connection may return structured `owner_action_required`; no access token appears in tool arguments/results. Provider-specific tools are not copied wholesale into the Project model palette. Agents receive semantic provider/Watch operations.

Resources:

```text
holdspeak://providers
holdspeak://provider-connections/{connection_id}
holdspeak://project-setups/{session_id}
holdspeak://projects/{project_id}/watches
holdspeak://watches/{watch_id}/evaluations
```

## 15. Strict V0 slices

### V0-A — outcome interview and native Watches

- durable setup session;
- outcome and signal questions;
- deterministic suggestions for local Meetings, Decisions, actions, and evidence;
- Blank escape hatch;
- finalization and Project Room Watch summary.

### V0-B — GitHub connection and PR Watches

- connection/auth status and repository discovery or exact typed repo fallback;
- one PR Watch per selected repository;
- open/all plus bounded filters;
- manual test, current matches, baseline, manual evaluation;
- normalized PR observations into Delta.

No GitHub writes or webhooks are required.

### V0-C — scheduled YOLO action

- `every_minutes` polling;
- checks changed-to-failure and PR merged conditions;
- `project.observe`, `project.steward.run_once`, and optional deduplicated `door.add_item`;
- evaluation/effect history, idempotency, and degraded-source state.

### V0-D — Jira provider parity

- real Jira connection/discovery/search adapter (acli transport);
- constrained Project/issue type/status Watch;
- test, baseline, poll, semantic observations, and same Project actions.

This slice enters the proving V0 only if Jira is selected for the EverDriven Project. Otherwise it follows GitHub proof. It MUST NOT simulate readiness with pushed fixtures.

### V0-E — provider write effects

Only after repeated Watch/Steward value:

- one explicit GitHub or Jira write capability;
- idempotency, readback, receipt, YOLO, and indeterminate-outcome behavior.

## 16. Time-to-value and validation

| ID | Requirement / threshold | Verify |
|---|---|---|
| VAL-INT-001 | At least 80% of design partners create one tested Watch in their first session. | U |
| VAL-INT-002 | Median Create Project → active Watch is at most 5 minutes with existing auth; p90 at most 10 minutes. | T,U |
| VAL-INT-003 | At least 60% of installed first Watches originate from a recommendation without custom query syntax. | U,I |
| VAL-INT-004 | At least 4/5 partners say the live test made the watched population clear. | U |
| VAL-INT-005 | At least 4/5 see a useful current-state observation or initial assessment before leaving setup. | U |
| VAL-INT-006 | At least 60% of Watch condition events lead to a retained useful attention item, action, or update. | U,I |
| VAL-INT-007 | Median weekly Watch correction time is at most 2 minutes per Project. | U,I |
| VAL-INT-008 | At least 3/5 retain YOLO actions after two weeks. | U |

Falsify or redesign if owners must understand provider query syntax, activate generic “watch everything” rules, repeatedly repair scopes, cannot predict live-test results, or disable YOLO because cleanup offsets value.

## 17. Acceptance journeys

### SETFLOW-001 — GitHub-first creation

Given authenticated GitHub capability, the owner says:

> Ship the routing upgrade without merging broken integrations. Watch critical checks and reviews that become blocked.

HoldSpeak MUST recommend CI Health/Review Queue, discover or validate the exact repo, compile a readable PR query and conditions, show current PRs/concerns, propose actions/cadence, baseline and activate, open populated Now, and support initial assessment. Prepared-fixture completion MUST be under five minutes without JSON/query authoring.

### SETFLOW-002 — later semantic change

When a watched PR's checks change to failure, one evaluation MUST add Project attention/observation, request at most one configured Steward run, perform any enabled idempotent action without prompting, and appear in Delta with source evidence. An identical refresh MUST perform no duplicate effect.

### SETFLOW-003 — missing connection

Installed-but-unauthenticated GitHub MUST return `owner_action_required`, preserve setup, name/launch provider recovery, and offer Recheck/continue-without. GitHub MUST never appear active before a passing test.

### SETFLOW-004 — connected but unmapped MCP/app

A provider with tools/resources but no Watch adapter MUST appear `Connected · Watch mapping unavailable`, remain non-installable, and never receive invented identity/query semantics.

### SETFLOW-005 — Jira honesty

Until live search/discovery exists, Jira MUST appear partial rather than ready. Once the adapter exists, a blocked/due-risk Watch MUST produce one typed Delta and one configured action after a fixture transition, with no duplicate on unchanged refresh.

### SETFLOW-006 — correction

Editing an overbroad Watch MUST preserve history, test a new revision, preview its population, replace the baseline only at activation, and avoid replaying old entities as new.
