# HS-105-01 badge-source map

Static audit of the HoldSpeak tree on 2026-07-25. This is a source map, not a
proposal to manufacture state in the browser.

Legend:

- **SOURCE** — an existing hub response carries the object-local fact. Computing
  `array.length`, comparing a timestamp with `now`, or joining by an explicit ID
  is allowed and is called out.
- **ABSENT** — no stable object-local response field exists today. A qualifier
  distinguishes a meaningful badge that needs a new field from a badge that is
  not applicable to the kind and should be dropped. Parsing prose is never a
  source.

## Executive findings

1. The desk `kb` is not the Project Facts glossary. It is a named bag of
   resource memberships (`member_ids`); its model explicitly distinguishes
   itself from project-scoped KB files
   (`holdspeak/db/models.py:522-545`). Therefore a **member count is live**, but
   the story's literal “KB with 14 facts” badge is **ABSENT**. The unrelated
   Project Facts endpoint returns a `kb` dictionary selected by
   `project_root`, not by desk-KB id
   (`holdspeak/web/routes/dictation/kb.py:21-45`).
2. HS-103-04 has a live global health signal, but not a per-profile or
   per-agent field. `GET /api/setup/status` exposes
   `sections[?id=="endpoint-health"].status/detail`; `detail` is prose containing
   breaker keys. A per-agent open-circuit badge is therefore **ABSENT** unless
   the hub adds structured endpoint rows keyed to a target/profile. Parsing
   `detail` would be a decorative guess.
3. Except for an open Meeting conflict, there is no per-object sync state.
   `last_modified` is a conflict clock, not “synced/pending/error,” and
   `POST /api/sync/push` returns only aggregate `received` counts.
4. Most modified timestamps exist on hub routes but are discarded by the desk's
   wire adapters. Counts and Attention are much closer to render-ready than
   freshness.
5. `profile` and `run` are not current world-object lanes: `Kind`/`Items` have
   neither (`web/src/desk/api.ts:7-16`, `web/src/desk/api.ts:99-109`), the world
   order has neither (`web/src/desk/world.ts:17-26`), profiles live in a
   separate store array, and `/api/invocations` is not loaded at all
   (`web/src/desk/api.ts:245-387`). Their routes can feed future icons, but those
   icons cannot be rendered from today's `items`.

## 1. Counts and freshness/modified

All counts below are derived from a named collection field; none is inferred
from label text.

### Note

- **Item/fact count — ABSENT (not applicable; drop this badge).** `NoteRecord`
  has content and tags, but no item/fact collection
  (`holdspeak/db/models.py:490-518`). A character count could be derived from
  `body_markdown`, but that is a different badge contract.
- **Freshness — SOURCE.** `GET /api/notes` →
  `notes[].last_modified` (and `notes[].updated_at`). The route returns
  `NoteRecord.to_dict()` (`holdspeak/web/routes/primitives/notes.py:24-29`);
  the DB orders/loads notes at `holdspeak/db/primitives.py:113-125` and maps the
  clocks at `holdspeak/db/primitives.py:145-155`; serialization is
  `holdspeak/db/models.py:508-518`.

### KB / Knowledge

- **Member count — SOURCE.** Batch form: `GET /api/kbs` →
  `kbs[].member_ids.length`
  (`holdspeak/web/routes/primitives/kbs.py:23-28`). Exact edge form:
  `GET /api/kbs/{kb_id}/members` → `members.length`
  (`holdspeak/web/routes/primitives/kbs.py:94-102`). The authoritative edge
  query is `KnowledgeMembershipRepository.list_for_knowledge`
  (`holdspeak/db/relationships.py:130-136`), and edge writes refresh the legacy
  `kbs.member_ids_json` used by the batch route
  (`holdspeak/db/relationships.py:159-167`).
- **Fact count — ABSENT.** There is no `fact_count` and desk Knowledge members
  are qualified resource refs, not Project Facts
  (`holdspeak/db/relationships.py:39-54`). `GET
  /api/dictation/project-kb?project_root=...` → `kb` is a separate,
  project-scoped dictionary with no desk-KB identity
  (`holdspeak/web/routes/dictation/kb.py:21-45`).
- **Freshness — SOURCE.** `GET /api/kbs` → `kbs[].last_modified`. The DB query
  and row map are `holdspeak/db/primitives.py:247-258` and
  `holdspeak/db/primitives.py:276-284`; the wire field is defined at
  `holdspeak/db/models.py:538-545`.

### Zone / Directory

- **Item count — SOURCE.** `GET /api/directories` →
  `directories[].member_ids.length`. The route explicitly queries membership
  rows and injects `member_ids`
  (`holdspeak/web/routes/primitives/directories.py:23-35`); the DB query selects
  only live memberships at `holdspeak/db/primitives.py:1044-1055`.
- **Freshness — SOURCE.** The same response carries
  `directories[].last_modified` through `d.to_dict()`. Directory rows are loaded
  at `holdspeak/db/primitives.py:903-915`, mapped at
  `holdspeak/db/primitives.py:947-955`, and serialized at
  `holdspeak/db/models.py:713-721`.

### Meeting

- **Item counts — SOURCE.** `GET /api/meetings` →
  `meetings[].segment_count` and `meetings[].action_item_count`
  (`holdspeak/web/routes/meetings/crud.py:55-87`). Both are SQL subquery counts
  (`holdspeak/db/meetings.py:594-600`) mapped into `MeetingSummary` at
  `holdspeak/db/meetings.py:632-648`.
- **Freshness — SOURCE, but not on the list route.** Batch source:
  `GET /api/sync/pull` → `meetings[].meta.last_modified`
  (`holdspeak/web/routes/sync.py:478-491`). Per-item source:
  `GET /api/meetings/{meeting_id}` → `sync_modified_at`
  (`holdspeak/web/routes/meetings/crud.py:111-122`;
  `holdspeak/meeting_session/models.py:199-231`). The DB loads that clock at
  `holdspeak/db/meetings.py:497-525` and advances it on a complete save at
  `holdspeak/db/meetings.py:248-292`.

### Recipe / Agent persona

- **Tool count — SOURCE if wanted.** `GET /api/recipes` →
  `recipes[].tools.length` (`holdspeak/web/routes/primitives/recipes.py:52-57`).
  The DB loads `tools_json` at `holdspeak/db/primitives.py:401-416`; the exact
  wire collection is at `holdspeak/db/models.py:579-595`. This is a **tool**
  count, not an item/fact count; label the contract accordingly.
- **Freshness — SOURCE.** `GET /api/recipes` →
  `recipes[].last_modified`, from the same route/serializer. The DB query is
  `holdspeak/db/primitives.py:371-383`.

### Chain / Sequence

- **Step count — SOURCE.** `GET /api/chains` → `chains[].steps.length`
  (`holdspeak/web/routes/primitives/chains.py:44-50`). DB query/map:
  `holdspeak/db/primitives.py:698-710`,
  `holdspeak/db/primitives.py:728-736`; wire shape:
  `holdspeak/db/models.py:676-684`.
- **Freshness — SOURCE.** Same route → `chains[].last_modified`.

### Workflow

- **Raw graph-node count — SOURCE with a caveat.** `GET /api/workflows` →
  `workflows[].graph_json.nodes.length`
  (`holdspeak/web/routes/primitives/workflows.py:52-57`). The DB preserves the
  graph dictionary byte-faithfully
  (`holdspeak/db/primitives.py:798-810`, `holdspeak/db/primitives.py:829-837`).
  A canonical graph's `nodes` includes plumbing nodes such as entry/source/output
  (`web/src/desk/graph.ts:89-118`), so a semantic “action-step count” is
  **ABSENT** unless its exclusion rule is specified or the hub adds
  `action_step_count`.
- **Freshness — SOURCE.** Same route → `workflows[].last_modified`, serialized
  at `holdspeak/db/models.py:783-792`.

### Profile / inference destination

- **Item/fact count — ABSENT (not applicable; drop this badge).**
- **Freshness — SOURCE.** `GET /api/profiles` →
  `profiles[].last_modified`
  (`holdspeak/web/routes/primitives/profiles.py:49-75`). The DB query/map is
  `holdspeak/db/primitives.py:498-503` and
  `holdspeak/db/primitives.py:521-535`; the wire shape is
  `holdspeak/db/models.py:644-658`.

### Artifact

- **Source count — SOURCE if wanted.** `GET /api/sync/pull` →
  `artifacts[].value.sources.length`; **freshness — SOURCE** at
  `artifacts[].meta.last_modified`
  (`holdspeak/web/routes/sync.py:492-510`,
  `holdspeak/web/routes/sync.py:150-169`). Artifact rows and sources are loaded
  together at `holdspeak/db/plugins.py:845-884` and
  `holdspeak/db/plugins.py:886-950`; `updated_at` is the DB clock used by the
  sync envelope. This is a lineage-source count, not a generic item count.

### Run / capability invocation

- **Attempt count — SOURCE.** `GET /api/invocations` →
  `invocations[].attempts.length`; **freshness — SOURCE** at
  `invocations[].updated_at`
  (`holdspeak/web/routes/primitives/invocations.py:20-25`). The DB list and
  nested attempt load are `holdspeak/db/invocations.py:133-151` and
  `holdspeak/db/invocations.py:170-180`; exact serialization is
  `holdspeak/db/models.py:846-862`.

### Coder session

- **Event count — SOURCE if wanted.** `GET /api/coders/status` →
  `agent.sessions.items[].session.event_count`; **freshness — SOURCE** at
  `.session.updated_at`, with already-derived
  `agent.sessions.items[].age_seconds`
  (`holdspeak/web/routes/system/coders.py:168-195`,
  `holdspeak/web/routes/system/coders.py:237-249`). For the broader live set,
  `GET /api/coders/sessions` returns
  `sessions[].session.updated_at/event_count` and `sessions[].age_seconds`
  (`holdspeak/web/routes/system/coders.py:291-331`).
- Coder sessions are not DB rows. Their durable source is the local
  agent-session registry: `AgentSession.to_dict()` carries `updated_at` and
  `event_count` (`holdspeak/agent_context/models.py:178-206`), and the registry
  loads/sorts them at `holdspeak/agent_context/sessions.py:769-786`. Do not cite
  a fictitious DB repository for this kind.

## 2. Egress posture

### Profile — declared posture is live

**SOURCE:** `GET /api/inference-targets` →
`targets[].{id,profile_id,kind,boundary,owner,transport,data_scope,readiness}`.
The route builds these targets from DB profiles
(`holdspeak/web/routes/primitives/profiles.py:167-186`;
profile DB query `holdspeak/db/primitives.py:498-503`). The target serializer
defines the exact boundary fields at `holdspeak/inference_targets.py:81-114`,
and `target_from_profile` maps on-device, paired-device, mesh, private endpoint,
and external service profiles at `holdspeak/inference_targets.py:174-253`.

An at-rest “leaves this device” mark can therefore be based on a named
`boundary`/`kind` contract, not on URL guessing.

### Recipe / Agent — declared default posture is live by an explicit join

**SOURCE:** `GET /api/recipes` → `recipes[].profile_id` (or
`recipes[].capability.supported_placements`) joined to `GET
/api/inference-targets` by target/profile id. The recipe route emits the
placement contract at `holdspeak/web/routes/primitives/recipes.py:27-34` and
the DB stores `profile_id` at `holdspeak/db/primitives.py:293-355`. A null
profile is explicitly `this_machine`.

This is the Agent's declared default. It is not a claim about a past run.

### Chain and Workflow — no saved definition posture

- **Chain: ABSENT.** The saved chain has only `steps`; its run target is chosen
  from the POST body or defaults to `this_machine`
  (`holdspeak/web/routes/primitives/chains.py:178-187`). Agent profile ids are
  not a truthful chain-level egress source because the chain runner uses the
  one request-selected target for all steps.
- **Workflow: ABSENT.** The saved definition has no persisted target; the run
  target is chosen from the POST body or defaults to `this_machine`
  (`holdspeak/web/routes/primitives/workflows.py:208-213`). Graph-node
  `runs_on` is carried but explicitly not enforced by this hub
  (`holdspeak/web/routes/primitives/workflows.py:145-163`), so it cannot drive
  an “actual egress” badge.

### Run — actual posture is live

**SOURCE:** `GET /api/invocations` (or `/api/invocations/{id}`) →
`invocations[].attempts[-1].actual_placement.{target_id,target_kind,boundary,owner,transport,engine,model}`.
The read routes are
`holdspeak/web/routes/primitives/invocations.py:20-36`; the attempt DTO is
`holdspeak/db/models.py:811-824`, and actual placement is persisted by
`holdspeak/db/invocations.py:52-77`. The receipt fields are defined at
`holdspeak/inference_targets.py:116-140` and written by the run lifecycle at
`holdspeak/web/routes/primitives/_shared.py:129-180`.

### Artifact — only run-born artifacts can be resolved

**SOURCE for `origin=="run"` only:** `GET /api/sync/pull` →
`artifacts[].value.{origin,sources}`; find the source with
`source_type=="invocation"`, then fetch `GET /api/invocations/{source_ref}` and
use its last attempt's `actual_placement.boundary`. Run artifacts intentionally
carry invocation lineage
(`holdspeak/web/routes/primitives/_shared.py:186-190`,
`holdspeak/web/routes/primitives/_shared.py:256-287`), and sync emits origin and
sources (`holdspeak/web/routes/sync.py:150-169`).

**ABSENT for meeting-born artifacts:** no historical provider/boundary is
stored on `ArtifactSummary` (`holdspeak/db/models.py:198-216`).

### Note, KB, Zone, Meeting, Coder session

**ABSENT (not applicable; drop this badge)** for object-local egress posture.
In particular, current global setup egress is not historical per-meeting
egress, so it must not be copied onto old Meetings or Artifacts.

## 3. Endpoint-health / open-circuit

The internal structured truth exists:
`EndpointHealth.snapshot()[endpoint_key].circuit_open` plus failure counters
(`holdspeak/intel/endpoint_health.py:99-117`). It is reduced to a doctor check
at `holdspeak/commands/doctor.py:1210-1231`, converted to generic
`{id,label,status,detail,fix}` sections
(`holdspeak/setup_status.py:30-46`), and exposed by:

- `GET /api/setup/status` →
  `sections[?id=="endpoint-health"].status`
- same section → `detail` (human prose naming all breaker keys)

Route and envelope citations:
`holdspeak/web/routes/setup.py:26-40`,
`holdspeak/setup_status.py:192-199`,
`holdspeak/setup_status.py:227-235`.

This is a **SOURCE only for one global “some endpoint circuit is open” system
mark**. It is **ABSENT for Profile, Recipe/Agent, Chain, Workflow, Run, and
Artifact icons** because:

- the response has no structured endpoint rows;
- breaker keys are transport-oriented (`cloud:{base_url-or-model}` or
  `dictation:{base_url}`), not stable profile ids
  (`holdspeak/intel/engine.py:169-173`,
  `holdspeak/plugins/dictation/runtime_openai_compatible.py:102-105`);
- a run failure exposes only an error string, not `circuit_open`.

Minimum honest new contract: add a structured array/map such as endpoint key +
`circuit_open` + failure counters, and either a stable `profile_id`/`target_id`
or an explicit target-to-endpoint-key mapping. The names are illustrative; the
current code does **not** provide such fields.

## 4. Needs-you / Attention

The canonical badge source is:

`GET /api/desk/projections` →
`subject_counts[<canonical-subject-ref>].needs_attention`.

The route returns the envelope at
`holdspeak/web/routes/projections.py:16-42`. The DB builds subject counts before
drawer filters, increments only rows whose `attention_state` is exactly
`needs_attention`, and returns the map at
`holdspeak/db/projections.py:83-126`.

Per-kind availability:

| Kind | Subject key / field | Status and authoritative producer |
|---|---|---|
| Note | `subject_counts["note:{id}"].needs_attention` | **SOURCE**, for Desk actuator proposals whose source is a Note. The source route admits only Meeting, Note, or Artifact (`holdspeak/web/routes/desk_actuators.py:45-73`); the projection maps its `_source.ref` and proposal lifecycle at `holdspeak/db/projections.py:197-298`. |
| KB / Knowledge | would be `knowledge:{id}` | **ABSENT.** No projection producer emits a Knowledge subject. |
| Zone / Directory | would be `zone:{id}` | **ABSENT.** No projection producer emits a Zone subject. |
| Meeting | `meeting:{id}` | **SOURCE.** Capture recovery, sync conflicts, intel/plugin jobs, meeting proposals, and meeting-related cadence rows emit this subject (`holdspeak/db/projections.py:415-458`, `holdspeak/db/projections.py:482-506`, `holdspeak/db/projections.py:517-530`). |
| Recipe / Agent | `persona:{id}` | **SOURCE.** Failed/unavailable/empty capability invocations become needs-attention projections (`holdspeak/db/projections.py:300-340`). |
| Chain / Sequence | `sequence:{id}` | **SOURCE**, from the same invocation producer. |
| Workflow | `workflow:{id}` | **SOURCE**, from the same invocation producer. |
| Profile | would be `profile:{id}` | **ABSENT.** Target readiness is available elsewhere, but no Attention producer uses a Profile subject. |
| Artifact | `artifact:{id}` | **SOURCE.** `draft` and `needs_review` are needs-attention (`holdspeak/db/projections.py:460-480`); actuator proposals can also use the Artifact as source. |
| Run / Invocation | no invocation subject count exists | **SOURCE directly, not through `subject_counts`:** `GET /api/invocations` → `invocations[].state`; the existing projection policy defines `failed`, `unavailable`, and `empty` as needs-attention (`holdspeak/db/projections.py:309-329`). A true invocation-scoped Attention count is **ABSENT**. |
| Coder session | `coder_session:{agent}:{session_id}` | **SOURCE** when steering/cadence rows exist (`holdspeak/db/projections.py:370-413`, `holdspeak/db/projections.py:508-547`). Immediate waiting truth is also live at `GET /api/coders/status` → `agent.sessions.items[].session.awaiting_response`/`question` (`holdspeak/web/routes/system/coders.py:168-195`). |

An unsupported subject returning no entry is not evidence that the feature is
healthy; for KB/Zone/Profile it means there is no producer. Do not render a
permanent zero badge for those kinds.

## 5. Sync state

### Meeting

- **SOURCE for the only explicit state, “open conflict”:**
  `GET /api/meetings/{meeting_id}/sync-conflicts` →
  `conflicts.length` (`holdspeak/web/routes/meetings/crud.py:162-168`).
  The DB query returns only `resolved_at IS NULL`
  (`holdspeak/db/meetings.py:98-106`) and serializes each conflict at
  `holdspeak/db/meetings.py:215-225`.
- The same open conflict also becomes Meeting Attention with reason
  `sync_conflict_open` (`holdspeak/db/projections.py:437-458`).
- **ABSENT for generic clean/pending/synced/error state.**

### Every other kind

**ABSENT.** `GET /api/sync/pull` carries change records with
`meta.{id,kind,last_modified,deleted}`; `_primitive_record` defines that exact
header at `holdspeak/web/routes/sync.py:172-193`. It is a clock/tombstone, not a
delivery state. `POST /api/sync/push` returns only
`{"success":true,"received":{bucket:count}}`
(`holdspeak/web/routes/sync.py:737-766`), with no per-object ack/status.

That absence covers Note, KB, Zone, Recipe, Chain, Workflow, Profile, and
Artifact. Runs are not in the sync pull at all, and coder sessions are a local
registry rather than sync primitives.

## 6. What the web client already holds

### `useDesk` (`web/src/desk/store.ts`)

`DeskState` holds `items`, raw `profiles`, typed `inferenceTargets`, route
reachability `status`, and the full setup object
(`web/src/desk/store.ts:160-179`). Refresh stores those exact values at
`web/src/desk/store.ts:366-383`.

The normalization in `web/src/desk/api.ts` determines badge readiness:

| Kind | Already held client-side | Live hub badge fields currently dropped |
|---|---|---|
| Note | `bodyMarkdown`, `tags`, `createdAt` | `updated_at`, `last_modified` (`web/src/desk/api.ts:123-130`) |
| KB | `memberIds`, `createdAt` — member count is ready | `last_modified`; no fact count exists (`web/src/desk/api.ts:146-152`) |
| Zone | `memberIds`, `parentId`, `createdAt` — item count is ready | `last_modified` (`web/src/desk/api.ts:154-161`) |
| Meeting | `startedAt`, `endedAt`, `segmentCount`, `actionItemCount`, duration | no `sync_modified_at`/modified field; list adapter also drops capture fields (`web/src/desk/api.ts:186-197`) |
| Recipe / Agent | `tools`, `kbId`, `profileId`, `capability`; `inferenceTargets` is also in the store, so declared egress is join-ready | `last_modified` (`web/src/desk/api.ts:132-144`, `web/src/desk/api.ts:341-344`) |
| Chain | `steps`, `capability` — step count is ready | `last_modified` (`web/src/desk/api.ts:163-169`) |
| Workflow | `graphJson`, `hasGraph`, `capability` — raw node count is possible | `last_modified` (`web/src/desk/api.ts:171-184`) |
| Profile | raw profile objects retain `last_modified`; typed `inferenceTargets` retain boundary/readiness | not an `items`/world lane (`web/src/desk/api.ts:321-344`) |
| Artifact | `status`, `sources`, content — source count is ready | sync `meta.last_modified` and `value.origin` are lost because `liveValues` unwraps the envelope and `fromWireArtifact` omits both (`web/src/desk/api.ts:115-120`, `web/src/desk/api.ts:199-209`, `web/src/desk/api.ts:266-270`) |
| Run | nothing; `/api/invocations` is never fetched | all run badge fields |
| Coder session | `state`, `question`, `selected`, `pinned`, `stale` — direct waiting/needs-you and stale presentation are ready | `updated_at`, `age_seconds`, `event_count`, raw `awaiting_response` (`web/src/desk/api.ts:211-243`) |

Two traps:

- `DeskState.updatedAt` is the browser refresh time (`Date.now()`), not any
  item's modification time (`web/src/desk/store.ts:366-383`).
- `Status` is only per-route `"live" | "unreachable"`, not per-item sync or
  endpoint health (`web/src/desk/api.ts:27-29`).

The setup object loaded into `useDesk.setup` contains the runtime
`sections` array, so the global endpoint-health section is present at runtime;
`SetupStatus` does not type that field explicitly, relying on its index
signature (`web/src/desk/setup.ts:20-35`).

### `useProjections` (`web/src/desk/projections.ts`)

The client already types and stores:

- every projection's `subject_ref`, `attention_state`, `timestamp`, `severity`,
  and provenance (`web/src/desk/projections.ts:4-30`);
- the exact badge-ready
  `subject_counts: Record<string,{needs_attention,receipts}>`
  (`web/src/desk/projections.ts:32-36`);
- `subject_counts` from every full refresh
  (`web/src/desk/projections.ts:90-108`).

The scene already consumes that map and writes `counts?.needs_attention || 0`
onto each world object (`web/src/desk/gl/sceneModel.ts:119-155`), and the list
view renders the same count (`web/src/desk/components/DeskListView.tsx:135-168`).
Thus Attention is not merely available client-side; it is already wired into
the scene model.

## 7. Ship/no-ship interpretation for HS-105-01

Can ship from existing live data once adapters retain the fields:

- Zone member count, KB **member** count, Meeting counts, Sequence steps,
  optional tools/sources/attempts/events counts;
- a record/event freshness clock for every listed kind;
- declared egress for Profile and Agent;
- actual egress for Run (and run-born Artifact through an explicit join);
- Attention for Note, Meeting, Agent, Sequence, Workflow, Artifact, and coder
  sessions as qualified above;
- Meeting open-sync-conflict.

Cannot honestly ship without a hub contract change:

- literal desk-KB **fact** count;
- per-profile/per-agent/per-run `circuit_open`;
- generic per-object sync state;
- saved chain/workflow egress posture;
- historical Meeting or meeting-born Artifact egress;
- Attention for KB, Zone, or Profile;
- any Run/Profile world badge before those kinds are added to the desk item/scene
  lanes.

## 8. Final kind × badge matrix

Every badge claim is binary: it names an exact **SOURCE** field or says
**ABSENT**. An absent claim distinguishes “needs a field” from “not applicable;
drop the badge.” “Count” always names what is being counted.

| Kind | Count | Freshness / modified | Egress posture | Open circuit | Needs-you / Attention | Sync state |
|---|---|---|---|---|---|---|
| Note | **ABSENT** (no item/fact collection; drop badge) | **SOURCE** `/api/notes` `notes[].last_modified` | **ABSENT** (not applicable; drop badge) | **ABSENT** (not applicable; drop badge) | **SOURCE** `/api/desk/projections` `subject_counts["note:{id}"].needs_attention` (proposal-backed only) | **ABSENT** |
| KB / Knowledge | **SOURCE** `/api/kbs/{id}/members` `members.length` (members); **ABSENT** literal fact count | **SOURCE** `/api/kbs` `kbs[].last_modified` | **ABSENT** (not applicable; drop badge) | **ABSENT** (not applicable; drop badge) | **ABSENT** | **ABSENT** |
| Zone / Directory | **SOURCE** `/api/directories` `directories[].member_ids.length` | **SOURCE** `/api/directories` `directories[].last_modified` | **ABSENT** (not applicable; drop badge) | **ABSENT** (not applicable; drop badge) | **ABSENT** | **ABSENT** |
| Meeting | **SOURCE** `/api/meetings` `meetings[].segment_count`, `meetings[].action_item_count` | **SOURCE** `/api/sync/pull` `meetings[].meta.last_modified` | **ABSENT** historical actual egress | **ABSENT** per Meeting | **SOURCE** `/api/desk/projections` `subject_counts["meeting:{id}"].needs_attention` | **SOURCE** `/api/meetings/{id}/sync-conflicts` `conflicts.length` for open conflict only; generic state **ABSENT** |
| Recipe / Agent | **SOURCE** `/api/recipes` `recipes[].tools.length` (tools) | **SOURCE** `/api/recipes` `recipes[].last_modified` | **SOURCE** `/api/recipes` `recipes[].profile_id` joined to `/api/inference-targets` `targets[?id==profile_id].boundary` | **ABSENT** per Agent; global setup section only | **SOURCE** `/api/desk/projections` `subject_counts["persona:{id}"].needs_attention` | **ABSENT** |
| Chain / Sequence | **SOURCE** `/api/chains` `chains[].steps.length` | **SOURCE** `/api/chains` `chains[].last_modified` | **ABSENT** saved posture | **ABSENT** (no saved target) | **SOURCE** `/api/desk/projections` `subject_counts["sequence:{id}"].needs_attention` | **ABSENT** |
| Workflow | **SOURCE** `/api/workflows` `workflows[].graph_json.nodes.length` (raw nodes); semantic action count **ABSENT** | **SOURCE** `/api/workflows` `workflows[].last_modified` | **ABSENT** saved/actual posture | **ABSENT** (no saved enforced target) | **SOURCE** `/api/desk/projections` `subject_counts["workflow:{id}"].needs_attention` | **ABSENT** |
| Profile | **ABSENT** (no item/fact collection; drop badge) | **SOURCE** `/api/profiles` `profiles[].last_modified` | **SOURCE** `/api/inference-targets` `targets[?profile_id==profile.id].kind` / `.boundary` | **ABSENT** per Profile; global setup section only | **ABSENT** | **ABSENT** |
| Artifact | **SOURCE** `/api/sync/pull` `artifacts[].value.sources.length` (lineage sources) | **SOURCE** `/api/sync/pull` `artifacts[].meta.last_modified` | **SOURCE** for `value.origin=="run"` via `value.sources[?source_type=="invocation"].source_ref` joined to `/api/invocations/{source_ref}` `invocation.attempts[-1].actual_placement.boundary`; meeting-born **ABSENT** | **ABSENT** per Artifact | **SOURCE** `/api/desk/projections` `subject_counts["artifact:{id}"].needs_attention` | **ABSENT** |
| Run / Invocation | **SOURCE** `/api/invocations` `invocations[].attempts.length` | **SOURCE** `/api/invocations` `invocations[].updated_at` | **SOURCE** `/api/invocations` `invocations[].attempts[-1].actual_placement.boundary` | **ABSENT** structured flag (error prose is not a source) | **SOURCE** `/api/invocations` `invocations[].state` using existing failed/unavailable/empty policy; invocation subject-count **ABSENT** | **ABSENT** (not a synced kind; drop badge) |
| Coder session | **SOURCE** `/api/coders/status` `agent.sessions.items[].session.event_count` (events) | **SOURCE** `/api/coders/status` `agent.sessions.items[].session.updated_at` or sibling `age_seconds` | **ABSENT** (not applicable; drop badge) | **ABSENT** (not applicable; drop badge) | **SOURCE** immediate `/api/coders/status` `agent.sessions.items[].session.awaiting_response`/`question`; `/api/desk/projections` `subject_counts["coder_session:{agent}:{id}"].needs_attention` when cadence/steering records exist | **ABSENT** (local registry, not a sync primitive; drop badge) |
