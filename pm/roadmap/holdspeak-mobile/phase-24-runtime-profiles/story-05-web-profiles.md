# HSM-24-05 — Web authors + uses profiles

**Status:** planned (after 24-01; needs the hub from 24-04 as its backend).

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
