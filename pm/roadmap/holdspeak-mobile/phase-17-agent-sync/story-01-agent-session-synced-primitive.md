# HSM-17-01 — The agent-session as a synced primitive (the contract)

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** todo — **leads the phase.** Everything else renders or feeds this contract.
- **Depends on:** the sync object model (Phase 10 — `SyncKind` / `Synced<>` / `ChangeSet` in
  `apple/Sources/Contracts/Sync.swift`), the companion seam (`CompanionTarget` / `CompanionBoardState`
  in `apple/Sources/Providers/Providers.swift`, `/api/companion/*`), the desktop capture
  (`holdspeak/agent_context/` `AgentSession`, `holdspeak/agent_device.py`).
- **Unblocks:** every other story in Phase 17.
- **Owner:** unassigned

## Problem

"Agent" means two unrelated things in our code. The **canonical** one is a live coding session
(`AgentSession{agent ∈ {claude, codex}, session_id, cwd}`, `holdspeak/agent_context/`), already surfaced
to the iPad as `CompanionTarget{agent, sessionID, question?, project?, selected, pinned, stale,
confidence?}` over the *loose, optional-everything* companion DTO seam. The **divergent** one is the
iPad's local `AgentRecord` persona builder — a `@AppStorage` invention with no server domain and no sync.

The desk has no canonical agent object to render, and the word is ambiguous. We fix both: define the
agent-session as a real **contract** type and a real **synced primitive**, and resolve the persona.

## The design

1. **Lift the companion target out of the loose DTO seam into `Contracts`.** Define an `AgentSession`
   contract type (camelCase-in-Swift / snake_case-on-the-wire, matching the Phase-0 serialization
   convention used by `Models.swift`) carrying at least: `agent` (`claude`/`codex`), `sessionId`, `cwd`,
   `project?`, `state` (`working` / `waiting` / `idle` / `ended`), `question?`, `lastActivity`,
   `confidence?`. This is the single source of truth both the companion board and the desk read.
2. **Promote it into the sync layer as ephemeral presence.** The agent-session is **live state, not
   durable content**, so it is NOT stored like Meeting/Artifact. Decide (and document the call) between:
   - extending `SyncKind` with `.agentSession` carried as `Synced<AgentSession>` with last-write-wins +
     tombstone-on-`ended` (cheap, uses the existing engine), or
   - formalizing the companion stream: a typed `/api/agents` (or the existing `/api/companion/status`)
     endpoint whose response is `[AgentSession]` from `Contracts`, polled/streamed by a presence watcher.
   Default lean: the latter — agent presence is high-churn and ephemeral; pushing it through the durable
   `ChangeSet` is the wrong shape. Either way it stops being an untyped DTO.
3. **The desk primitive.** Reclaim `PrimitiveKind.agent` to mean *a live coding session*. Define
   `AgentSessionPrimitive` (a `DeskPrimitive`) backed by the contract `AgentSession` — its `title` is the
   agent + project, its `preview` is the live state or the pending question, its `accepts` includes the
   content kinds (so you can drop a meeting/artifact/note on it as answer context — 17-04), it `emits`
   nothing durable. It is built from synced state, never from `@AppStorage`.
4. **Resolve the persona collision.** Decide the disposition of `AgentRecord`/`ChainRecord`
   (`DeskAgents.swift`): cut entirely, or keep and **rename** to a word that is not "agent" (e.g.
   "template"/"recipe") so "agent" means exactly one thing across server, sync, and desk. (Owner call;
   default: keep, renamed, clearly local-only — it's useful authoring, just not an "agent".)

## Scope

- **In:** the `AgentSession` contract type; its sync/stream transport decision + implementation seam; the
  `AgentSessionPrimitive` conformer; the persona rename/cut. The desktop endpoint shape that serves live
  sessions from `agent_context`/`agent_device`.
- **Out:** the hook install that *populates* sessions (HSM-17-02); the desk rendering + question surfacing
  (HSM-17-03); the answer composer (17-04/05).

## Acceptance criteria

- [ ] `AgentSession` exists in `apple/Sources/Contracts` with a documented wire shape mirroring the
      desktop `AgentSession`/`CompanionTarget`; it round-trips through the contract coder.
- [ ] Live sessions reach the iPad as typed `Contracts.AgentSession` (not a loose `CompanionTarget` DTO),
      via the chosen transport, with `state` and `question` populated.
- [ ] `AgentSessionPrimitive` conforms to `DeskPrimitive`, is built from the synced/streamed session, and
      declares `accepts` for content kinds (for dropped-context answers).
- [ ] `PrimitiveKind.agent` now means a coding session everywhere; the persona builder is renamed or
      removed so the word is unambiguous. No code path treats `AgentRecord` as a `PrimitiveKind.agent`.
- [ ] `swift test` green; the contract round-trip has a unit test.

## Test plan

- Unit: encode/decode an `AgentSession` through the contract coder; a `working`→`waiting(question)`→
  `ended(tombstone)` transition resolves by recency; `AgentSessionPrimitive` derives title/preview/accepts
  correctly from a sample session.
- Integration (with 17-02 stubbed): a fixture session from the desktop endpoint decodes into the typed
  contract and yields one `AgentSessionPrimitive`.
