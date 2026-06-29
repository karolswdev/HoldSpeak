# HSM-24-03 — Apple advanced config: manage profiles + per-agent assignment + the gauge

- **Status:** done (2026-06-28) — CRUD + per-agent + inline selectors at the desk Ask/route, meeting generate, and the builder. Evidence: [evidence-story-03.md](./evidence-story-03.md). `swift test` 389/0. (Dictation = remote n/a; workbench uses the active default — per-node chips a noted follow-up.)

## Problem

The owner's exact ask: "one thing running locally, another against an OpenRouter endpoint with an
API key, a third against Claude" — and different agents on different backends.

## The design

- **Advanced config screen** (in-world, not a modal hell — see the no-modals rule): a list of
  `RuntimeProfile`s with add / edit / delete. The editor:
  - Name; kind toggle (On-device / OpenAI-compatible).
  - On-device → the downloaded-model picker (reuse `ModelsView` data).
  - OpenAI-compatible → base URL + model (the `fetchModels()` picker) + an **API key field that
    writes to the Keychain via `ProfileKeyStore`**, never to the synced shape. A voice mic on text
    fields (the every-input rule).
  - `contextLimit`: on-device computed; endpoint declared (with sensible presets, e.g. 8k/32k/128k/
    200k) since we can't always introspect an endpoint's window.
  - The egress badge previews `local` vs `cloud(host)`.
- **Per-agent assignment:** add `AgentRecord.profileId` (empty = active default). The agent builder's
  GROUNDING CONTEXT section gains a "Runs on" chip row (the profiles) so you pick the agent's backend
  right where you set its grounding.
- **The gauge closes the loop:** `DioAgentBuilder.contextLimit` is sourced from the *assigned
  profile* (not just the global active one), so the ring reflects that agent's real window.

## Scope

- The advanced profiles screen (list + in-world editor, voice mics, Keychain key write).
- `AgentRecord.profileId` (+ contract `Agent.profileId`, sync-safe) + a "Runs on" picker in the
  builder.
- The gauge reads the assigned profile's `contextLimit`.

## Test plan

- `swift test`: editing a profile updates the synced shape but writes the key only to the Keychain;
  an agent with `profileId` resolves to that profile's provider + `contextLimit`.
- Real metal (per the verify-on-device rule): create an on-device profile and an OpenAI-compatible
  profile (a real key), assign two agents to different profiles, run each, confirm each hits its
  backend and the gauge shows each agent's true fill.

## Done when

You can define multiple profiles (local + endpoint(s) with keys), assign agents to them, and the
gauge reflects each agent's window — proven on a cabled device with at least one real endpoint.
