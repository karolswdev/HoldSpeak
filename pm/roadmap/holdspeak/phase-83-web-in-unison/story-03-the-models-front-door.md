# HS-83-03 — The models front door (`/api/models` + chat-with-model)

- **Project:** holdspeak
- **Phase:** 83
- **Status:** done — 2026-07-07, see [`evidence-story-03.md`](./evidence-story-03.md).
- **Depends on:** HS-83-02 (the chat surface a model persona opens into). The
  route half is independent and can land first.
- **Unblocks:** HS-83-04.

## Problem

Grounded 2026-07-07: no web surface lists what the hub can run. The runnable
set exists only as (a) the profiles page's per-profile `model` fields and (b)
the ask route's 400 body when you guess wrong. The iPad ships a models front
door (HSM-15-13); the web — the surface that lives ON the hub — has none.

## The design

- **The route.** `GET /api/models` returns the runnable allow-list — the SAME
  set `/api/ask`'s override check computes (the hub's own configured model +
  each non-deleted profile's model), each row
  `{name, source: "hub" | "profile", profile_id?}`. One derivation, shared
  with the ask route's check (extract the helper; no second list to drift).
  New route ⇒ regenerate `docs/api-surface.json`.
- **The front door.** The desk lists the hub's models (a models row on the
  desk chrome or rail — decided at build against the desk idiom); one click
  opens the HS-83-02 chat surface with a transient persona
  (`modelchat:desktop:<model>`) whose turns pin `model: <name>` on the ask
  body. No parallel chat component (the 15-13 rule).
- **Honest states.** Hub unreachable renders the degraded state it already
  has; an unknown-model 400 (config changed under a stale list) renders the
  hub's `allowed_models` verbatim.

## Acceptance criteria

- [x] `GET /api/models` names exactly the ask route's allow-list (test pins
      equality via the shared derivation); api-surface regenerated.
      (`_runnable_models` — one derivation; set-equality pytest.)
- [x] The desk lists the models; one click opens a chat titled with the model.
      (The rail's MODELS section; rig-asserted hub-row-first + title.)
- [x] A turn in that chat runs pinned to THAT model; the reply's badge wears
      the hub-reported model/egress. (Rig: the pin resolved at the engine
      seam; badge asserted. The in-browser .43 beat rides HS-83-04's walk;
      the override itself was real-metal-proven in HSM-15-11/15-13.)
- [x] The thread persists under the model-chat persona id; grounding rides.
      (`modelchat:hub:<name>` keys the same device-local store; the composer
      carries the HS-83-01 picker.)
- [x] Screenshots: the models list; a model-chat reply. (`hs-83-03-*.png`.)

## Test plan

- Hub: pytest for the route (set equality with the ask allow-list, shape,
  auth) — `uv run pytest -q -k models`.
- Vitest: the persona mapping + pinned-model request body.
- Live: one real pinned turn; screenshots.
