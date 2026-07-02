# Evidence — HS-72-01 — The primitive contract, machine-checked

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## Files touched

- `pm/roadmap/holdspeak-mobile/contracts/schemas/` — **8 new schemas**
  (`note`, `kb`, `agent`, `chain`, `workflow`, `directory`,
  `directory-membership`, `profile`) + `changeset.schema.json` (the sync
  envelope); `meeting.schema.json` / `artifact.schema.json` gained the
  `x-sync-kind` tag.
- `pm/roadmap/holdspeak-mobile/contracts/fixtures/primitives-sample.json` —
  the shared golden fixture: one canonical hub emission per kind + a
  ChangeSet envelope carrying a live record and a tombstone.
- `pm/roadmap/holdspeak-mobile/contracts/validate.py` — validates every kind
  + the envelope + the key-never-syncs negative (a profile carrying
  `api_key` must fail).
- `tests/unit/test_primitive_contract.py` — the CI drift guard (real
  `/api/sync/pull` over a tmp Database validated against the schemas; the
  three-way kind-set lock hub==schemas==Swift; the web `primitives.ts`
  no-invented-fields check).
- `apple/Tests/ContractsTests/PrimitiveContractFixtureTests.swift` — decodes
  the golden fixture through `HoldSpeakContracts` + round-trips every kind +
  envelope/tombstone assertions.
- `apple/Sources/Contracts/Primitives.swift` — tolerant decoders (see
  findings).
- `holdspeak/web/routes/sync.py` — the tombstone fix (see findings).
- `pyproject.toml` — `jsonschema>=4.21` added to the `test` extra + `dev`
  group.
- `pm/roadmap/holdspeak-mobile/contracts/SERIALIZATION-CONTRACT.md` — new
  §12 records the enforcement mechanism + locked findings.

## Findings (real drift caught by the first enforcement pass)

1. **The hub violated its own tombstone rule.** `Sync.swift` documents
   "value is nil exactly when meta.deleted"; the hub's `_primitive_record`
   emitted full values on tombstones. Fixed (one line); all pre-existing
   sync tests still green.
2. **The hub emits no `updated_at`** for kb/agent/chain/workflow/directory/
   membership/profile, while the Swift types required it — a hub-pulled KB
   could never have decoded as `Synced<KB>`. Swift now decodes tolerantly
   (`updatedAt` defaults to `createdAt`; `meta.last_modified` stays the LWW
   key), matching `ChangeSet`'s documented tolerant-decode philosophy.
3. **`Agent.manual_context` / `use_zone_context` are lossy through hub
   sync** — the iPad encodes them, the hub neither persists nor re-emits
   them. Locked in the agent schema as optional-and-lossy; the fix (two
   hub columns) is a follow-up, not silently absorbed here.
4. **`RuntimeProfile.baseURL` could never decode off the wire**: under
   `convertFromSnakeCase`, wire `base_url` becomes lookup key `baseUrl`,
   which never matched the synthesized `baseURL` coding key. Fixed with an
   explicit `case baseURL = "baseUrl"`; asserted by the fixture test.
5. Documented type drift (not fixed here, HSM-22 territory): web
   `primitives.ts` types `graphJson` as `string`; the hub emits an object.
   Recorded in `workflow.schema.json`.

## Verification artifacts

- `contracts/validate.py` (uv run --with jsonschema): **20/20 PASS** incl.
  all 8 kinds, the envelope with tombstone, the `api_key` negative, UTC-Z,
  and fixture canonicality.
- `uv run pytest -q tests/unit/test_primitive_contract.py
  tests/unit/test_web_routes_sync_primitives.py tests/unit/test_web_routes_sync.py`
  → **21 passed**.
- `swift test --filter PrimitiveContractFixtureTests` → **5/5 passed**;
  full `swift test` → **394 tests, 0 failures (8 skipped)**.
- Full python suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3051 passed, 38 skipped, 0 failures**.
- **Deliberate-drift red proofs (both ways), reverted:**
  - Removed `"note"` from `SYNC_KINDS` →
    `test_schemas_cover_exactly_sync_kinds` AND
    `test_swift_sync_kind_matches_hub` failed naming the missing kind.
  - Renamed `body_markdown` → `body_md` in `NoteRecord.to_dict` →
    `test_every_kind_value_validates_against_its_schema` failed:
    `"Additional properties are not allowed ('body_md' was unexpected)"` +
    `"'body_markdown' is a required property"`.

## Acceptance criteria — re-checked

- [x] Schemas for all 10 sync kinds + the ChangeSet envelope exist and are
      consumed by all three guards.
- [x] All three surfaces validate in their own suites (pytest / swift test /
      the web shape check inside pytest).
- [x] The `SYNC_KINDS` lockstep comment is replaced by a mechanical
      three-way test.
- [x] A deliberate one-surface drift fails the guard (proven both ways,
      outputs above).

## Deviations from plan

- The web check runs **inside pytest** (parsing `primitives.ts` interfaces
  and cross-checking against the schemas) instead of a separate node script
  wired into `npm run build`. Same machine-enforcement, zero new web
  infrastructure; the TS shapes are in-app view shapes, so the honest check
  is "web never *requires* a field the contract lacks" with one documented
  exception (`Directory.memberIds`, composed from membership edges).
- Schema `required` = what every surface must send (data + `created_at`);
  the hub's richer emission superset (`updated_at`/`last_modified`/`deleted`
  in values) is pinned by the pytest, not the schemas — so an iPad push
  (which omits sync plumbing inside `value`) validates against the same
  schemas.

## Follow-ups

- Persist `agent.manual_context` + `use_zone_context` on the hub (ends the
  documented lossy sync) — schema flip from "lossy" comment to required is
  the closing move.
- `graphJson` string-vs-object on the web — owned by HSM-22 (the graph
  bridge).
- HS-72-02 (the API-surface manifest) builds on this story's pattern.
