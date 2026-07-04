# Phase 17 — Agent Sync (the coder on your desk)

**Status:** in-progress (opened 2026-06-26, on the owner's direct instruction: *"the full agent sync done
by you... we inject ourselves by running our hooks on our Claude and Codex instances, and then those
instances are showing on our DeskOS as primitives when the agent has a question, when we answer, and so
on."*)

**Last updated:** 2026-07-04 (**HSM-17-07 done — the entry points know the loop.** AGENT_HOOK_INSTALL.md leads with the one-command install/uninstall (and its stale event lists corrected to the shipped templates); the README's iPad section documents coding-agents-on-the-desk with the four answer modes and the never-autonomous guarantee; ARCHITECTURE.md gained "The agent sync loop" mermaid (hooks → registry → hub → desk object → composer → explicit send → the pane) in the house style. Doc guard 18 green, mermaid render guard 2 green. THE PHASE IS NOW 5/7: only HSM-17-01 (event-stream taxonomy + the `.agent`-reclaim/persona owner call) and HSM-17-06 (the cabled-iPad walk: mic, drop, glare, on-device air-gap draft) remain. Earlier: **HSM-17-05 done — THE LOOP IS INTELLIGENT: the owner's headline.** `CoderAnswer.draftPrompt/draft` (RuntimeCore): the question is the `[TASK]`, dropped grounding a cited `[CONTEXT]` block, one `ILLMProvider.complete` on a FRESH resolved provider (the desk's `callLLM`, Mode-A KV rule) — and the draft API cannot reach the desktop client by construction (test-pinned: never autonomous). The composer gained the violet Draft-with-AI/Re-draft action with its OWN egress chip (`.local`/`.cloud("endpoint")` — where the draft RUNS ≠ where the answer GOES), drafting state, honest inline errors, the draft landing editable. LIVE endpoint proof: the LAN Qwythos drafted a first-person answer that argued FROM the attached mesh-queue grounding in 0.52s (`CoderDraftLiveTests`, opt-in-gated like the Python e2es). 6 new unit tests; suite 465/9/0; sim build green; the composer shot shows every 17-04+05 affordance in one frame. The on-device air-gap draft is a 17-06 device beat by the story's own acceptance. Earlier: **HSM-17-04 done — THE LOOP IS CLOSED: a live coder asked, the desk's flow answered, the coder continued.** `CoderAnswer` (RuntimeCore) is the one flow: compose (reply + cited/trimmable dropped-context grounding) → select-then-send into the EXACT session → `approve` sends the raw dialog keystroke; failed select never sends (9 tests). The composer gained the speak-to-fill mic, the grounding block, and the egress badge; the keystone drop gesture pointed at a waiting coder opens the composer with the dropped primitive's `routableText`. answerCoder/approveCoder are REAL (demo stays offline-optimistic; failure keeps the question on the desk). THE PROOF FOUND A REAL BUG: `tmux_transport` submitted with a named-Enter send-keys that current Claude TUIs (2.1.x) drop — answers were 'delivered' yet sat unsubmitted; fixed to a literal `\r` and re-proven: the coder acknowledged the grounded reply verbatim and the desk flipped waiting→working on the next poll (before/after shots). Honest note: AskUserQuestion SELECTOR dialogs ignore typed text (arrows only) — recorded for the 17-01 event taxonomy; the composer targets plain-text questions, the canonical shape. Earlier: **HSM-17-03 done — the coders are ON THE DESK, fed by real data.** The 17-01 transport call decided + shipped: `LiveCoderSession` + `IDesktopClient.coderSessions()` (typed polled presence endpoint, honest-unsupported default) decode `GET /api/coders/sessions`; `CoderSession.init(from:)` builds an honest minimal feed; `startCoderPolling()` in the diorama (4s cadence, PresenceStore pattern, demo-suppressed) maps the live set into `coders` with a once-per-rising-edge glare into `waiting` (6s auto-clear); ended tombstones leave via the existing filter. PROOF: beyond the seeded bar, the sim paired to a live Mac hub rendered the REAL registry — the session that built the story (working), the owner's delivery-workbench session (waiting, accent), the morning's codex (idle by decay) — and the ended claude absent. 4 new Providers tests on the real proof-run wire payload; SPM suite 449/0; sim build green. Sim-pairing gotcha recorded (write the app-container plist directly; spawn defaults write lands in the wrong domain). Earlier: **HSM-17-02 done — the capture loop is LIVE on the owner's Mac.** `AgentSession` gained the raw `lifecycle` + secret-filtered `question`; `effective_state()` decays idle/dead at read time; the Claude template gained Notification/PostToolUse/SessionEnd (Codex Notification/SessionEnd); `holdspeak agent-hook install|uninstall` is the one-command, idempotent, reversible inject; `GET /api/coders/sessions` serves the FULL live set (not just awaiting) in the 17-01 shape. Real-metal proven end to end: a live Claude driven working → waiting(two real permission asks captured) → resumed(question cleared) → SessionEnd tombstone, plus a live Codex session captured (codex emits no SessionEnd; the decay window tombstones it — recorded honestly); the session that BUILT the story reported through its own hooks while proving it. 23 new tests. TRUTH-UP: the `desk-parity` branch the 2026-06-26 note below calls 'uncommitted' has since been MERGED to main via the Primitive Framework waves (`389d2b1`, `b5baaac` — PRs #140–142); `DeskCoder.swift` (CoderSession/CoderEvent/AgentSessionPrimitive) is in main. 17-01's remaining gap is the typed Contracts round-trip + the event-stream transport, not the Swift scaffolding. Earlier: opened. Authored directly from the instruction, grounded in a two-sided
parity audit of the desktop server domain and the cross-device sync contract. Leads with **HSM-17-01 (the
agent-session as a synced primitive)** — the canonical contract everything else is built on, which also
**resolves the "agent" naming collision** in favour of the one true meaning: a live Claude/Codex coding
session.)

## Why this phase exists

A parity audit this session found that "agent" already means **two unrelated things** in our own code, and
we'd been building the wrong one as a primitive:

- The **canonical agent** is a live coding session: `AgentSession{agent ∈ {claude, codex}, session_id,
  cwd}` (`holdspeak/agent_context/`), captured by our integration hooks
  (`holdspeak/commands/agent_hook.py`) and already formatted for the iPad
  (`holdspeak/agent_device.py`). The companion seam already carries it as `CompanionTarget{agent,
  sessionID, question?, ...}` over `/api/companion/*`.
- The **divergent invention** is the iPad's local persona builder (`AgentRecord` / `ChainRecord` in
  `DeskAgents.swift`) — a user-authored system-prompt + avatar object with **no server domain
  counterpart** and no sync. It wears the same word and means something else.

The owner's call settles it: **"agent" = a Claude/Codex session.** This phase makes that the real,
synced DeskOS primitive and closes the loop — the coder asks, it surfaces on your desk, you answer (typed
/ spoken / with dropped context / **AI-drafted**), and the answer is injected back into the live session.

This is also the proof that the DeskOS is a faithful client of the shared domain, not a third parallel
model: the agent primitive is **promoted into the sync/contract layer**, not invented in
`@AppStorage`.

## The load-bearing design call (decided here, refined in 17-01)

The whole phase reuses three **already-proven** seams and invents almost nothing except the primitive +
sync promotion:

1. **Capture (the hooks).** `agent_hook.py` installs into the live Claude/Codex instances so each one
   reports its state — working, *has a question*, idle — up to the desktop continuously. The injection
   into our own running instances is the literal "we inject ourselves by running our hooks."
2. **Surface (the primitive).** A live session becomes a first-class `DeskPrimitive` (`PrimitiveKind.agent`
   reclaimed for this meaning) backed by the synced `AgentSession` / `CompanionTarget`, **not**
   `AgentRecord`. When it `has a question`, it gets the glaring NEW-arrival treatment — *"Claude needs
   you."*
3. **Answer (the loop close).** The reply rides the proven inject path (`/api/dictation/remote`, the
   Phase-13 answer-the-coder gate). Four ways to compose it, one inject:
   - **Spoken** (WhisperKit → text, the `VoiceNoteComposer` path).
   - **Typed.**
   - **Dropped context** — pull a meeting / artifact / note onto the agent's question so it is answered
     *from that*; the dropped primitive's `routableText` is the grounding. This is the keystone routing
     gesture.
   - **AI-drafted (local or remote)** — route the question (+ any dropped context) through the AI core
     (`ILLMProvider`: on-device `LlamaProvider` Mode A, or the endpoint Mode B/C, both proven on the
     iPad) → a drafted answer comes back → **you approve / edit → it injects.**

**Non-negotiable: never autonomous.** AI may *draft*; only an explicit human approval *sends*. Every
inject carries the egress badge (the answer leaves the iPad for the Mac). Same approval posture the
Companion track already holds.

**Content vs. organization vs. this.** Content (Meeting/Artifact) syncs already (Phase 10); organization
(KBs/dirs) is Phase 16. The agent-session is **ephemeral live state**, not durable content — so it syncs
as a **streamed presence record** (last-write, tombstoned when the session ends), not a stored entity.
17-01 decides whether that rides an extended `SyncKind` or a formalized companion stream lifted out of the
loose DTO seam into `Contracts`.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-17-01 | The agent-session as a synced primitive (the contract) — **leads** | **done** (2026-07-04: transport shipped with 17-03; the persona collision resolved by the owner-ratified RECIPE rename, atomic across hub/wire/Swift/web; the rich event stream filed as its own backlog feature) |
| HSM-17-02 | Hooks: inject into the live Claude/Codex instances (capture) | **done** (2026-07-04, real-metal both agents) |
| HSM-17-03 | The agent on the desk: a live session as a DeskOS primitive | **done** (2026-07-04, live-hub sim proof) |
| HSM-17-04 | Answer the coder — spoken / typed / dropped-context | **done** (2026-07-04, live loop + transport bug fixed) |
| HSM-17-05 | AI-drafted answers (local or remote, approve-then-inject) | **done** (2026-07-04, endpoint draft live-proven; on-device run = a 17-06 beat) |
| HSM-17-06 | The real-metal proof (cabled iPad + a live coder on the Mac) | todo |
| HSM-17-07 | Docs — the agent-sync loop, the hook install, entry points | **done** (2026-07-04, both guards green) |
| HSM-17-08 | The first-class Recipe experience (in-world, no modals) — the rename's rider mandate | **done** (2026-07-04: DioAtelierPanel; all four surfaces off the scrim; the chain builder's live pipeline; web authoring filed as the next slice) |

## Where we are

**The robust contract + the live "running coder" feed shipped + Simulator-proven** (branch
`holdspeak-mobile/desk-parity`, uncommitted), in `apple/App/MeetingCapture/DeskCoder.swift`. On the owner's
call (*"we need it robust... recreate the actual session... a real running Claude"*) the contract is a
**session mirror**, not a presence badge:

- **`CoderSession`** — header (`agent`, `sessionId`, `project`, `model`, `tokensUsed`, `state`) **plus an
  append-log `events: [CoderEvent]`**. `state` ∈ working/waiting/idle/ended; `question`/`pendingApproval`
  derived from the tail. Initializer from the live `CompanionTarget` for the thin-wire fallback.
- **`CoderEvent`** — the full taxonomy: `userPrompt`, `assistant` (narration), `tool(CoderTool, target,
  detail)` (read/edit/write/bash/search/web/task), `result(ok, summary, +added/−removed)`, `command(cmd,
  exit, output)`, `approval(question, command)` (the blocking ask), `notification`, `usage(tokens)`,
  `ended`. This is the "how much Claude/Codex fill our sessions" model — diffs, commands, approvals, all.
- **`AgentSessionPrimitive`** (`DeskPrimitive`, kind **`.coder`**) — on the desk: working sits calm
  (cobalt), `waiting` **glares** (accent ring + NEW). Tap → the feed.
- **`DioCoderSession`** — the live running-coder window: header (model + tokens + state pill), a
  **scrolling, auto-to-latest replay** of the event stream (rich per-kind rows: tool verbs + targets,
  `+N −M` diffs, `$` commands with exit codes, narration), and the pending **approval card** with
  **Approve / Answer** pinned at the bottom.
- **`DioCoderAnswer`** — the typed answer composer (the coder's question shown as context → Send).
- Seeded sim proof (`SIMCTL_CHILD_HS_DESK_CODER=1|session|answer`): `screenshots/coders_on_desk.png`,
  `screenshots/coder_session_feed.png`, `screenshots/coder_answer.png`.

**Naming call (this slice):** coding session shipped as kind **`.coder`**, not by reclaiming `.agent`
(that cascade through the Tailored-Agents subsystem is a separate deliberate rename, owner go-ahead
pending).

**Remaining on the lead stories:**
- 17-01: move `CoderSession`/`CoderEvent` into `Contracts` (snake_case wire) + pick/implement the
  transport — an **append/tail event stream** (NOT the durable `ChangeSet`), with **server-side
  persistence for replay** (the dictation-journal pattern). Today the feed is built from a seeded session.
- 17-02: the hooks emit the full `CoderEvent` taxonomy from live Claude Code / Codex instances
  (PreToolUse/PostToolUse/UserPromptSubmit/Notification/Stop + the transcript), secret-filtered.
- 17-03: wire the **live** stream → `coders`, continuous updates, clean removal on `ended`.
- 17-04: the real inject + approve (`HTTPDesktopClient.sendRemoteDictation` / approve route) + voice +
  dropped context; today Send/Approve are optimistic desk-side stubs that append a resolving event.
- 17-05 (AI-draft) + 17-06 (real metal) + 17-07 (docs) unstarted.

## Carried context (not in scope, flagged)

- The uncommitted **desk-parity batch** (branch `holdspeak-mobile/desk-parity`: the zone studio, the
  kind-agnostic filing, the Note/KB/Game primitives) is held pending the broader content-model parity
  call (`OutputRecord → Artifact`, etc.), which belongs to the Phase-16 capability/sync rebuild, not
  here. 17-01 only touches the **agent** primitive. See [[project_desk_parity_lite]].
- The persona builder (`AgentRecord`/`ChainRecord`) disposition is decided in **17-01**: cut, or kept and
  **renamed** so it never shares the word "agent."
