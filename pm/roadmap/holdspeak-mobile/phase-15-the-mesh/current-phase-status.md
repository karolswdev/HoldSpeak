# Phase 15 — The Mesh

**Status:** in-progress (opened 2026-06-22 in direct response to the owner: "I do love
your idea of the mesh… create a fucking phase that's going to be so amazing." The owner
ratified the holistic framing — HoldSpeak is not a Mac app with an iPad sidekick; it is a
**personal intelligence mesh** — and asked that this phase ALSO ship LinkedIn-worthy proof:
a senior software architect increasing his efficiency with tools + memory he paid for,
running local inference on a machine he owns that is **completely air-gapped**, and still
extracting enormous value.)

**Last updated:** 2026-06-22 (**opened.** Authored from the owner's ratified vision. The
connective tissue already exists in code — the iPad pairs to the desktop over
`HTTPDesktopClient` (host + port + token), `POST /api/dictation/remote` already runs an iPad
dictation through the desktop's full pipeline into any focused app, `/api/companion/*` is the
answer-the-coder board, and inference already resolves on-device / homelab / endpoint
(`RuntimeMode` A/B/C). The Mesh **unifies** these into one felt product. Leading with
**HSM-15-01 (dictation into your Mac, as a first-class flagship mode)** — highest daily value,
smallest new surface, reuses `/api/dictation/remote`.)

## Why this phase exists

HoldSpeak's pieces are built but **fragmented**: a capability-rich desktop server (the hub —
the big models, the dictation pipeline, the actuators/connectors), an on-device meeting +
Workbench app, and a separate companion (answer-the-coder) surface. The wiring between them
exists but is exposed as separate apps and separate concepts. There is no single model that
says *"these are your devices, this is your intelligence, it runs wherever you point it, and
nothing leaves without your nod."*

The Mesh is that model. It is the difference between "an iPad app that can also call a server"
and **one copilot that lives across the devices you own**. It is also the most honest, most
sellable story HoldSpeak has: a senior architect, on hardware he controls, **air-gapped**,
extracting real daily value from local inference — no SaaS, no data exhaust, paid-for tools and
paid-for memory working for him.

**And the mesh is not only reactive.** The desktop already runs the agent-hook loop — it tracks
which coding agents (Claude/Codex in tmux) are live, which are **awaiting your answer**, and the
exact question each is asking (`awaiting_response` / `last_assistant_text` in
`agent_context/sessions.py`; surfaced by `GET /api/companion/status`). HoldSpeak is therefore also
**your agent command desk** — your "vibe code desk": when an agent goes quiet waiting on you, the
mesh **proactively surfaces it** ("your agent in `pylon-infra` is waiting: *migrate the schema
now?*") on whatever glass you're holding, and you answer by voice. Dictation is you → your agents;
the desk is your agents → you. Together — on top of the intelligence layer (meetings, dictation,
the Workbench) — that is the proper product: **you, linked to your agents and your intelligence,
across your mesh.** This pillar was under-weighted in the first draft of this phase and is now
first-class (HSM-15-08/09).

## Goal

Turn the desktop server + the iPad companion into **one coherent mesh**:

1. **Two modes on every surface.** Dictation (into your Mac) becomes a first-class flagship
   mode beside meetings — the iPad is the best microphone you own; the Mac has the keyboard and
   the apps.
2. **Fluid compute.** "RUNS ON" means *where in your mesh a step runs* — On-device / Your Mac /
   Endpoint — and "Your Mac" is a **capability** target (its connectors, its big models), not
   just an inference URL.
3. **One queue** spanning the mesh — desktop jobs and pending approvals appear beside on-device
   jobs, on the glass in your hand.
4. **One approval + egress contract** — approving on either surface is one act; the egress scope
   is consistent everywhere.
5. **The Agent Desk (proactive, agent-aware).** A first-class "vibe code desk": your live coding
   agents across the mesh, their state (working / **waiting on you** / idle), and the question each
   is asking — surfaced **proactively** (a Queue-HUD lane / a presence nudge / a notification) the
   moment an agent goes `awaiting_response`, answerable by voice in one tap. Built on the existing
   agent-hook loop + `/api/companion/*` + the iPad CompanionBoard + the web `/companion` portal.

…and **ship the proof**: an owner-driven, air-gapped demonstration captured as committed
artifacts + screenshots + a written narrative ready to adapt for a public post.

## Principle (load-bearing) — the iPad is a full peer, never a thin client

The iPad is a powerful machine. **On-device is first-class and complete:** capture, transcription
(WhisperKit), meeting intelligence (on-device Llama / Qwen), AND **every Workbench workflow** run
locally, fully **air-gapped**. The hero scenario is the test of this phase: *flip the iPad to flight
mode, turn it on during a meeting, and it is absolute heaven* — no network, no Mac, no endpoint, full
value.

The mesh is **additive, never a dependency**:
- **Default `RUNS ON` is On-device** (`ModelPref.auto` resolves to the on-device model when nothing
  is reachable). Every workflow must execute end-to-end on the iPad alone.
- **Your Mac** adds *more* — bigger models, and the desktop's real connectors (Slack/GitHub) — when
  you choose it and it's reachable. It is opt-in, not the headline.
- **Honest degradation:** anything that *would* need the mesh (a Slack send, a step pinned to the Mac,
  the Agent Desk — which is inherently connected because the agents live on the Mac) degrades
  honestly when offline (a local draft + the egress badge; the desk simply shows "no peer"), and
  **never blocks the on-device core.**

So the rebuild is two-sided and both sides are first-class: (a) we re-craft the **desktop/web**
experience for cohesion and richness (Phase 68), and (b) the **iPad stays a complete, powerful,
air-gapped node** that also *gains* the mesh when connected. We never trade the iPad's independence
for the mesh.

## Source canon this phase is grounded in

- `docs/internal/POSITIONING.md` — "one copilot, two modes"; the egress badge (no privacy
  novels); honest, named-competitor voice. The Mesh extends the two-modes story across devices.
- `Sources/Providers/Desktop/HTTPDesktopClient.swift` — the pairing + `/api/dictation/remote` +
  `/api/companion/*` seam (the mesh backbone; do not reinvent).
- `Sources/Providers/Inference/InferenceSettings.swift` — `RuntimeMode` (on-device / homelab /
  endpoint) + `makeProvider`; the compute-fluidity seam.
- The Workbench (`MeetingCaptureApp.swift`: `NodeKind`, `ModelPref`, the `QueueHUD` /
  `RunQueueStore`) — the visual language + the transparency surface this phase makes mesh-aware.

## What already exists (grounding research, 2026-06-22)

An independent analysis of the **desktop** Python package corrected this plan: most of the mesh
machinery already ships. Build on it; do not reinvent it.

- **Dictation into your Mac through the desktop pipeline — EXISTS.** `POST /api/dictation/remote`
  (`holdspeak/web/routes/dictation/pipeline.py:299`) runs companion text through the **full** DIR-01
  pipeline (`_run_dictation_dry_run_text`) and delivers via `ctx.on_remote_dictation` →
  `_deliver_remote_dictation` (`holdspeak/runtime/dictation_capture.py:344`). Delivery is
  **`tmux send-keys -t <pane> -l <text>` + Enter** (`holdspeak/tmux_transport.py:20-41`) when a coder
  pane is known, else **`TextTyper` keystroke injection** into the focused app (`holdspeak/typer.py`,
  with `target_profile`). This is HSM-13-01/04, LAN-proven. It is deliver-on-command, never autonomous.
- **The tmux/LLM connection is the agent-hook loop.** The coder installs a Claude/Codex hook
  (`holdspeak agent-hook ingest`); on stop it reads the agent's JSONL transcript, detects a question
  (`looks_like_agent_question`), captures `$TMUX_PANE` via `tmux display-message`, and persists an
  `AgentSession` (pane, awaiting, pinned) — `holdspeak/agent_context/sessions.py` + `hooks.py`. The
  desktop targets the recently-awaiting (or pinned) session's pane. It does **not** guess the pane.
- **Companion control routes exist:** `GET /api/companion/status` (the readiness oracle: waiting
  sessions, `tmux_reply_available`, `text_injection_enabled`, `blockers`) + `POST /api/companion/
  {select,pin,dismiss,clear-stale}` (`holdspeak/web/routes/system.py`).
- **LLM seams exist (both OpenAI-compatible-capable):** meeting intel (`intel/engine.py`,
  `providers.py` — local llama-cpp OR an OpenAI-compatible client; the .43:8080 self-hosted box is
  `provider=cloud` + `meeting.intel_cloud_base_url`) and the **separate** dictation runtime
  (`Config.dictation.runtime`, `openai_compatible` backend).
- **One approval/egress contract — EXISTS.** `ActuatorProposal` + `ActuatorExecutor`'s 5-gate stack
  (status → policy → payload-parity TOCTOU → connector → audit), with Slack/GitHub/webhook/voice-macro
  connectors (`holdspeak/plugins/actuator_executor.py`, `web/routes/meetings.py` proposals/decision).
- **Two job queues exist:** the MIR plugin-run queue (`web/routes/activity/plugin_jobs.py`, DB-backed,
  status/attempts/retry) + the meeting intel queue (`holdspeak/intel_queue.py`).
- **Auth:** bearer token (`Authorization: Bearer` / `X-HoldSpeak-Token`) enforced when bound
  off-loopback (`holdspeak/web_auth.py`).

### The genuinely-new work (the delta this phase must actually build)

1. **Free-typing target for remote dictation.** `/api/dictation/remote` today targets the **waiting
   coder session**. To "dictate into any focused Mac app from the iPad," add a target option that uses
   the `TextTyper`/`target_profile` path **without** requiring an awaiting agent session (the typer
   seam already supports it). Plus the iPad flagship surface (HSM-15-01).
2. **A "run a capability on your Mac" RPC.** Capabilities (intel, dictation rewrite, actuators) are
   reachable only through their specific domain routes; there is **no** generic "run this step, return
   the result" endpoint. The mesh Workbench/runner needs one (HSM-15-02/04).
3. **One aggregated mesh inbox.** The two queues + the (meeting-scoped) proposals are **separate**.
   A single "everything in flight + everything pending approval" endpoint is new (HSM-15-03).
4. **Decouple the approval ledger from `meeting_id`.** `actuator_proposals` is meeting-scoped, so
   device-initiated (non-meeting) actions aren't in the proposals table. Generalize it so every
   cross-device action shares one approval/audit contract (HSM-15-05).

Everything else (the tmux loop, remote dictation delivery, companion selection, the actuator
contract, the LLM endpoints) is **reuse**, not new.

## Scope

- **In:** dictation-into-your-Mac as a first-class flagship mode (HSM-15-01); the Workbench
  targeting the mesh — "Your Mac" as a RUNS-ON capability target, sink nodes routing through
  the desktop's real connectors (HSM-15-02); the mesh queue — desktop jobs + approvals in the
  iPad's QueueHUD (HSM-15-03); the one mesh runner — executes a workflow locally OR dispatches
  per RUNS-ON, enforcing the per-workflow failure policy (HSM-15-04); one approval + egress
  contract across surfaces (HSM-15-05); **the Proof** — the air-gapped value demonstration +
  the launch narrative (HSM-15-06); the docs catch-up (HSM-15-07).
- **Out:** new on-device engines (Phases 1–13 own those). App Store / TestFlight logistics. A
  brand-new transport — the mesh rides the **existing** HTTP seam (`HTTPDesktopClient`); we
  extend its routes, we do not replace it. Autonomy — the mesh never acts without approval.

## Exit criteria (evidence required)

- [ ] **Dictation into your Mac** is a first-class mode on the flagship home: speak into the
      iPad, words land in the focused desktop app through the real pipeline; pairing-aware
      (unreachable Mac is a first-class state); the mic widget is the now-reactive waveform;
      egress-honest — device + LAN-proven against the real desktop server (HSM-15-01).
- [ ] **The Workbench targets the mesh** — "RUNS ON: Your Mac" runs a node's intelligence on the
      desktop, and a Slack/GitHub sink routes through the desktop's propose→approve→execute
      connector — Simulator-shot + LAN-proven (HSM-15-02).
- [ ] **The mesh queue** — the QueueHUD shows desktop jobs + pending approvals beside on-device
      jobs; a desktop actuator is approvable from the iPad; an unreachable peer is a first-class
      queue state — Simulator-shot + LAN-proven (HSM-15-03).
- [ ] **One mesh runner** — a host-tested `WorkflowRunner` executes a graph locally or dispatches
      per RUNS-ON, threading inputs, substituting `{input}`, and enforcing retry → queue → fallback
      (HSM-15-04).
- [ ] **One approval + egress contract** — desktop actuators and the mobile egress badge are one
      model; the egress scope (local / local+cloud / cloud+target) is consistent across the mesh
      (HSM-15-05).
- [ ] **The Proof** — an owner-driven, **air-gapped** session is captured: real local inference on
      owned hardware producing real value, with committed artifacts + screenshots + a written,
      post-ready narrative (HSM-15-06).
- [ ] **Docs** — the entry points (README two-modes tour, mobile docs) catch up to the mesh:
      pairing, dictation-into-your-Mac, RUNS-ON-mesh, the mesh queue, the approval contract
      (HSM-15-07).

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HSM-15-01 | Dictation, into your Mac (first-class flagship mode) | in-progress (**01a desktop delta + 01b iPad SURFACE both BUILT + Simulator-proven**; live LAN trace owner-gated) | [story-01](./story-01-dictation-into-your-mac.md) | `DictateView` (reactive waveform + push-to-talk/hands-free + read-back ticks + pairing-aware reach chip + egress badge); `sendRemoteDictation(target:.focused)`; suite **250/6/0**; `dictate-surface.png` |
| HSM-15-02 | The Workbench targets the mesh (RUNS ON: Your Mac + real connectors) | backlog | [story-02](./story-02-workbench-mesh-targets.md) | — |
| HSM-15-03 | The mesh queue (desktop jobs + approvals in the QueueHUD) | backlog | [story-03](./story-03-the-mesh-queue.md) | — |
| HSM-15-04 | One runner for the mesh (local or dispatched, policy-enforcing) | in-progress (pure runner BUILT + host-proven; **CANVAS NOW EXECUTES through it** — `PatchModel.lowerToWorkflow()` → `WorkflowRunner` on-device; nodes light + Queue HUD shows live `StepOutcome` jobs; Simulator-proven) | [story-04](./story-04-one-mesh-runner.md) | suite 250/6/0 · `scratchpad/wb-exec.png` (the Workbench running) |
| HSM-15-05 | One approval + egress contract (across surfaces) | backlog | [story-05](./story-05-one-approval-egress-contract.md) | — |
| HSM-15-08 | The Agent Desk — your live agents + the question each is asking | **built + Simulator-proven** (`AgentDeskView`/`AgentDeskCard`; waiting sorts first + pulses, tight question quote, Answer/pin/dismiss; `HS_DEMO_AGENTDESK` seed) — live `companionStatus()` poll + voice-answer are the wiring follow-up | [story-08](./story-08-the-agent-desk.md) | `apple/build/agentdesk.png`; iPad build green (runner+desk; FailurePolicy unified into RuntimeCore) |
| HSM-15-09 | Proactive agent presence — surface a waiting agent the moment it asks | **built + Simulator-proven** (`PresenceWatcher` pure rising-edge/debounce/quiet-mode, 7 host tests; HUD waiting-lane + the nudge card w/ Answer-by-voice; non-autonomous) — voice delivery reuses the desk composer (LAN proof owner-gated) | [story-09](./story-09-proactive-agent-presence.md) | 83 ProvidersTests green; `presence-hud-lane.png` |
| HSM-15-10 | The Connect surface ("Your Computer" — discovery-first pairing) | **built end-to-end + Simulator-proven** (desktop advertises `_holdspeak._tcp` + unauth `/api/mesh/info`; iPad `ConnectView` browses via `NWBrowser`, discovered list by name + reach, tap-to-pair w/ token step + manual fallback, `DictatePeerStore.adopt/forget`; `NSBonjourServices` in plist + gen assertion) — real LAN discover+pair is the owner-at-iPad proof | [story-10](./story-10-the-connect-surface.md) | 12 mesh + 2205 desktop · iPad build green · `connect-surface.png` |
| HSM-15-06 | The Proof — air-gapped value + the launch narrative | backlog | [story-06](./story-06-the-proof-and-narrative.md) | — |
| HSM-15-07 | Docs — the Mesh, end to end | backlog | [story-07](./story-07-docs.md) | — |

## Where we are

**2026-06-22 — opened.** Phase authored from the owner's ratified Mesh vision. The thesis:
HoldSpeak is a **personal intelligence mesh** — a desktop hub + mobile companions, two modes on
every surface, fluid compute, one queue, one approval contract, all private and air-gappable.
The seam already exists (`HTTPDesktopClient` pairing, `/api/dictation/remote`, `/api/companion/*`,
`RuntimeMode` A/B/C); this phase unifies it into one felt product and ships the proof.

Sequencing is deliberate: **HSM-15-01 (dictation into your Mac) leads** because it is the
most-used daily path, the smallest new surface, and it makes the mesh *felt* immediately — you
pick up the iPad, talk, and the words land on your Mac, through a model on hardware you own. The
runner (HSM-15-04) is built **once, for the mesh** (local OR dispatched per RUNS-ON), rather than
a throwaway local-only runner. The Proof (HSM-15-06) is a first-class deliverable, not a closeout
footnote: the air-gapped, owner-driven demonstration is the marketing-grade asset the owner asked
for.

**2026-06-22 (later) — grounded against the shipped desktop.** The owner flagged that the plan was
assuming surfaces that already exist. An independent analysis of the desktop Python package confirmed
it: the **tmux/LLM "answer the coder" loop, the remote-dictation delivery (`/api/dictation/remote` →
`tmux send-keys` / `TextTyper`), companion selection, the one actuator approval/egress contract, both
job queues, and the OpenAI-compatible LLM seams all already ship.** See "What already exists" above.
The phase was re-scoped to the **four genuine deltas** (free-typing remote-dictation target; a generic
"run a capability on your Mac" RPC; one aggregated in-flight + pending-approval inbox; decouple the
approval ledger from `meeting_id`) plus the iPad flagship surfaces and the Proof. Story grounding
blocks added to 15-01…05. Net: much less new code than first drafted — the mesh is mostly **wiring the
iPad into machinery that exists.**

Owner bar carried in from Phase 14: no prose in the product (tight chips, the egress badge — not
sentences); PixelLab for bespoke craft; premium/native/"oozes awesomeness"; **show it** (Simulator
shots + live on the iPad); deliver, don't checkpoint. The mesh stories add a hard rule of their
own: **the mesh never acts without your nod**, and the headline proof runs **air-gapped**. And the
standing lesson from this grounding: **read what the desktop already does before planning new mobile
work — a lot of it is already there.**
