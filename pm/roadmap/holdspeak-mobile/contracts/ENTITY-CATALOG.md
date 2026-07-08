# HoldSpeak Entity Catalog (HSM-0-01)

**Status:** in-progress (HSM-0-01). The reverse-engineered inventory of every
domain entity the shipped desktop product emits, traced to source, so the JSON
Schemas (HSM-0-02) and serialization contract (HSM-0-03) are grounded in real
behavior rather than the charter's prose list.

**Source tree:** `holdspeak/` at the repo this roadmap lives in (desktop v0.3.0).
**Home note:** this file sits under the roadmap project for now; HSM-0-03 decides
the final `holdspeak-contracts` package home and may relocate it.

> Tracing convention: each field cites `file:line` against the shipped code. The
> charter's ten Layer-1 entities are mapped first; everything else the extraction
> surfaced is in "Beyond the charter."

---

## Headline findings (these drive HSM-0-02 / HSM-0-03)

1. **`Artifact` is a tagged union, not ten classes.** Decision, Risk,
   Requirement, ADR, Follow-up etc. are **`artifact_type` discriminator values**
   on a single `ArtifactDraft`/`ArtifactSummary`, each carrying a type-specific
   `structured_json` blob. The 15 shipped types come from
   `_ARTIFACT_TYPE_BY_PLUGIN` (`holdspeak/plugins/synthesis.py:13`). The contract
   should model `Artifact` as a discriminated type with an open `structured_json`,
   not invent one class per charter artifact noun.
2. **Two unrelated "profile" concepts.** The **MIR meeting profile**
   (`balanced/architect/delivery/product/incident`, `plugin_sdk.py:65`,
   `config.py:154`) routes meeting intelligence — this is the one Phase 7 ports.
   The **dictation target profile** (`codex_cli/claude_code/chat/editor/...`,
   `target_profile.py`) routes dictation rewrites. They must not be conflated in
   the contract.
3. **No first-class `Transcript` or `Speaker` entity.** The charter lists both,
   but desktop models a transcript as `MeetingState.segments:
   list[TranscriptSegment]` (+ a `transcript_hash()`), and a speaker as the
   `speaker`/`speaker_id`/`device_id` fields on a segment. HSM-0-03 must decide
   whether the contract mints explicit `Transcript`/`Speaker` types or keeps them
   implicit (recommendation: a thin `Transcript` wrapper for sync addressing; keep
   `Speaker` as the segment fields plus an optional roster).
4. **Mixed timestamp representations.** `datetime` objects (`MeetingState`),
   ISO-8601 strings (`ActionItem.created_at`, all `ActuatorProposalRecord`
   stamps), and float seconds-since-meeting-start (segment timing,
   `Bookmark.timestamp`). HSM-0-03 must pin one wire format and a meeting-relative
   vs. absolute rule.
5. **Mixed ID representations.** Content-hash strings (`ActionItem.id` =
   `sha256[:12]`, `intel/models.py:33`), opaque strings (`MeetingState.id`),
   autoincrement ints (`ConnectorRun.id`, `DictationJournalRecord.id`). HSM-0-03
   must decide the cross-runtime ID rule (recommendation: string ids everywhere on
   the wire).
6. **Egress scope is a UI concept, not yet a model field.** The desktop egress
   badge (Phase 62) is computed at the surface, not stored on `Artifact`/`Action`.
   The charter wants the contract able to carry it — HSM-0-03 decides whether to
   add an optional `egress` field to actionable entities.

---

## Charter Layer-1 entities

### 1. Meeting → `MeetingState` (+ `MeetingSummary`)

`holdspeak/meeting_session/models.py:118` (`MeetingState`),
`holdspeak/db/models.py:24` (`MeetingSummary`, the list-view projection).

| Field | Type | Notes / source |
|---|---|---|
| `id` | str | opaque meeting id — `models.py:121` |
| `started_at` | datetime | `:122` |
| `ended_at` | datetime? | None while active (`is_active`) — `:123` |
| `title` | str? | `:124` |
| `tags` | list[str] | `:125` |
| `segments` | list[TranscriptSegment] | the transcript — `:126` |
| `bookmarks` | list[Bookmark] | `:127` |
| `intel` | IntelSnapshot? | latest snapshot — `:128` |
| `intel_status` | str enum | `disabled`/`requested`/`running`/`ready`/`failed` family — `:129` (serialized as nested `intel_status{state,detail,requested_at,completed_at}` — `:200`) |
| `intel_status_detail` | str? | `:130` |
| `intel_requested_at` / `intel_completed_at` | datetime? | `:131-132` |
| `mic_label` / `remote_label` | str | speaker display defaults — `:133-134` |
| `web_url` | str? | `:135` |
| `devices` | list[DeviceDescriptor] | AIPI-Lite contributors — `:139` |
| derived (serialized): `duration`, `formatted_duration` | — | `to_dict()` adds these; not stored — `:188-210` |
| derived (not serialized): `is_active`, `transcript_hash()` | — | `:141-186` |

> **`mir_profile` is NOT a Meeting field.** Verified against a live
> `MeetingState.to_dict()` (see cross-check below): the active MIR profile lives
> in **config** (`config.py:154 mir_profile`, `:165 plugin_profile`) and is only
> persisted per-meeting on `IntentWindowSummary.profile` when MIR runs. So
> Phase-7 HSM-7-03 ("carry the profile on the `Meeting`") is a **contract
> addition**, escalated to HSM-0-03 — not an existing serialized field.

> **`intel_status` serializes nested.** `to_dict()` emits
> `intel_status: {state, detail, requested_at, completed_at}` (`:200`), even
> though the in-memory field is a flat string. HSM-0-02 must schema the nested
> shape (this exact nesting bit the desktop in Phase 55).

`MeetingSummary` adds `duration_seconds`, `segment_count`, `action_item_count`
(`db/models.py:24`) — a projection for `/history`, useful for the mobile Review
Queue (Phase 9).

### 2. Transcript → implicit (`MeetingState.segments` + `transcript_hash()`)

No standalone type. The transcript is the ordered `list[TranscriptSegment]` on a
`MeetingState`, with `transcript_hash()` (`models.py:180`) as its stable digest
(used as the intel-job idempotency key). **HSM-0-03 decision:** mint a thin
`Transcript` contract type (meeting_id + ordered segments + hash) for sync
addressing, or keep implicit.

### 3. Speaker → implicit (segment fields; runtime diarizer separate)

No persisted `Speaker` entity. Speaker identity lives on the segment as `speaker`
(display name), `speaker_id` (link, None for "Me"), `device_id`
(`meeting_session/models.py:39-48`). `SpeakerEmbedding`/`SpeakerDiarizer`
(`speaker_intel.py:73,126`) are runtime diarization machinery, not a serialized
contract. **HSM-0-03 decision:** keep speaker as segment fields + an optional
per-meeting speaker roster; the Phase-3 `Segment` (HSM-3-04) reserves the slot.

### 4. Segment → `TranscriptSegment`

`holdspeak/meeting_session/models.py:36`.

| Field | Type | Source |
|---|---|---|
| `text` | str | `:38` |
| `speaker` | str | display name ("Me"/"Speaker 1"/"John") — `:39` |
| `start_time` / `end_time` | float | seconds since meeting start — `:40-41` |
| `is_bookmarked` | bool | `:42` |
| `speaker_id` | str? | identity link, None for "Me" — `:43` |
| `device_id` | str? | producing AIPI-Lite device — `:48` |
| derived: `duration`, `format_timestamp()` | — | `:51-67` |

This is the shape Phase 3 (HSM-3-04) emits "speaker-ready."

### 5. ActionItem → `ActionItem` (+ `ActionItemSummary`)

`holdspeak/intel/models.py:40` (`ActionItem`), `db/models.py:81`
(`ActionItemSummary`, with meeting context).

| Field | Type | Source |
|---|---|---|
| `task` | str | `:43` |
| `owner` | str? | `:44` |
| `due` | str? | free-text due — `:45` |
| `id` | str | `sha256(task:owner)[:12]`, auto if blank — `:46`,`:33` |
| `status` | str enum | `pending`/`done`/`dismissed` — `:47`, `db/models.py:13` |
| `review_state` | str enum | `pending`/`accepted` — `:48`, `db/models.py:14` |
| `reviewed_at` | str? (ISO) | `:49` |
| `source_timestamp` | float? | link to transcript moment — `:50` |
| `created_at` | str (ISO) | `:51` |
| `completed_at` | str? (ISO) | `:52` |

The `review_state`/`accept()` flow is the Propose→Review→Approve lifecycle the
charter preserves; `source_timestamp` is the transcript-moment link (mobile
transcript linking, HSM-8-03, mirrors this).

### 6. Decision → `Artifact` with `artifact_type="decisions"`

Produced by the `decision_capture` plugin (`synthesis.py:13` map). Not a class —
a tagged `Artifact` (see entity 10) whose `structured_json` carries the decision
shape. Related: `decision_announcement` (artifact_type, `decision_announcement_drafter`).

### 7. Risk → `Artifact` with `artifact_type="risk_register"`

Produced by the `risk_heatmap` plugin (`synthesis.py:13`). A tagged `Artifact`.

### 8. Requirement → `Artifact` with `artifact_type="requirements"`

Produced by the `requirements_extractor` plugin (`synthesis.py:13`). A tagged
`Artifact`.

### 9. Artifact → `ArtifactDraft` (pre-persist) + `ArtifactSummary` (persisted)

`holdspeak/artifacts.py:35` (`ArtifactDraft`), `db/models.py:188`
(`ArtifactSummary`), `artifacts.py:21` (`ArtifactSourceRef`).

| Field | Type | Source |
|---|---|---|
| `artifact_id` / `id` | str | `artifacts.py:39` |
| `meeting_id` | str | `:40` |
| `artifact_type` | str enum | the discriminator — 15 values, §artifact types — `:41` |
| `title` | str | `:42` |
| `body_markdown` | str | human-rendered body — `:43` |
| `structured_json` | dict | the type-specific payload — `:44` |
| `confidence` | float | `:45` |
| `status` | str enum | `draft`/`needs_review`/`accepted`/`rejected` — `:46`, `artifacts.py:9` |
| `plugin_id` / `plugin_version` | str | producing plugin — `:47-48` |
| `sources` | list[ArtifactSourceRef] | lineage `{source_type, source_ref}` — `:49`,`:21` |
| `created_at` / `updated_at` | datetime | (on `ArtifactSummary`) — `db/models.py:202-203` |

Status default is confidence-derived (`artifact_status_from_confidence`,
`artifacts.py:12`). **This is the union type all of entities 6–8 (and ADR,
Follow-up) collapse into.**

### 10. IntelJob → `IntelJob` (+ `IntelSnapshot`, `IntelResult`)

`holdspeak/db/models.py:40` (`IntelJob`, the deferred-queue record),
`meeting_session/models.py:74` (`IntelSnapshot`, the in-meeting result),
`intel/models.py:80` (`IntelResult`, the engine output).

`IntelJob` fields: `meeting_id`, `status`, `transcript_hash`, `requested_at`,
`updated_at`, `attempts`, `last_error`, `meeting_title?`, `started_at?`,
`intel_status_detail?` (`db/models.py:40-52`). `transcript_hash` is the
idempotency key tying a job to a transcript state. `IntelResult` carries
`topics`, `action_items: list[ActionItem]`, `summary`, `raw_response`, `error?`
(`intel/models.py:80`).

---

## Enum vocabularies (the contract must pin these)

| Vocabulary | Values | Source |
|---|---|---|
| Artifact type (15) | `requirements`, `action_items`, `diagram`, `decisions`, `adr`, `milestone_plan`, `dependency_map`, `scope_review`, `customer_signals`, `incident_timeline`, `risk_register`, `stakeholder_update`, `runbook_delta`, `decision_announcement`, `project_association` | `plugins/synthesis.py:13` |
| Artifact status | `draft`, `needs_review`, `accepted`, `rejected` | `artifacts.py:9` |
| Action status | `pending`, `done`, `dismissed` | `db/models.py:13` |
| Action review state | `pending`, `accepted` | `db/models.py:14` |
| **MIR profile** (Phase 7) | `balanced`, `architect`, `delivery`, `product`, `incident` | `plugin_sdk.py:65`, default `config.py:154` |
| **MIR intent** | `architecture`, `delivery`, `product`, `incident`, `comms` | `plugin_sdk.py:68` |
| Intel provider | `local`, `cloud`, `auto` | `intel/models.py:26` |
| Actuator proposal status | `proposed`, `approved`, `executed`, `rejected`, `failed` | `db/models.py:19` |
| Dictation target profile (NOT MIR) | `codex_cli`, `claude_code`, `chat`, `editor`, `browser`, `terminal_shell`, `unknown` | `target_profile.py` |

---

## Beyond the charter (surfaced by extraction)

These are real entities the desktop emits that the charter's ten don't name.
Keep/park recommendations for the mobile contract:

| Entity | Source | Recommendation |
|---|---|---|
| `Bookmark` | `meeting_session/models.py:21` | **Keep** — part of a Meeting; mobile capture marks moments |
| `IntentWindowSummary` (MIR window + scores) | `db/models.py:99` | **Keep (Phase 7)** — the MIR routing record; `profile`, `active_intents`, `intent_scores` |
| `PluginRunSummary` / `PluginRunJob` | `db/models.py:120,139` | **Park** — MIR execution telemetry; mobile may not need the full run ledger in v1 |
| `ActuatorProposalRecord` + `ActuatorProposalAuditEntry` | `db/models.py:352,384` | **Keep** — the Propose→Approve→Execute record (charter non-goal preservation; Phases 8–9 review/approve) |
| `DictationJournalRecord` | `db/models.py:415` | **Keep (lightweight)** — dictation afterlife; mobile Quick Capture/Voice Notes (Phase 9) |
| `DictationCorrectionRecord` | `db/models.py:397` | **Park** — desktop learning loop; revisit if mobile dictation learns |
| `ProjectSummary` (project KB) | `db/models.py:171` | **Park/keep-thin** — project association exists as an artifact_type; full KB likely desktop-only v1 |
| `DeviceDescriptor` | referenced `meeting_session/models.py:213` | **Park** — AIPI-Lite hardware devices; not a mobile v1 concern |
| `ActivityRecord` + activity family | `db/models.py:207+` | **Park** — the local browser-activity layer; out of mobile v1 scope |
| Operational: `MeetingSaveResult`, `IntelQueueSummary`, `IntelJobAttempt`, `ConnectorRun` | various | **Park** — runtime/telemetry, not interop domain |

---

## Cross-check against a real payload (HSM-0-01 acceptance)

The catalog was verified both ways against a **live** serialization — real
`MeetingState`, `TranscriptSegment`, `Bookmark`, `IntelSnapshot`, `ActionItem`,
and `ArtifactDraft` objects run through their actual `to_dict()` (via
`uv run python`, the real `holdspeak` package). Captured at
[`fixtures/meeting-sample.json`](./fixtures/meeting-sample.json) as the seed
conformance fixture for HSM-0-02/HSM-0-04.

Confirmed by the payload:

- Every serialized key maps to a catalog field, and every catalogued field of the
  serialized entities appears in the payload (no orphans either direction).
- `MeetingState.to_dict()` adds derived `duration` + `formatted_duration`.
- `intel_status` is emitted **nested** (`{state, detail, requested_at,
  completed_at}`).
- `mir_profile` does **not** appear — confirming it is not a Meeting field today.
- Timestamps are mixed in one payload: ISO-8601 strings (meeting/bookmark/action
  stamps) alongside float seconds (segment timing, bookmark `timestamp`) — finding
  4 is real and visible in a single document.
- `ActionItem.id` is the 12-hex content hash (e.g. `a0375768f4eb`) — finding 5.

## Open questions routed to HSM-0-03 (serialization contract)

- Mint explicit `Transcript` / `Speaker` types, or keep implicit? (finding 3)
- One wire timestamp format + relative-vs-absolute rule (finding 4).
- One ID representation on the wire (string), normalizing hash/str/int (finding 5).
- Optional `egress` scope field on actionable entities? (finding 6).
- `Artifact.structured_json` — open dict, or per-`artifact_type` sub-schemas in
  HSM-0-02? (recommendation: open dict in v1, document the known shapes).
- The two profile vocabularies must be named distinctly in the contract
  (`mir_profile` vs `target_profile`) so neither host conflates them (finding 2).

## Presence: steering + rails (HSM-26-01, Phase 87/88)

The DeskOS belt (B4) renders these ephemeral live shapes from the
desktop hub. They are the framework's **presence** sync class — read
from the documented routes, not synced as durable `ChangeSet`
primitives. Each has a schema in `schemas/` and a conformance fixture
in `fixtures/steering-and-rails-sample.json`; `validate.py` and the
desktop test `tests/unit/test_steering_contracts_fidelity.py` both
check the real hub responses against them.

| Shape | Schema | Route / source |
|---|---|---|
| `CoderSessionPeek` | `coder-session-peek.schema.json` | `GET /api/coders/{key}/peek` (Phase 87) |
| `ArmingGrant` | `arming-grant.schema.json` | `POST /api/coders/{key}/arm`, `GET .../steering/grants` (Phase 87) |
| `SteerRequest` | `steer-request.schema.json` | `POST /api/coders/{key}/steer` body (Phase 87/88) |
| `SteerGrounding` | `steer-grounding.schema.json` | the `grounding` object (Phase 83/87/88) |
| `SteerResult` | `steer-result.schema.json` | `POST /api/coders/{key}/steer` result (Phase 87) |
| `SteeringAuditEntry` | `steering-audit-entry.schema.json` | `GET /api/coders/steering/audit` (Phase 87) |
| `RailsGroundingRef` | `rails-grounding-ref.schema.json` | `grounding.rails[]` (Phase 88) |
| `RailsJournalEntry` | `rails-journal-entry.schema.json` | `GET /api/missioncontrol/rails/journal` (Phase 88) |
| `RailsRemoteEventsEnvelope` | `rails-remote-events-envelope.schema.json` | `POST /api/missioncontrol/rails/remote-events` (Phase 88) |

Consent is part of the contract: the grant pins the pane's `%N` and
counts down; the steer result's status is the full deliver vocabulary
(delivered + typed refusals, a revoking refusal disarms); every steer
is audited (hash + head, never the full text). The reach is events
only — the remote-events envelope schema rejects a file body, matching
the route's runtime refusal. So the iPad enforces the same consent the
desk does, from the shape alone.
