# HSM-18-07 — The Desk-Era rider: run-born artifacts land on the iPad desk + the route-surface lock

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** todo — the Desk-Era catch-up rider (owner-scoped into this phase, 2026-07-03).
- **Depends on:** nothing in this phase (parallel-startable); hub schema v6 (run-born
  artifacts, Phase 74) and the Phase-72 route rename + `docs/api-surface.json` manifest,
  both already on `main`.
- **Unblocks:** the iPad desk staying honest against the Desk-Era hub; every future hub
  route rename breaking loudly instead of silently.
- **Owner:** unassigned

## Problem

The web/hub Desk Era (Phases 72–78, 2026-07-02/03) moved two contracts out from under the
iPad:

1. **Run-born artifacts exist and the iPad cannot say so.** Phase 74 made runs persist as
   real artifacts (hub schema v6: `origin='run'`, lineage, DB `meeting_id` NULL serialized
   as `""` on every wire — a rule written *for* the iPad's non-optional decode). The web
   desk materializes a finished run's results on the stage. On the iPad: the cross-surface
   contract schema (`pm/roadmap/holdspeak-mobile/contracts/schemas/artifact.schema.json`)
   carries **no `origin` field**, neither Swift read model
   (`Contracts/Models.swift::Artifact`, `Contracts/MeetingArtifact.swift`) decodes it, and
   a run-born artifact syncing in is an orphan with an empty `meetingId` — no lineage, no
   arrival, indistinguishable from bad data.
2. **The Phase-72 route rename is honored but unlocked.** `HTTPDesktopClient` moved to
   `/api/coders/*` + `/api/desk/actuators/*` (zero `api/companion` literals remain), but
   nothing machine-checks the Swift client against the hub's declared API surface
   (`docs/api-surface.json`). The rename shipped safely this time because one session did
   both sides; the next one won't be.

## The design

1. **`origin` joins the artifact contract.** Add `origin` (`"meeting" | "run"`) to
   `artifact.schema.json` and both Swift read models — decode-tolerant (absent ⇒
   `"meeting"`, unknown string never fails the decode, matching the `MeetingArtifact`
   convention). The `meeting_id ""` wire rule stays exactly as written.
2. **A run-born artifact materializes on the iPad desk.** When one arrives (sync or read),
   it lands on the stage with the arrival beat — the same grammar as the web desk's
   Phase-74 materialization — and its pull-out shows the run lineage the same way the
   meeting drawer groups derivatives by provenance. Filed stays filed (the filed-object
   grammar is the iPad's own contract; do not re-litigate it).
3. **The route-surface lock.** A hub-side guard test that parses the path literals out of
   `HTTPDesktopClient.swift` and asserts every one exists in `docs/api-surface.json` —
   the `test_primitive_contract.py` Swift-parsing pattern, pointed at routes. This is the
   durable form of "verify the renamed routes": it locks Phase 72's rename and every
   future one.

## Scope

- **In:** the schema + both Swift models; the desk materialization beat + run lineage in
  the pull-out; the route-surface guard test.
- **Out:** the owner's Phase-72 device walk (legacy `@AppStorage` decode in anger,
  coder-board and desk-relay taps — owner-gated, tracked in the Desk-Era handover);
  starting runs *from* the iPad (the agent/chain run path already exists); intel token
  streaming (the hub honestly emits running→ready only).

## Test plan

- Schema validator round-trips an `origin: "run"` artifact on all validating surfaces;
  an origin-less payload still validates (back-compat).
- Swift decode tests: `origin` present/absent/unknown; `meetingId == ""` accepted.
- The route-surface guard: red against a fabricated stale path, green on `main`.
- Simulator screenshot: a run-born artifact materialized on the desk with its lineage
  pull-out open.
