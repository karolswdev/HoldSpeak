# HS-156-01 - The recommendation: packs A/B/C from what the desk already knows

- **Project:** holdspeak
- **Phase:** 156
- **Status:** in-progress
- **Depends on:** -
- **Unblocks:** HS-156-02, HS-156-04, HS-156-06
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

## What shipped

- `holdspeak/services/front_door_service.py` -- pure recommender:
  `recommend(hardware, catalog_entries, known_endpoints, ...)` returns
  `{packs, facts}`. Up to three packs (Light / Balanced / Full), each
  COMPLETE (all seven assignment groups + speech + TTS) or not offered.
  Balanced marked recommended. Detected assets (reachable endpoints,
  legacy GGUF) become pack ingredients with provenance labels. No
  network-wide scan (only known endpoints probed). Cloud never appears
  without an existing credential.

- `holdspeak/web/routes/front_door.py` --
  `GET /api/front-door/recommendation` gathers hardware, catalog,
  profiles (endpoints), legacy config, and runtime availability from
  the desk's existing services, then calls the pure recommender.
  Owner-only (403 for non-owner). Registered in
  `web/routes/__init__.py` and `web_server.py`.

- `docs/api-surface.json` regenerated (565 routes, new route present).

- `tests/unit/test_front_door_recommendation.py` -- 38 tests:
  - Test16GBAppleSiliconNoEndpoints (12 tests): truth table for 16GB
    Apple Silicon with no endpoints. Light uses 0.8B preset, Balanced
    and Full use 4B preset. Whisper: base/small/small. TTS in all.
  - Test32GBAppleSilicon (4 tests): bigger Balanced/Full; Full whisper
    is medium.
  - TestEndpointAndLegacyGGUF (5 tests): reachable endpoint becomes
    pack ingredient with provenance; unreachable excluded with reason,
    falls back to legacy GGUF.
  - TestCompletenessLaw (3 tests): no runtime + no endpoints = zero
    packs; every offered pack covers all seven groups + speech + TTS.
  - TestProbeBoundary (3 tests): spy proves only known endpoints are
    probed; reachable/unreachable pair verified.
  - TestNoCredentialCloudExclusion (2 tests): no cloud entries without
    credential.
  - TestHumanSize (4 tests): size formatting utility.
  - TestFrontDoorRoute (3 tests): integration route test via real
    FastAPI app with isolated DB. Owner gets packs; non-owner gets 403.
  - Plus 2 fence tests: test_api_surface.py (5), test_no_positional_inserts.py (3).

## Notes / open questions

- Reuse `inspect_hardware` and the catalog reads — the recommender adds no new facts, only judgment over existing ones.
