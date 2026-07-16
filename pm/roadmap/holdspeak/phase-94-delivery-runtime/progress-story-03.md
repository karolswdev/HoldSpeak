# HS-94-03 progress record — Authenticated node link, capabilities, liveness, reconnect

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped scope (the second physical
machine over Tailscale is BACKLOG candidate Y; the localhost two-process
proof and injected-clock suites carry the behavioral contract).

## What shipped

- `holdspeak/delivery/node_link.py`: per-node pairing tokens
  (`~/.holdspeak/node_auth_tokens.json`, 0600, rotate/revoke without repo
  edits, refusals name the node), hub liveness derived from injected
  monotonic clocks (live <15s, stale <30s, offline after, last-seen retained
  forever), metadata-only event ingestion behind a strict allow-list, cursor
  authority rules that make duplicates impossible after a node loses its
  file, and an embedded LocalNodeAdapter running the identical code path.
- `holdspeak/web/routes/delivery_node.py`: hello/heartbeat/disconnect/
  commands(claim envelope)/nodes projection; the hub web token is checked
  first so a browser credential can never authenticate as a node.
- `holdspeak/commands/node_serve.py` + the `holdspeak node {serve|token}`
  CLI: outbound-only worker (hello, 5s heartbeats, persisted cursor, bounded
  backoff + jitter, token via env never argv).
- Transport decision: outbound long-poll on the proven mesh-worker pattern
  rather than raw WebSocket — every binding behavior (node initiates,
  liveness, cursor resume, capability scoping, token custody) holds, and
  the claim envelope is §8-shaped so a streaming upgrade replaces only the
  poll leg.

## Verification

66 tests green: token distinctness/rotation/revocation by name, capability
mismatch disabling commands while observation continues, liveness
transitions with injected clocks, cursor resume without duplicate or gap,
content-smuggling refusals, a five-scenario local/remote parity suite, and
a REAL two-process proof (subprocess node against a real uvicorn hub:
live → SIGKILL → stale → offline with last-seen → restart → contiguous
cursor resume, seqs 1..5). Combined delivery/node/mesh lane green; the
legacy steering relay is untouched and surfaces as `legacy-direct`.
Captured at close in [evidence-story-03](./evidence-story-03.md).
