# Phase 24 — Runtime profiles (basic + advanced), in equilibrium

**Status:** in-progress (opened 2026-06-28) — a pre-GA extension of
[`EQUILIBRIUM.md`](../EQUILIBRIUM.md): the same "honor the contract on every surface" discipline,
applied to *where intelligence runs*.

**Last updated:** 2026-06-28 (**24-01 + 24-02 landed.** `InferenceConfigStore` is profile-backed
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
| HSM-24-03 | Apple **advanced** config — manage the profile list + per-agent `profileId` + the gauge reads `profile.contextLimit` | planned |
| HSM-24-04 | The desktop hub honors profiles (`web_runtime` maps a profile to its runtime) | planned |
| HSM-24-05 | Web authors + uses profiles (the flagship surface) | planned |
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

Next: **24-03** (Apple advanced) — the profiles management screen (add/edit/delete, key→Keychain),
per-agent `Agent.profileId`, the `RunsOnPicker` dropped at every model-touch point (dictation,
generate, agent run/chat, the Ask gesture, the builder), and the gauge reading the assigned profile's
`contextLimit`. That story also enables the live multi-profile switch walk 24-02 deferred.

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
