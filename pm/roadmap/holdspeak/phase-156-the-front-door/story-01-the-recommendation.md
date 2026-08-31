# HS-156-01 - The recommendation: packs A/B/C from what the desk already knows

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-156-02, HS-156-03, HS-156-05
- **Owner:** unassigned

## Problem

The desk knows the hardware, the catalog, the legacy config, and the
LAN servers — and still greets the owner with a blank 24-row list. The
owner ruled it: "Let me download it for you, a recommended pack based
on your hardware…, and maybe A/B/C options" (settled design D1).

## Scope

- **In:** a pure server-side recommender (`holdspeak/services/
  front_door_service.py` or similar): inputs = the existing hardware
  snapshot, catalog, downloaded/connected state, the legacy config's
  named models, and explicitly-known OpenAI-compatible endpoints
  (probed for reachability; NO network-wide scan). Output = up to
  three complete packs (Light / Balanced / Full), each covering ALL
  seven job groups + speech + TTS with plain one-line-per-job wording,
  download sizes, and a machine-readable apply plan. Detected assets
  (a LAN server, an existing GGUF) become pack ingredients with named
  provenance. `GET /api/front-door/recommendation` returns the packs;
  API-surface manifest updated.
- **Out:** applying a pack (02), any UI (03), new model catalog rows.

## Acceptance criteria

- [ ] Fixtures pin the truth table: a 16 GB Apple-Silicon machine, a 32 GB one, and a machine with a reachable LAN endpoint + legacy gguf each yield the expected packs (models, sizes, per-group wiring) — exact-match tests.
- [ ] A pack is always COMPLETE (all seven groups + speech resolved) or not offered; the Balanced pack is marked recommended.
- [ ] Unreachable LAN endpoint → excluded with a reason in the payload; no scan beyond explicitly-known endpoints (a test asserts no other hosts are probed).
- [ ] The cloud path never appears in a pack unless a credential already exists (recorded law).

## Test plan

- **Unit:** `tests/unit/test_front_door_recommendation.py` (fixture truth tables, completeness, probe boundaries).
- **Integration:** route test via the real app (the 153/154 pattern).
- **Manual / device:** story 05 stopwatch walk.

## Notes / open questions

- Reuse `inspect_hardware` and the catalog reads — the recommender adds no new facts, only judgment over existing ones.
