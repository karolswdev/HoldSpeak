# Phase 10 — Sync

**Status:** in-progress (HSM-10-01 + HSM-10-02 + **HSM-10-03 done** — object model,
engine, transport (both sides), and the conflict policy (LWW + non-destructive
concurrent-divergence + tombstone-no-resurrect + idempotent, both-ends validated)
are all host-proven; only the continuity gate (HSM-10-04, live cross-device) remains,
and it needs the iPad). Track K of the Council
Implementation Charter. The `ISyncProvider` (Layer 3): cross-device continuity so
a meeting captured on the phone shows up on the desktop, and edits round-trip —
over the user's own network (desktop / homelab / Tailscale), local-first and
never destructive.

**Last updated:** 2026-06-19 (**HSM-10-01 done — the sync object model + engine**.
The sync set is the Phase-0 entities themselves, carried in a contract-layer
envelope (`ChangeSet` of `Synced<T>`; payload = the unmodified entity, `nil` ⇔
tombstone) — no parallel schema, no drift; recorded in SERIALIZATION-CONTRACT §11.
`ISyncProvider` is now a `push`/`pull` seam; `ISyncStore` adds modified-time +
soft-delete tombstones to the Phase-4 store (SQLite **schema v2**, guarded
migration); the RuntimeCore `SyncEngine` does `snapshot`/`apply` (schema-validated
before any write) / `sync(local:via:)`. `swift test` **55/55** incl. 6 sync tests
(round-trip, JSON-wire round-trip, tombstone propagation, idempotent apply,
malformed-wire rejection) — and the Phase-4 storage tests still pass through the
migration. The envelope's JSON Schema + the Python-side mirror land with HSM-10-02
(transport). Earlier: scaffolded — stories HSM-10-01..04 stubbed from charter Track
K.)

## Goal

Build the sync layer behind the `ISyncProvider` abstraction: move the Phase-0
contract objects (Meetings, Actions, Artifacts) between the mobile runtime and the
desktop/homelab over a Tailscale network, with an idempotent round-trip and a
conflict policy that never loses or silently overwrites data. The phase passes on
cross-device continuity — the Track K gate / program Gate 6. Sync is additive and
local-first; it never acts autonomously.

## Scope

- **In:** the `ISyncProvider` abstraction + the sync object model on the Phase-0
  contracts (HSM-10-01); transport to Desktop / Homelab / Tailscale targets
  (HSM-10-02); conflict/merge policy + idempotent round-trip validated against the
  Phase-0 fixtures (HSM-10-03); the cross-device continuity gate closeout
  (HSM-10-04).
- **Out:** a hosted cloud sync service (this is the user's own network — desktop /
  homelab / Tailscale, not a HoldSpeak server). Real-time collaborative editing.
  The host UIs (Phases 8–9 — sync surfaces through them but the screens are
  theirs). Auth/identity beyond what Tailscale provides. Hardening (Phase 11).

## Exit criteria (evidence required)

- [ ] The `ISyncProvider` abstraction exists and the sync object model is the
      Phase-0 contracts (Meetings/Actions/Artifacts) — the Runtime Core depends on
      the interface, not a transport (HSM-10-01).
- [ ] Sync works over the three targets (desktop, homelab, Tailscale network) for
      the object set (HSM-10-02).
- [ ] Round-trip is idempotent (syncing twice changes nothing) and the conflict
      policy is defined and non-destructive; validated against the Phase-0
      conformance fixtures (HSM-10-03).
- [ ] **Track K gate / Gate 6 — cross-device continuity:** capture on one device,
      it appears on another; an edit on one round-trips to the other; proven on
      real devices over a real network (HSM-10-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-10-01 | Sync provider + object model | done | [story-01](./story-01-sync-provider-object-model.md) | [evidence-01](./evidence-story-01.md) |
| HSM-10-02 | Transport targets | done (both sides) | [story-02](./story-02-transport-targets.md) | [evidence-02](./evidence-story-02.md) |
| HSM-10-03 | Conflict + round-trip | done | [story-03](./story-03-conflict-and-roundtrip.md) | [evidence-03](./evidence-story-03.md) |
| HSM-10-04 | Continuity closeout (Gate 6) | in-progress (SyncCoordinator orchestration host-proven; live device walkthrough pending) | [story-04](./story-04-continuity-closeout.md) | in story |

## Where we are

**HSM-10-01 is done.** The object model + engine are host-proven on the Phase-0
contracts + the Phase-4 store, reusing the Phase-0 conformance fixture as the
round-trip test bed. The sync set is the entities themselves in a `ChangeSet` of
`Synced<T>` envelopes; the `SyncEngine` produces a snapshot from the store and
applies one back (schema-validated), driven through the `ISyncProvider` push/pull
seam — so the Runtime Core depends on the interface, never a transport. The store
gained modified-time + tombstones (schema v2). **Next: HSM-10-02 (transport to the
user's own desktop/homelab/Tailscale targets, incl. the new Python-side sync API +
the envelope's JSON Schema), then HSM-10-03 (conflict/idempotency) and HSM-10-04
(the continuity gate on real devices).** The remaining stories are where sync
touches real hardware/network; HSM-10-01 is fully host-proven.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Conflict handling silently overwrites or loses an edit (the unforgivable sync bug) | high | Define a non-destructive conflict policy in HSM-10-03 (last-writer-wins is not enough for meetings — prefer merge/keep-both for divergent edits); test divergent-edit cases explicitly | A test shows a concurrent edit on two devices loses one side — halt; sync that loses data is worse than no sync |
| Round-trip isn't idempotent — re-syncing duplicates or mutates rows | high | Idempotency is an HSM-10-03 acceptance criterion (sync twice → no change), tested against the Phase-0 fixtures | Re-sync changes the data set — fix before the gate |
| The mobile↔desktop contract drifts and sync corrupts on the wire | medium | Sync payloads ARE the Phase-0 contract objects; validate every payload against the schemas on both ends (reuse HSM-0-04 fixtures) | A synced object fails Phase-0 schema validation on arrival — the runtimes have drifted; reconcile the contract before shipping sync |
| Tailscale/network availability assumed; sync blocks the app when offline | medium | Local-first: the app fully works offline; sync is opportunistic and additive, never on the capture path | Capture or review stalls because sync can't reach a peer — decouple; sync is never in the foreground path |

## Decisions made (this phase)

- 2026-06-18 — Sync is over the user's own network (desktop / homelab / Tailscale),
  not a hosted HoldSpeak cloud service; sync payloads are the Phase-0 contract
  objects validated on both ends — charter Track K + local-first principle.

## Decisions deferred

- Conflict resolution strategy (last-writer-wins vs. field-merge vs. keep-both for
  divergent meeting edits) — trigger: HSM-10-03 — default: non-destructive
  keep-both/merge for divergent edits; LWW only for trivially-last-write fields.
- Transport mechanism (direct device↔desktop HTTP over Tailscale vs. a homelab
  rendezvous) — trigger: HSM-10-02 — default: direct over the Tailscale network to
  the desktop/homelab endpoint; no third-party relay.
- Whether the desktop product needs a sync-receiver story of its own (this roadmap
  is mobile; the desktop side may need work) — trigger: HSM-10-02 — default:
  flag desktop-side receiver work as a `holdspeak` roadmap item if absent.
