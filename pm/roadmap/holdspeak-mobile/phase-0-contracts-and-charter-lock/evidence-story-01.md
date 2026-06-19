# Evidence — HSM-0-01 — The entity catalog

- **Shipped:** 2026-06-18
- **Commit:** initial Phase-0 contracts bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `contracts/ENTITY-CATALOG.md` — the catalog: all ten charter Layer-1 entities
  traced to shipped `holdspeak/` source, a "Beyond the charter" inventory with
  keep/park calls, the enum vocabularies, six headline findings, and the
  real-payload cross-check section.
- `contracts/fixtures/meeting-sample.json` — the live-serialization sample the
  catalog was cross-checked against (also seeds HSM-0-02/04).

## Verification artifacts

The catalog was cross-checked **both ways** against a live serialization produced
by the real `holdspeak` package (not hand-written), via
`uv run python` over `MeetingState`/`TranscriptSegment`/`Bookmark`/
`IntelSnapshot`/`ActionItem`/`ArtifactDraft` → their actual `to_dict()`:

- Every serialized key maps to a catalogued field, and every catalogued field of
  the serialized entities appears in the payload (no orphans either direction).
- Confirmed `intel_status` serializes nested; `duration`/`formatted_duration` are
  derived-only; `mir_profile` is absent (not a Meeting field) — recorded as the
  HSM-7-03 contract-addition finding.
- `ActionItem.id` observed as the 12-hex content hash (`a0375768f4eb`).

## Acceptance criteria — re-checked

- [x] Every charter Layer-1 entity appears with a complete field list — proven by
  the catalog's "Charter Layer-1 entities" tables.
- [x] Every field cites a desktop source — `file:line`/symbol traces throughout.
- [x] Enum-valued fields list their full vocabulary — see "Enum vocabularies"
  (artifact types ×15, statuses, MIR profile/intent, provider, actuator status).
- [x] Entity relationships drawn — Meeting → Segments/Bookmarks/IntelSnapshot →
  ActionItems; Artifact tagged-union; IntelJob ↔ transcript_hash.
- [x] Entities beyond the charter's ten listed with keep/park — "Beyond the
  charter" table.

## Deviations from plan

The catalog's home is the in-repo `contracts/` tree (decided in HSM-0-03), not a
standalone package — recorded, not a deviation in intent.

## Follow-ups

Per-`artifact_type` `structured_json` sub-shapes are documented but not schema'd
(HSM-0-02 left them open; can tighten additively later).
