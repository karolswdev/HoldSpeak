# HSM-24-05 — Web authors + uses profiles

- **Status:** done (2026-06-28) — the web `/profiles` surface (list + editor over `/api/profiles`) + the
  desk agent editor's "Runs on" picker + per-agent chip; on-device profiles render honest n/a; the key
  is the hub's secret (`HOLDSPEAK_PROFILE_<id>_KEY`), never the browser. Also fixed a pre-existing dead
  nav link (`/desk` had no route). Evidence: [evidence-story-05.md](./evidence-story-05.md). Built
  (`npm run build`), Playwright-screenshotted (0 page errors), full `uv run pytest` 3039 passed.

**Key custody divergence (deliberate, stronger):** the plan said "hand the key to the hub over the
session." The shipped hub (24-04) holds the key in its environment secrets and joins it at run time —
so the key never rides ANY payload, not even a hub-bound one. The web editor therefore shows
`requires_key` + the env var name to set on the hub; there is no key field and no key flow over the
wire. This is a tighter never-sync posture than the story imagined.

## Problem

Web is the flagship surface. With profiles synced, the web app must let you author/manage them and
assign agents to them, honoring the same contract + the same never-sync key rule — or web users are
stuck on a single backend while iPad users aren't (an equilibrium break).

## The design

- A web "Runtime profiles" surface mirroring the Apple advanced screen: list + editor (kind, model/
  endpoint, declared context limit, egress preview). Same `RuntimeProfile` shape over the same sync.
- **Key handling on web:** the key is a credential — it is held by the **hub** (its secrets path),
  not stored in the browser or the synced shape. The web UI sets a key by handing it to the hub over
  the authenticated session for that profile id; the browser never persists it. (Web has no Keychain;
  the hub is its key custodian.)
- Per-agent "Runs on" picker in the web agent editor → `agent.profileId`.
- Honest `n/a`: an `.onDevice` GGUF profile is shown as "device-only" on web (it can't run a local
  GGUF in a browser); web defaults such agents to a cloud/endpoint profile when run from web.

## Scope

- Web profiles list + editor; per-agent assignment.
- Key-to-hub flow (browser never persists the key).
- The `n/a` rendering for device-only kinds.

## Test plan

- Web smoke + a route test: profiles list/create/assign; the key is never returned to the browser in
  any payload; an agent assigned a cloud profile runs via the hub.

## Done when

Web can author profiles, assign agents, and run them — with the key custodian being the hub, never
the browser — at parity with Apple advanced.
