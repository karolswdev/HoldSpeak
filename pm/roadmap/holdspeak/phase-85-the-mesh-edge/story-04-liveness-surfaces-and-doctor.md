# HS-85-04 — Liveness on every surface + the honest doctor

- **Project:** holdspeak
- **Phase:** 85
- **Status:** backlog
- **Depends on:** HS-85-02, HS-85-03
- **Unblocks:** HS-85-05
- **Owner:** unassigned

## Problem

A mesh profile's availability is soft — real only while its worker polls.
Existence-only pickers would invite runs that refuse (or worse, feel like
hangs). Every surface that offers a mesh target must show liveness, every
refusal must name the node, and doctor must answer "which edges are alive
right now" the way it answers everything else since HS-84-04: honestly, in
one line.

## Scope

- In: `GET /api/models` + `_runnable_models` — meshNode profiles appear
  with their node and a `live` flag (+ last-seen age when stale); the ask
  route's model-override refusal for an offline mesh model is immediate and
  names the node (never a queue-then-timeout).
- In: the pickers grown in HS-84-03 (`/settings` Runs-on, `/dictation`
  Runs-on-profile) and the desk rail models section — mesh entries labeled
  live/offline ("Pocket 4B — mesh, offline 3m"); offline entries stay
  pickable (assignment is durable; liveness is momentary) but wear the
  state.
- In: doctor — the "Runtime profiles" check names a meshNode resolution
  with its liveness; a new "Mesh edges" line (or check) lists workers seen
  and last-seen ages; `/api/setup/status` carries it via the standing 1:1
  adapter.
- In: `/profiles` cards for meshNode kind (node named, liveness chip,
  honest n/a note that the WEB can't host it — the existing on-device
  pattern).
- Out: new pages, push/WS liveness (polling truth only), Apple UI.

## Acceptance criteria

- [ ] `/api/models` rows for mesh profiles carry `live` + last-seen; the
  set-equality test with the ask allow-list still holds (tests).
- [ ] Offline mesh model override ⇒ immediate 400 naming the node (route
  test with an aged worker clock).
- [ ] Pickers + rail render the liveness state (screenshot-verified, live
  and offline both, via the house rig pattern).
- [ ] Doctor lists mesh workers with ages; the drift guard stays green
  with the new check registered (tests).
- [ ] Non-mesh picker/doctor behavior byte-identical (existing tests
  unmodified).

## Test plan

- Unit: extend `test_web_routes_ask.py` (models/override cases with an
  injected liveness window) + doctor cases in
  `test_doctor_runtime_profiles.py`; `uv run pytest -q tests/ -k
  "doctor or ask"`.
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`; web
  bundle rebuilt; a `scripts/screenshot_hs85_*.py` rig with asserted claims.
- Manual / device: n/a — HS-85-05.

## Notes / open questions

- Liveness rides existing payloads (`/api/models`, profile lists) — no new
  poller on any client; the web reads what it already fetches.
- Wording stays badge-not-prose (Phase 62): a chip like "mesh · live" /
  "mesh · offline 3m", never a sentence.
