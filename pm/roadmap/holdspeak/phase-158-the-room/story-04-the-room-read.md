# HS-158-04 - The room read: one coherent, honest, bounded projection

- **Project:** holdspeak
- **Phase:** 158
- **Status:** backlog
- **Depends on:** HS-158-02
- **Unblocks:** HS-158-05
- **Owner:** unassigned

## Problem

The Web surface opens a Project with five parallel requests
(ProjectMemoryCore.tsx:384-390). SRS §6.2 replaces that with
`GET /api/projects/{project_id}/room`: one revision-stamped
projection for the first useful render — header/outcome/posture/
review state, focus records, coverage summary, latest update, steward
summary, per-section status. In P1 most domains don't exist yet;
Art VI demands they be honestly absent, not faked.

## Scope

- **In:** `GET /api/projects/{project_id}/room` via a service-level
  `room(principal, project_id)` composition: `project` orientation
  (identity + §5.1 fields + revision), `items` focus block (bounded
  top-N by severity/due, deterministic order), `meetings`/`resources`
  summaries (counts + latest — reusing existing reads), `changes`
  (recent, bounded), and EXPLICIT absent-section markers for
  `review`, `sources`, `updates`, `steward` (named honestly — the
  exact vocabulary recorded in CONTRACTS-P0.md as an amendment).
  Per-section error isolation: one failing sub-read degrades its
  section, not the response (NFR-003). Bounded + indexed +
  deterministically ordered (DB-005); response carries `revision`
  and `observed_at`.
- **Out:** any P2+ section content, caching layers, Web changes (05).

## Acceptance criteria

- [ ] One request returns everything 05's first render needs; the legacy detail routes remain untouched (API-006).
- [ ] Absent domains are explicit absent-markers — grep-proof that no empty-faked review/steward/update payloads exist (Art VI; NFR-006).
- [ ] A failing sub-read (fault-injected) degrades only its section with a typed per-section error.
- [ ] NFR-001 sanity: with 500 linked records the projection stays bounded (top-N focus, capped lists) — a test asserts the caps.
- [ ] Response stamped with `revision`; two reads with no writes in between are byte-identical (determinism).

## Test plan

- **Unit:** `tests/unit/test_project_room_read.py` (composition, caps, ordering, absent markers, section fault isolation, revision stamping).
- **Integration:** the route through the real app incl. 404 + non-owner.

## Notes / open questions

- CONTRACTS-P0.md gains the room-section state vocabulary (absent | ok | degraded) as a §-amendment in the same commit — the suite rule (names agreed before use).
