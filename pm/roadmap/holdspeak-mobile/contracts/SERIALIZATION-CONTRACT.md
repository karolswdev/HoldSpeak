# HoldSpeak Serialization Contract (HSM-0-03)

**Status:** in-progress (HSM-0-03). The cross-runtime rules that let Python
(desktop) and Swift (mobile) exchange the [entity catalog](./ENTITY-CATALOG.md)
without drift. Where this contract and a JSON Schema disagree, **this document is
the intent and the schema is corrected to match** (the schemas in `./schemas/`
were authored to these rules).

These rules are binding on HSM-0-02 (schemas), HSM-0-04 (fixtures), and all of
Phase 1 (the Swift `Codable` types are generated/written to satisfy them).

---

## 1. The wire format is the desktop's `to_dict()` shape

The desktop product has shipped since v0.3.0; its `to_dict()` output is the
incumbent wire format. The contract **adopts it as-is** rather than re-casing or
restructuring it, so no desktop churn is required for interop.

- **Field naming: `snake_case`.** Confirmed from live serialization
  (`started_at`, `intel_status`, `body_markdown`). The wire is snake_case.
- **Swift side maps, the wire does not.** Swift types use
  `JSONDecoder.keyDecodingStrategy = .convertFromSnakeCase` (or explicit
  `CodingKeys`) so idiomatic camelCase Swift properties bind to snake_case JSON.
  The wire never carries camelCase.

## 2. Timestamps — two deliberate representations

A single payload mixes two, and that is correct, not a defect:

- **Absolute instants → ISO-8601 UTC with a `Z` suffix.** `started_at`,
  `ended_at`, `created_at`, `requested_at`, all actuator stamps. Format:
  `2026-06-18T09:30:00Z` (UTC, `Z`-terminated). Swift: `Date` with an ISO-8601
  strategy. **Owner decision 2026-06-18 (HSM-0-05): standardize on UTC `Z`** — so
  one instant means one thing on every device, before the mobile clients
  multiply. **Normalization boundary:** the desktop currently emits bare-local
  `datetime.isoformat()` (no offset); a desktop↔mobile participant MUST normalize
  to UTC `Z` at the contract boundary (a Phase-10 sync-adapter / desktop-side
  concern). The greenfield mobile runtime emits UTC `Z` natively. The conformance
  fixture and the validator enforce the `Z` form.
- **Intra-meeting offsets → float seconds since meeting start.**
  `Segment.start_time/end_time`, `Bookmark.timestamp`,
  `ActionItem.source_timestamp`, `IntelSnapshot.timestamp`. These are durations,
  not instants; they stay numeric and are never converted to dates.

## 3. IDs are strings on the wire

Desktop mixes content-hash strings (`ActionItem.id` = `sha256(task:owner)[:12]`),
opaque strings (`MeetingState.id`), and DB autoincrement ints (telemetry rows).
**Contract rule:** every id that crosses the wire is a **string**. Entities whose
desktop id is an int (the parked telemetry rows) are out of the mobile v0 surface;
if one is ever added, its id is stringified at the boundary. Swift models id
fields as `String`.

## 4. Null vs. absent

- **Optional-and-present-as-null:** desktop emits explicit `null` for known-but-
  unset fields (`ended_at: null`, `speaker_id: null`). The schema marks these
  `["T", "null"]` and they are **required keys** (present, possibly null).
- **Optional-and-absent:** fields desktop may omit entirely (e.g. `created_at`/
  `updated_at` on a draft vs. persisted artifact) are **not required** and absent
  means "unknown", not null.
- Swift: present-null → `T?` decoded from explicit null; absent → `T?` defaulting
  to nil via `decodeIfPresent`. Decoders must not treat absent and null as
  interchangeable when the schema distinguishes them.

## 5. Enums are closed; `structured_json` is open

- The enum vocabularies in [the catalog](./ENTITY-CATALOG.md#enum-vocabularies)
  are **closed** — an unknown value fails validation (proven by `validate.py`'s
  negative case). Swift models them as `enum` with a documented decode-failure or
  an explicit `.unknown` fallback case (decision deferred to Phase 1 per-enum).
- `Artifact.structured_json` is an **open object** in v0 (the tagged-union payload
  varies by `artifact_type`). The contract documents the known shapes but does not
  schema them per-type yet; HSM-0-02 may add per-`artifact_type` sub-schemas later
  without a breaking change (additive).

## 6. The two "profile" vocabularies are named distinctly

- `mir_profile` — the **meeting** routing profile
  (`balanced/architect/delivery/product/incident`). **Phase 7 (HSM-7-03) adds this
  to the Meeting contract** — it is NOT a serialized Meeting field today (it lives
  in config; per-meeting it appears only on `IntentWindowSummary.profile`).
- `target_profile` — the **dictation** target
  (`codex_cli/claude_code/chat/editor/...`). Unrelated to meetings.

No contract field is ever just `profile`. A host that conflates them is wrong by
construction.

## 7. Transcript and Speaker (the implicit entities)

- **`Transcript`:** the contract mints a thin wrapper — `{meeting_id, segments[],
  transcript_hash}` — for sync addressing (Phase 10) and so a transcript can be
  referenced without the whole `Meeting`. It is a view over the segments, not a
  new source of truth.
- **`Speaker`:** stays the segment fields (`speaker`, `speaker_id`, `device_id`)
  plus an **optional per-meeting roster** (`speaker_id → display name`) the
  contract reserves for when diarization assigns identities. Phase 3 (HSM-3-04)
  emits the segment with the reserved slot; no standalone `Speaker` row in v0.

## 8. Egress scope (reserved, optional)

The desktop egress badge (Phase 62) is computed at the UI, not stored. The charter
wants the contract able to carry it. **Contract rule:** actionable entities
(`Artifact`, `ActionItem`, and any future proposal) may carry an **optional**
`egress` object `{scope: "local"|"local_cloud"|"cloud", label?: string}`. Absent =
"compute at the surface as desktop does". Reserved now so adding it later is
additive; not populated in v0.

## 9. Versioning

- **`contract_version`** is a string, starts at **`"0.1.0"`** (semver). It is
  **independent of** the desktop DB `SCHEMA_VERSION` and the mobile SQLite
  `SCHEMA_VERSION` (Phase 4) — a contract change never forces a DB migration with
  no storage change, and vice-versa.
- **Where it lives:** not on every entity. It is a constant in the
  `holdspeak-contracts` package and is carried in the **sync envelope** (Phase 10),
  so a receiver knows which contract minted a change-set.
- **Compatibility policy:** additive-only within a major. **Unknown newer fields
  are ignored on decode** (forward-compatible) — Swift `Codable` ignores unknown
  keys by default; Python decoders must not hard-fail on an unexpected key.
  Removing or retyping a field is a major bump.

## 10. The `holdspeak-contracts` package

- **Layout (decided):**
  ```
  contracts/
    ENTITY-CATALOG.md          # HSM-0-01
    SERIALIZATION-CONTRACT.md  # this file
    schemas/*.schema.json      # HSM-0-02 (the canonical wire schemas)
    fixtures/*.json            # HSM-0-04 (golden conformance payloads)
    validate.py                # the cross-runtime validator
  ```
- **Home (decided, with trigger):** the canonical schemas + contract live as a
  **versioned `contracts/` tree in this repo** for now (under the roadmap project
  while planning; promoted to a stable repo path — e.g. a top-level `contracts/`
  or the mobile source root — when Phase 1 needs to vendor it into the Swift
  package). **Trigger to extract to a standalone repo:** a second independent
  consumer (beyond desktop + this mobile app) needs to depend on it without
  pulling this repo. Until then, one repo, one source of truth, no submodule
  overhead.

---

## Worked example — `Meeting`, end to end (acceptance criterion)

Catalog field → schema → contract rule → the Swift type Phase 1 will write:

| Wire (snake_case JSON) | Schema | Contract rule | Predicted Swift |
|---|---|---|---|
| `"id": "mtg_001"` | string, required | §3 string id | `let id: String` |
| `"started_at": "2026-06-18T09:00:00"` | string/date-time | §2 ISO instant | `let startedAt: Date` (ISO strategy) |
| `"ended_at": null` | `[string,null]`, required | §4 present-null | `let endedAt: Date?` (from explicit null) |
| `"tags": ["architecture"]` | array<string> | — | `let tags: [String]` |
| `"segments": [ {...} ]` | `$ref` segment | — | `let segments: [Segment]` |
| `"intel_status": {"state": "ready", ...}` | nested object | desktop shape (§1) | `let intelStatus: IntelStatus` (nested struct) |
| `"duration": 1800.0` | number | derived, present | `let duration: Double` |
| (`mir_profile` absent) | — | §6 added by HSM-7-03 | `var mirProfile: MIRProfile?` (Phase 7) |

A reader with the catalog + this contract can predict each Swift declaration with
no ambiguity — which is the HSM-0-03 acceptance bar.

---

## §11 — Sync envelope (HSM-10-01; brought current HSM-23-04)

Cross-device sync moves the **contract entities themselves**, never a parallel sync
schema. The sync metadata a transport needs rides in a thin additive envelope; the
entity structs are unchanged (no `last_modified`/`deleted` field bolted onto each
entity — that was the escalation the story flagged, resolved this way):

- `sync_metadata`: `{ id (string), kind (see the kind set below), last_modified
  (ISO-8601 UTC Z, §2), deleted (bool) }`. `deleted=true` is a **tombstone** — a
  propagated delete whose `value` is `null` (never a payload; the §12 rule).
- `synced<T>`: `{ meta: sync_metadata, value: T|null }`; `value` is the unmodified
  contract entity, and is `null` exactly when `meta.deleted`.
- `change_set` — eleven buckets, one per kind (all optional on the wire; decoders
  tolerate absent buckets):
  `{ meetings, artifacts, notes, kbs, recipes, chains, workflows, profiles,
  directories, directory_memberships, models }`, each `synced<T>[]`. (The recipes
  bucket wore the word "agents" before the Phase-17 owner-ratified rename; the
  shipping wire is `recipes`/`recipe`.)
- The `kind` enum matches the buckets one-to-one: `meeting`, `artifact`, `note`,
  `kb`, `recipe`, `chain`, `workflow`, `profile`, `directory`,
  `directory_membership`, `model`. A `directory_membership` record's synced id is
  its `primitive_id` (the filing-map key); its value carries the `directory_id`
  edge. Actions are not a top-level store entity (they live inside an Action-Items
  artifact), so they do not sync as a kind.
- `model` is a **manifest**, never a binary (HSM-16-08): `{ id ("<node>:<file>"),
  node, name, capabilities[] }` — availability only. The schema's
  `additionalProperties: false` makes any path/url/bytes-shaped field a validation
  failure, and the hub's pull additionally emits its OWN model as a live virtual
  row (`desktop:intel`, computed from config, never stored).

History: HSM-10-01 shipped the envelope with `{meetings, artifacts}` only; the
Primitive Framework (Phases 72–77) grew it to ten kinds, HSM-23-04
back-updated this section to the shipping wire, and HSM-16-08 added the
eleventh kind (`model` manifests). The envelope's JSON Schema is
`schemas/changeset.schema.json` (`additionalProperties: false`, per-bucket `kind`
const, tombstone ⇒ `value: null`); every kind's push→pull round-trip + LWW +
tombstone behavior is locked per-primitive in
`tests/unit/test_web_routes_sync_primitives.py` +
`tests/integration/test_primitive_framework_sync.py`. Enforcement is §12.

## §12 — Enforcement (HS-72-01): the contract is machine-checked

The rules above stopped being prose on 2026-07-02. Every sync kind now has a
JSON Schema in `schemas/` (`note`, `kb`, `agent`, `chain`, `workflow`,
`directory`, `directory-membership`, `profile`, plus the `changeset` envelope
alongside the existing meeting-domain schemas), each tagged `x-sync-kind`, and
three guards consume them:

- **Hub (pytest, CI):** `tests/unit/test_primitive_contract.py` validates a
  REAL `/api/sync/pull` body (one row per kind + a tombstone) against the
  schemas + the envelope, pins the hub's emission superset, and locks the kind
  set three ways — `sync.py SYNC_KINDS` == the schemas' `x-sync-kind` set ==
  Swift `SyncKind` raw values (parsed from `Sync.swift`). It also asserts the
  web's `primitives.ts` desk interfaces never *require* a field the contract
  lacks.
- **Swift (`swift test`):** `ContractsTests/PrimitiveContractFixtureTests`
  decodes the shared golden fixture (`fixtures/primitives-sample.json` — the
  hub's canonical emissions) through `HoldSpeakContracts` and round-trips it.
- **Standalone:** `validate.py` covers the same fixture + the
  key-never-syncs negative (a `profile` carrying `api_key` must fail).

Locked findings from the first enforcement pass: a tombstone carries NO
payload (the hub was emitting full values on tombstones — fixed); the hub
emits no `updated_at` for kb/agent/chain/workflow/directory/membership/profile
(Swift decodes tolerantly, defaulting to `created_at`; `meta.last_modified`
stays the LWW key); `Agent.manual_context`/`use_zone_context` were iPad-authored
and **lossy through hub sync** — **fixed by Phase 77** (db v7 persists both, the
push route merges them, pull re-emits them; byte-faithful round-trip locked in
`tests/unit/test_agent_pinned_context.py`);
`RuntimeProfile.baseURL` could never decode off the wire under
`convertFromSnakeCase` (fixed with an explicit coding key).

## Decisions locked here (carried to the phase status)

1. Wire = desktop `to_dict()` snake_case; Swift maps via key strategy (§1).
2. ISO-8601 **UTC `Z`** strings for instants (owner-decided 2026-06-18), float
   seconds for intra-meeting offsets; desktop bare-local normalizes at the
   boundary (§2).
3. String ids on the wire (§3).
4. Required-present-null vs. not-required-absent are distinct (§4).
5. Closed enums; open `structured_json` (§5).
6. `mir_profile` vs `target_profile` named distinctly; never bare `profile` (§6).
7. Thin `Transcript` wrapper; `Speaker` = segment fields + optional roster (§7).
8. Optional reserved `egress` on actionable entities (§8).
9. `contract_version = "0.1.0"`, independent of DB version, additive-only,
   ignore-unknown-on-decode, carried in the sync envelope (§9).
10. `holdspeak-contracts` is a versioned in-repo `contracts/` tree; extract to a
    standalone repo only when a second independent consumer appears (§10).

## Owner confirmations (HSM-0-05, 2026-06-18)

- **Timestamps:** standardize on UTC `Z` (§2). Resolved — folded into the contract.
- **Quality Gates 3–7:** confirmed as-reconstructed (see `../CHARTER.md`).

## §N. Presence: read, never synced (HSM-26-01)

The steering + rails shapes (the peek, the grant, the steer, the audit
entry, the rails ref, the journal entry, the remote-events envelope)
are the framework's **presence** class: ephemeral live state a surface
READS from the documented routes, not durable primitives that flow
through the `ChangeSet` sync path. There is no last-write-wins, no
tombstone, no bidirectional merge for these — the desktop hub is the
one authority, and a surface polls the route (poll-only-while-open,
the web desk's posture) or reads on demand. They still obey the wire
rules: snake_case on the wire, camelCase native, instants UTC `Z`.
Their schemas live beside the durable ones in `schemas/`; only their
sync class differs.
