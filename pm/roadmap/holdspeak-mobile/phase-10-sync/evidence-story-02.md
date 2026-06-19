# Evidence — HSM-10-02 — Transport targets

- **Shipped:** 2026-06-19 (two PRs: PR-A Swift transport, PR-B Python receiver)
- **Owner:** unassigned

## What shipped — both sides of the wire

### Mobile (Swift, PR-A — merged #75)
- `apple/Sources/Providers/Sync/HTTPSyncProvider.swift` — `ISyncProvider` over HTTP
  (`push` → `POST /api/sync/push`, `pull` → `GET /api/sync/pull`; URLSession,
  Foundation; optional bearer; direct to the peer, no relay; honest
  `egressLabel` "local + LAN → host").
- `apple/Sources/Providers/Sync/SyncQueue.swift` — disk-backed FIFO;
  `flush(through:)` drains to a reachable peer and **leaves the queue intact +
  never throws when the peer is down** (offline tolerated; sync off the
  capture/review path).

### Desktop (Python, PR-B)
- `holdspeak/web/routes/sync.py` — `build_sync_router`: `GET /api/sync/pull`
  serializes the desktop's meetings (`MeetingState.to_dict`) + artifacts
  (`ArtifactSummary`) into the contract change-set envelope; `POST /api/sync/push`
  receives a change-set into a durable inbox (`<db_dir>/sync_inbox/`, plain JSON —
  no new DB schema). Mounted in `web_server.py`.

The wire is snake_case both ways (SERIALIZATION-CONTRACT §11), so the Swift coder
and the Python routes interoperate by shape.

## Verification
- Swift: `swift test` **77/77** (6 opt-in skips) — 8 transport tests (push shape,
  pull decode, non-2xx, egress, FIFO, drain, offline-keep, partial-resume).
- Python: `uv run pytest tests/unit/test_web_routes_sync.py` → **3 passed**
  (pull serializes meetings+artifacts into the envelope; push writes the change-set
  to the inbox + returns counts; non-change-set → 422). Route preflight + core
  route tests green with the new router mounted (no import cycle).

## Acceptance criteria — re-checked
- [x] Change-sets push and pull between the phone and a desktop/homelab endpoint —
      `HTTPSyncProvider` ⇄ the desktop sync routes; each side host-tested. The live
      phone↔desktop-over-Tailscale run is the device confirmation (rides with
      HSM-10-04 + the iPad unlock).
- [x] Offline tolerated: `SyncQueue.flush` keeps the queue + never throws when the
      peer is unreachable; the app is unaffected.
- [x] One implementation of `ISyncProvider`; swapping it would not touch the Runtime Core.
- [x] Sync egress represented honestly (`egressLabel` "local + LAN → host"); badge
      wiring is the host UI's (Phases 8–9).

## Deviations / follow-ups
- The desktop **receives** pushed change-sets into a durable inbox; **merging them
  into the live store with conflict resolution is HSM-10-03**. Pull is read-only.
- Pull's `last_modified` for meetings is `started_at` (transport-grade);
  conflict-grade `updated_at` semantics are HSM-10-03. Artifacts already carry `updated_at`.
