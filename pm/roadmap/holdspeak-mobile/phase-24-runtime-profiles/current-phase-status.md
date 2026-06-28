# Phase 24 — Runtime profiles (basic + advanced), in equilibrium

**Status:** planned (authored 2026-06-28) — a pre-GA extension of
[`EQUILIBRIUM.md`](../EQUILIBRIUM.md): the same "honor the contract on every surface" discipline,
applied to *where intelligence runs*.

**Last updated:** 2026-06-28 (authored from the owner's call: split the single global
inference choice into **basic** (pick one active target) vs **advanced** (named runtime
profiles + per-agent assignment), and bring it to desktop / iPad / iPhone / web. Grounded in
BACKLOG entry **S**.)

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
| HSM-24-01 | The `RuntimeProfile` contract + `SyncKind.profile` + the Keychain key store (key never syncs) — **leads, load-bearing** | planned |
| HSM-24-02 | Apple **basic** config — the active-profile picker over the existing `ILLMProvider` seam | planned |
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
