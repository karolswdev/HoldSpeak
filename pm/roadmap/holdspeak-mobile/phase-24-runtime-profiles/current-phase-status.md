# Phase 24 — Runtime profiles (basic + advanced), in equilibrium

**Status:** in-progress (opened 2026-06-28) — a pre-GA extension of
[`EQUILIBRIUM.md`](../EQUILIBRIUM.md): the same "honor the contract on every surface" discipline,
applied to *where intelligence runs*.

**Last updated:** 2026-06-28 (**24-01..05 landed — Apple + the hub + the web are done.** The web
`/profiles` surface authors profiles and the desk assigns them per-agent (the inline "Runs on" picker),
key custody is the hub's secret, on-device renders honest n/a; a pre-existing `/desk` dead nav link was
fixed and brought under the launch pre-flight. 0 page errors; full `uv run pytest` 3039 passed.
Remaining: the cross-surface parity proof + docs (24-06). Earlier: **24-01..04 — Apple side + the desktop hub.** The hub
persists/syncs/manages/RUNS on profiles, key from its secrets; full `uv run pytest` 3039 passed.
Remaining: web (24-05) + the cross-surface proof (24-06). Earlier: **24-01 + 24-02 + 24-03 — Apple's side complete.** Profiles
exist, are managed (CRUD, key→Keychain), assignable per-agent, and the inline "Runs on" selector sits
at every model-touch point with honest egress. Next: the hub (24-04), web (24-05), proof (24-06).
Earlier: **24-01 + 24-02 landed.** `InferenceConfigStore` is profile-backed
(migration + key→Keychain + `makeProvider(profile:)` + `resolveProfile`); the reusable `RunsOnPicker`
ships as the always-exposed "Active profile" chip. Below: 24-01 — The `RuntimeProfile` contract +
`SyncKind.profile` + tolerant `ChangeSet` decode + the Keychain `ProfileKeyStore` + the
legacy→profiles migration all ship, with the **never-sync-the-key invariant proven in a test**
and a back-compat test for payloads that predate `profiles`. `swift test` 389/0; the app
compiles with the additions. No UI yet — that's 24-02.)

## Why this phase exists

Today the app **conflates** "where intelligence runs" into one global choice. On Apple it is
`InferenceConfigStore` (`apple/App/MeetingCapture/SketchDiagram.swift`): a single `mode`
(`.local` / `.endpoint`) + a single endpoint (`url` / `model` / `key`) in `UserDefaults`. One
target, app-wide. You cannot say "Scout runs on-device, Editor runs on OpenRouter, Critic runs
on Claude." For a framework whose whole point is *many tailored agents*, that is the wrong shape.

The good news: the abstraction that makes this cheap **already exists** — the `ILLMProvider`
seam. `makeProvider` already returns `LlamaProvider` (on-device) or `OpenAIEndpointProvider`
(OpenAI-compatible). Profiles do not add a runtime; they turn the single config into a **list +
a default**, and let an agent point at one.

It is a pre-GA call because retrofitting a profile contract **after** sync + GA solidify means a
migration. Land the contract first.

## What "a profile" is

A **`RuntimeProfile`** — a named, reusable connectivity target:

```
RuntimeProfile {
  id, name,
  kind: .onDevice | .openAICompatible,
  onDevice:        { modelFile }                       // a downloaded .gguf
  openAICompatible:{ baseURL, model, apiKeyRef }       // a ref, NOT the key
  contextLimit: Int,                                   // the usable window
  egressScope                                          // feeds the trust badge
}
```

- **Basic configuration** = pick ONE active profile ("Run on: [This iPhone ▾]"). Today's
  experience, reframed; the casual user meets no new concept.
- **Advanced configuration** = manage a LIST of profiles + assign one **per agent**
  (`AgentRecord.profileId`, empty = the active default).

**Closes the gauge loop (Phase shipped the gauge already):** the GROUNDING CONTEXT ring reads the
*assigned profile's* `contextLimit` — "Scout on Claude (200k) = 1% full; Scout on a local 3B (8k)
= 22%."

## The governing usability principle (owner, 2026-06-28)

**Every surface that touches a model exposes a tiny, inline "Runs on: [Profile ▾]" control** — the
resolved default already selected, one tap to change, *at the point of use*, every time. Not buried
in Settings. Most users never touch it; but the default is always **shown** (never implicit) and
**changeable at any moment**.

- **Resolution order** for "which profile runs this": an explicit inline override → the agent's
  assigned `profileId` → the global active profile. Whichever applies is the one the chip displays.
- **One reusable component** (a `RunsOnPicker` chip) is dropped at every model-touch point —
  dictation, meeting generate, agent run/chat, chains, the desk "Ask"/route-to-AI-core gesture, the
  builder. Introduced in 24-02 (with the resolution helper); made pervasive in 24-03.
- `makeProvider` takes an explicit `RuntimeProfile`; call sites resolve via the order above so the
  inline override is honored.

## The one hard rule (security / robustness)

**API keys are credentials and MUST NOT sync.** The profile *shape* (name/kind/baseURL/model/
contextLimit/egress) syncs as a primitive; the **key lives only in the device Keychain**,
referenced by profile id, never in the synced payload. Each surface holds its own key for a shared
profile. (Same principle as the connector "credential stays on the desktop" rule and the existing
"API key never leaves this store" comment.)

## Equilibrium (the cross-surface point)

Add `SyncKind.profile` so desktop hub / iPad / iPhone / web share the same named profiles (shape
only). Each surface honors the profile **contract** through its own runtime, with honest `n/a`
where a surface cannot host a kind (an on-device GGUF profile is `n/a` on web). The egress badge
reads `profile.egressScope` so trust stays honest per profile.

## Story status

| Story | One-liner | Status |
|-------|-----------|--------|
| HSM-24-01 | The `RuntimeProfile` contract + `SyncKind.profile` + the Keychain key store (key never syncs) — **leads, load-bearing** | **done** (contract + migration + tolerant `ChangeSet` decode + `ProfileKeyStore`; never-sync invariant tested; `swift test` 389/0) |
| HSM-24-02 | Apple **basic** config — the active-profile picker over the existing `ILLMProvider` seam | **done** (profile-backed `InferenceConfigStore` + migration + key→Keychain + `makeProvider(profile:)` + `resolveProfile` + the reusable `RunsOnPicker`; `swift test` 389/0) |
| HSM-24-03 | Apple **advanced** config — manage the profile list + per-agent `profileId` + the gauge reads `profile.contextLimit` | **done** (CRUD + per-agent chip + gauge-per-profile + agent-run routing + inline `RunsOnPicker` at the desk Ask/route & meeting generate, with honest egress; dictation n/a, workbench uses active) |
| HSM-24-04 | The desktop hub honors profiles (`web_runtime` maps a profile to its runtime) | **done** (schema v3→v4 + `ProfileRepository` + sync + profiles CRUD routes + agent-run resolution with the key from the hub's secrets; never-sync-key tested; full `uv run pytest` 3039 passed) |
| HSM-24-05 | Web authors + uses profiles (the flagship surface) | **done** (the web `/profiles` list+editor over `/api/profiles` + the desk agent "Runs on" picker + per-agent chip; honest n/a for on-device; key is the hub's secret, never the browser; fixed a pre-existing `/desk` dead nav link; 0 page errors; 3039 passed) |
| HSM-24-06 | Cross-surface parity proof + the docs story | planned |

## Sequencing

```
24-01 (contract + Keychain) ─► 24-02 (Apple basic) ─► 24-03 (Apple advanced + per-agent)
                            └─► 24-04 (desktop hub) ─► 24-05 (web) ─► 24-06 (proof + docs)
```

24-01 is load-bearing — every surface depends on the contract + the never-sync key rule. 24-02
(basic) is a near-pure refactor of `InferenceConfigStore` into "a list with one active" and must
stay byte-identical for the single-target user. 24-03 unlocks the per-agent power (and lights up
the gauge). 24-04/05 bring the other surfaces into parity. 24-06 is the parity gate + docs.

## Where we are

**Opened; the foundation is in.** 24-01 landed the load-bearing contract with zero behavior change:
`RuntimeProfile` + `RuntimeProfileMigration` (Contracts/Primitives.swift), `SyncKind.profile` +
`ChangeSet.profiles` with a **tolerant decoder** (any absent array → `[]`, so a surface that doesn't
yet know `profiles` still decodes), and `ProfileKeyStore` (App-layer Keychain; the key is keyed by
profile id with `…ThisDeviceOnly` accessibility and **never** appears on the shape or in a
`ChangeSet`). Eight tests, including the never-sync invariant and the back-compat decode.

**24-02 also landed.** `InferenceConfigStore` is now profile-backed (`profiles` + `activeProfileId`,
migrated on first launch, key moved to the Keychain); the active profile is applied onto the legacy
fields so every existing reader is unchanged; `makeProvider(profile:)` + `resolveProfile` (override →
agent → active) are in; and the **reusable `RunsOnPicker`** ships — shown in Settings as the always-
exposed "Active profile" chip (the owner's "the default is always exposed + changeable" principle).

**24-03 in progress.** Landed: `Agent.profileId` (+ `AgentRecord.profileId`, tolerant decode so saved
agents are never wiped); the **advanced Profiles screen** (`ProfilesView` — add/edit/delete on-device
+ OpenAI-compatible endpoints, **key→Keychain via `ProfileKeyStore`**, set-active), reached from
Settings → "Manage profiles"; the builder's **"Runs on" chip** (per-agent profile) with the gauge now
reading the *assigned* profile's `contextLimit`; and **agent-run routing** (`callLLM`/`runAssembled`/
`agentReply` resolve the agent's profile → `makeProvider(profile:)`). Verified in the sim (2-profile
list, the chip, the gauge).

**24-03 DONE.** The inline `RunsOnPicker` is now at every user-facing model-touch point: the agent
builder ("Runs on" chip), the desk **Route through the AI core / Ask** gesture (with the egress badge
made honest — was hardcoded "On device"), and **meeting generate** (the hardcoded "on-device" wording
dropped). Dictation is remote → honest n/a; the Workbench uses the active default (per-node chips a
noted follow-up). `swift test` 389/0; device-SDK compiles.

**24-04 DONE** — the desktop hub now persists (schema v4), syncs, manages (profiles CRUD), and RUNS
on profiles (`/api/agents/{id}/run` resolves the agent's profile → its endpoint with the key from the
hub's secrets, never the payload; never-sync-key proven). Full `uv run pytest` 3039 passed. Also fixed
the pre-existing `/cadence` route-preflight gap.

**24-05 DONE** — the web flagship authors profiles at parity with Apple advanced: a new `/profiles`
surface (card grid + drawer editor over `/api/profiles`) and the desk agent editor's inline "Runs on:
[Profile ▾]" picker + per-agent egress chip. On-device profiles render honest n/a (no GGUF in a
browser); the key is the hub's env secret, shown by reference (`HOLDSPEAK_PROFILE_<id>_KEY`), never a
field and never on any payload — a tighter never-sync posture than the plan imagined. Fixed a
pre-existing dead nav link (`/desk` had no route; the TopNav pointed at it) and brought `/desk` +
`/profiles` under the launch pre-flight. Built clean; Playwright pass = 0 page errors (profiles list +
editor, desk cards + agent form); full `uv run pytest` 3039 passed.

Next: **24-06** (cross-surface parity proof + docs). Apple + the hub + the web are done; only the
parity gate + docs remain.

## Carried context

- Seam: `apple/Sources/Providers/Inference/` — `ILLMProvider`, `OpenAIEndpointProvider`,
  `EndpointConfig`; `LlamaProvider` in `InferenceLlama`. `makeProvider` is in
  `SketchDiagram.swift` (`InferenceConfigStore`).
- Per-agent: `AgentRecord` (`apple/App/MeetingCapture/DeskAgents.swift`) — add `profileId`.
- Gauge: `ContextGauge` + `DioAgentBuilder.contextLimit` (already reads a limit; point it at the
  profile).
- Sync: `apple/Sources/Contracts/Sync.swift` — the `SyncKind` enum + `ChangeSet`.
- Grounding assembly (the gauge's truth): `agentRoleAndContext` in `DeskDioramaStage.swift`.
- Related but SEPARATE (kept out of this phase unless the owner folds it in): "make KB grounding
  actually inject content" — today the KB only adds a one-line hint, so the gauge shows ~0 for a
  KB. See BACKLOG.

## Source of record

BACKLOG entry **S** (`pm/roadmap/holdspeak/BACKLOG.md`). This phase is its execution plan.
