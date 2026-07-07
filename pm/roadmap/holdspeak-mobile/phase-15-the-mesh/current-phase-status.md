# Phase 15 — The Mesh

**Status:** in-progress (opened 2026-06-22 in direct response to the owner: "I do love
your idea of the mesh… create a fucking phase that's going to be so amazing." The owner
ratified the holistic framing — HoldSpeak is not a Mac app with an iPad sidekick; it is a
**personal intelligence mesh** — and asked that this phase ALSO ship LinkedIn-worthy proof:
a senior software architect increasing his efficiency with tools + memory he paid for,
running local inference on a machine he owns that is **completely air-gapped**, and still
extracting enormous value.)

**Last updated:** 2026-07-05 (**RESUMED, SURVEY-CORRECTED — the deltas kept getting pre-paid.**
The phase's four genuinely-new deltas (named in the 2026-06-22 grounding) were re-read against
the shipped code: **15-05 is done pre-paid** (the `meeting_id` decoupling shipped as the
one-spine owner-typed proposal `origin`; the shared egress model is Phase 21's ONE
`EgressScope` grammar + two-surface trust chip; approval parity is Qlippy≡dashboard + the
iPad's `decided_by` decisions — receipts in `evidence-story-05.md`); the **"run a capability
on your Mac" RPC now exists as `POST /api/ask`** (HSM-16-04 — prompt + context in, output +
honest per-run egress out, persists nothing); the graph already **travels and runs on the hub
whole** (Phase 22) with per-node `runs_on`/`failure_policy` on the wire (22-01) and the target
pick informed by real model manifests (16-08). What is genuinely open: **the per-STEP
dispatch** — `WorkflowRunner.dispatchToMac` still THROWS `dispatchUnimplemented`, `run()`
hard-codes `.onDevice`, per-node `modelPref` is ignored at run time, and the Queue HUD's job
target label reads the app-wide `isLocal` (the 16-09 class of egress lie) — now HSM-15-02's
active build; the aggregated **mesh inbox** (15-03, still real: the hub has no single
in-flight + pending-approvals endpoint and the HUD shows no desktop lane); the **connector
sinks from a canvas run**, the **mesh source**, and the workflow-level policy (15-02's
remaining rows); and one wiring find: **`PresenceStore.startPolling` has no call site** — the
15-08/09 live-poll wiring is genuinely unwired. 15-06 (the air-gapped Proof) stays the
owner's; 15-07 docs after the builds. Earlier:
**2026-06-22 — opened.** Authored from the owner's ratified vision. The
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
| HSM-15-02 | The Workbench targets the mesh (RUNS ON: Your Mac + real connectors) | **in-progress — the HEART shipped 2026-07-05**: "Your Mac" in the node inspector (`ModelPref.desktop` + `BPRunsOn.desktop` on the wire, older hubs fold to auto — wire-safe), the runner dispatches the pinned step to the paired peer over `/api/ask`, honest `ranOn` + HUD label, IF-UNREACHABLE rides the policy. Proven sim → real local hub. Remaining: connector sinks from a run, the mesh source, workflow-level policy | [story-02](./story-02-workbench-mesh-targets.md) | slice record in the story · 2 screenshots |
| HSM-15-03 | The mesh queue (desktop jobs + approvals in the QueueHUD) | **done** (2026-07-05 — hub `GET /api/mesh/inbox` (both queues + pending proposals across origins, payload never rides) + the HUD's mesh lanes (peer-named hub jobs, approve/reject rows, unreachable = first-class blocked); proven LIVE sim → real scratch hub incl. an approve whose receipt reads `decided_by: ipad-companion`; the same commit wired `PresenceStore.startPolling` (the 15-08 finding)) | [story-03](./story-03-the-mesh-queue.md) | [evidence](./evidence-story-03.md) · 3 screenshots |
| HSM-15-04 | One runner for the mesh (local or dispatched, policy-enforcing) | **done** (2026-07-05 — the runner DISPATCHES per RUNS-ON: injected `MeshDispatch` over `POST /api/ask`, per-step targets, honest `ranOn`, no-peer rides the failure policy; proven Simulator → REAL local hub with prompt receipts; 2 latent finds fixed — HUD jobs never settled (the jobID mismatch) + the target label read the app default) | [story-04](./story-04-one-mesh-runner.md) | [evidence](./evidence-story-04.md) · `screenshots/hsm-15-02-mesh-run.png` |
| HSM-15-05 | One approval + egress contract (across surfaces) | **done** (2026-07-05, PRE-PAID: the `meeting_id` decoupling = the one-spine owner-typed proposal `origin` (locked by `test_db_actuator_origin.py`); one egress grammar = P21 `EgressScope` + two-surface trust chip; approval parity = Qlippy≡dashboard (P56) + iPad decisions (P19); air-gapped draft+badge = 17-05/16-09. Approve-from-the-HUD stays 15-03's) | [story-05](./story-05-one-approval-egress-contract.md) | [evidence](./evidence-story-05.md) |
| HSM-15-08 | The Agent Desk — your live agents + the question each is asking | **built + Simulator-proven** (`AgentDeskView`/`AgentDeskCard`; waiting sorts first + pulses, tight question quote, Answer/pin/dismiss; `HS_DEMO_AGENTDESK` seed) — **the live `companionStatus()` poll is WIRED as of the 15-03 build** (`startPolling` now called at the paired-peer call site in the app root; the survey had found it call-site-less); the device walk beat joins the owner queue | [story-08](./story-08-the-agent-desk.md) | `apple/build/agentdesk.png`; iPad build green (runner+desk; FailurePolicy unified into RuntimeCore) |
| HSM-15-09 | Proactive agent presence — surface a waiting agent the moment it asks | **built + Simulator-proven** (`PresenceWatcher` pure rising-edge/debounce/quiet-mode, 7 host tests; HUD waiting-lane + the nudge card w/ Answer-by-voice; non-autonomous) — voice delivery reuses the desk composer (LAN proof owner-gated) | [story-09](./story-09-proactive-agent-presence.md) | 83 ProvidersTests green; `presence-hud-lane.png` |
| HSM-15-10 | The Connect surface ("Your Computer" — discovery-first pairing) | **built end-to-end + Simulator-proven; 2026-07-06: the remote-pairing saga closed** (five stacked defects across TestFlight builds 3–4: the silent manual sheet, the un-bumped schema's missing `model_manifests`, two sync-wire poisons the Swift contract can't decode (`run_output` + naive `isoformat()`), and a leftover `tailscale serve` TLS interceptor on the hub port eating the app's cleartext while Safari's auto-HTTPS "proved" the network fine; build 4 = `WILL DIAL` + exact probe reason on `DioConnectCard`, ONE `PeerAddress` host rule w/ `https://` support, browse-on-open forces the LN prompt); **repo debt 1–3 paid** (schema v9 + tolerant ChangeSet/`runOutput` + honest sync-pill states) — owner's on-device green run is the remaining proof | [story-10](./story-10-the-connect-surface.md) | 12 mesh + 2205 desktop · iPad build green · sim "Synced · just now" vs the live hub · b4 VALID+attached · debt PR: hub 3199 / Swift 484 / sim build green |
| HSM-15-11 | Agents on your desktop's models (pick the Mac's model, run through it) | **built + live-proven in the sim** (2026-07-06: hub `/api/ask` manifest-bounded `model` override; `RuntimeProfile.Kind.desktop` + the ONE `callLLMTurn` dispatch across recipes/chat/chains/live-lenses; "Your desktop" picker section naming the hub's models; honest failure + one-tap on-device fallback; found+fixed: the desk `desktopClient` never sent the pairing token — every desk hub-run 401'd on a token-requiring hub) — owed: Phase-17 fidelity rider walk + the owner's cross-country run | [story-11](./story-11-agents-on-your-desktops-models.md) | ask pytest ×10 · real-metal .43 control-vs-treatment · sim→hub→llama.cpp printed card (`screenshots/15-11-desktoprun-live-proof.png`) · hub 3202 / Swift 484 |
| HSM-15-12 | The context envelope (select meetings, expand their artifacts, into the ask) | **built + real-metal hydration proven** (2026-07-06 evening: `ContextEnvelope`+`GroundingSelection` pure assembler (6 host tests) · "Ground this ask" picker on chat + run sheet, gauge live-priced, per-conversation persistence · hub `/api/ask` `grounding` refs hydration (+5 pytest, unknown ids refuse naming them) · `callLLMTurn(grounding:)` ships refs on desktop turns · KB hint string replaced by hydrated content or the honest marker · grounding rows on `RunProvenance`. Control-vs-treatment on the live hub → .43: ungrounded guesses "Mesh", grounded answers **BLUE LANTERN** from a transcript the request never shipped) — owed: the owner's cross-country phone walk | [story-12](./story-12-the-context-envelope.md) | hub 3206 · Swift 490 · 3 sim screenshots (`15-12-*.png`) · curl receipts in the story header |
| HSM-15-13 | Chat with the desktop's model (the manifest becomes a front door) | **built + live-proven** (2026-07-06 night, same session it was asked: `ModelChat` persona mapping (3 host tests) · the connect card's MODELS section off the synced manifests, blocked-not-hidden unpaired · one tap → the SAME `DioRecipeChat` pinned to `desktopProfile(model:)`, transient (no edit/delete), thread + 15-12 grounding persist per model id. Real-metal: sim paired to the LIVE hub — the chat wears the real manifest's `Qwen3.5-9B-UD-Q6_K_XL.gguf` and answers `MODEL CHAT OK` through 127.0.0.1:8765 → the .43 llama.cpp) | [story-13](./story-13-chat-with-the-desktops-model.md) | Swift 493 · 4 screenshots (`15-13-*.png`) |
| HSM-15-06 | The Proof — air-gapped value + the launch narrative | backlog | [story-06](./story-06-the-proof-and-narrative.md) | — |
| HSM-15-07 | Docs — the Mesh, end to end | backlog | [story-07](./story-07-docs.md) | — |

## Where we are

**2026-07-06 (late night) — THE MAC'S MODEL IS A PERSON YOU CAN OPEN (15-13 built + live-proven).**
The owner's third ask of the day, shipped in the same session: the connect card's new
MODELS section lists the desktop's models straight off the synced manifests (blocked,
never hidden, when unpaired), and one tap opens the EXISTING chat surface pinned to
`desktopProfile(model:)` — a transient `ModelChat` persona (RuntimeCore, host-tested):
no edit/delete, the thread persists under `modelchat:<node>:<model>`, and the 15-12
grounding picker rides free on its composer. Live proof: a sim paired to the live hub
opened a chat that titled ITSELF with the real pull's manifest name
(`Qwen3.5-9B-UD-Q6_K_XL.gguf`) and answered `MODEL CHAT OK` through
127.0.0.1:8765 → the .43 llama.cpp (`screenshots/15-13-live-run.png`). Swift **493**.

Earlier — **2026-07-06 (night) — THE ASK KNOWS YOUR RECORDS (15-12 built + real-metal hydration proven).**
The second owner ask of the day shipped the same day. One assembler:
`ContextEnvelope` (RuntimeCore, pure, host-tested) renders provenance-headed blocks
(`[MEETING: title — date]` / `[ARTIFACT: title — meeting]`), refuses past-budget
selections BEFORE the run, and `GroundingSelection` persists per CONVERSATION (the
chat keeps its grounding; the recipe's standing context stays authorship; a chain
step gets none). One split: `groundingForRun` — a desktop turn ships REFERENCES
(`/api/ask` gained `grounding: {meeting_ids, artifact_ids, expand}`; the hub
hydrates from its own store, bounds a full transcript at 12k chars with an in-block
cut marker, and refuses unknown ids naming them), every other target hydrates
client-side into `[GROUNDING]`. The picker ("Ground this ask") sits on BOTH
composers — the agent chat and the route sheet — with the ContextGauge pricing the
selection live and each meeting expanding to digest / transcript / its bound
artifacts, each independently toggleable. The KB honesty rider landed with it: the
"lean on the knowledge base" hint string is dead — hydrated member content or the
explicit `[KB: name — not hydrated on this device]` marker. Receipts: grounding rows
ride `RunProvenance`, and the hub echoes what it hydrated. Real-metal
control-vs-treatment on the restarted live hub (its engine = the .43 llama.cpp,
Qwen3.5-9B): the ungrounded ask GUESSES ("Mesh"); the grounded-by-reference ask
answers **BLUE LANTERN** — a codename living only in a transcript the request never
shipped; the ghost id refuses with `unknown_ids`. (First run also proved WHY the
rigs matter: the pre-restart hub silently ignored the new param — a stale process,
caught only because the proof was live.) 15-13 (chat with the desktop's model)
scaffolded from the owner's third ask. Suites: hub **3206**, Swift **490**, sim
build green, 3 screenshots. Owed: the owner's cross-country walk.

Earlier — **2026-07-06 (evening) — AGENTS RUN ON YOUR DESKTOP'S MODELS (15-11 built + live-proven).**
The owner's morning ask shipped the same day. Hub half: `POST /api/ask` gained a
manifest-bounded `model` override — the allow-list is what the hub can actually run
(its own engine + its profiles' models; another node's manifest row refuses loudly
with the runnable set). Proven real-metal on the restarted Denver hub: the pinned
Qwen3.5-9B on 192.168.1.43 answered, the unknown model 400'd. Swift half:
`RuntimeProfile.Kind.desktop` (schema + contract), and the new `callLLMTurn` seam —
the ONE dispatch every run path already funnels through (recipes, chat, chains, live
lenses, weave) — sends desktop-profile turns over the paired hub's ask route, pinned
to `profile.model`, and returns the hub's per-run egress so the printed card's badge
is REPORTED, never inferred. The Runs-on picker gained a "Your desktop" section naming
the hub's models from the synced manifests (blocked row when unpaired — never
disappears); a failed desktop turn wears the mesh vocabulary with a one-tap **Run on
this device** fallback. The `desktoprun` proof rig ran a REAL recipe sim→hub→llama.cpp:
`screenshots/15-11-desktoprun-live-proof.png` shows the answer on the printed card
wearing `Cloud · 192.168.1.43`. The rig found two real defects: the desk's
`desktopClient` NEVER sent the pairing token (every desk hub-run since 15-02 would
401 on a token-requiring hub — fixed via `DesktopPeer` + `PeerAddress`), and the sim
pairing injection must target the app CONTAINER defaults domain (the user-domain
write silently no-ops once the app owns container prefs). Ops: the Denver hub now runs
PLAIN on :8765 (hublog retired, DB stamped v9 with a fresh backup); stale
`tailscale serve` fronts on :8443/:34999 still owed (daemon CLI unreachable this
session). Owed on the story: the Phase-17 fidelity rider walk + the owner's
cross-country TestFlight run. Suites: hub **3202**, Swift **484**, validator ALL PASS,
sim build green.

Earlier — **2026-07-06 (later) — THE SAGA'S REPO DEBT IS PAID (15-10 riders 1–3, the mesh-repo-debt PR).**
The three code riders the saga left behind shipped together: **schema v9**
(`SCHEMA_VERSION = 9` routes every v8-stamped DB through backup-then-apply so
`model_manifests` lands; regression pin `test_v8_db_gains_model_manifests_via_the_bump` —
no other v8 install can hit the pull-500 again), **a tolerant ChangeSet wire**
(`ArtifactType.runOutput` known in enum + wire schema, and `ChangeSet.init(from:)` decodes
per-record: a novel type drops that one record into a visible `undecodedRecords` count
instead of failing the whole set — `ChangeSetToleranceTests`, plus the SyncEngine wire test
re-pinned to skip-and-count), and **honest sync-pill states**
(`DeskSyncDriver.Outcome.failure` distinguishes unauthorized / hubError(code) /
contractMismatch / unreachable; the pill says "Token rejected" / "Hub error 500" /
"Hub reply unreadable" — only a dead network path may say "Offline · queued", and "Synced"
admits "· n skipped"). Suites: hub **3199 passed**, Swift package **484/9/0**, contract
validator ALL PASS, iPad sim build green. Debt row 4 (classic-home connect cleanup) stays
open; next builds are 15-11 (agents on your desktop's models) then 15-12 (the context
envelope).

Earlier — **2026-07-06 — THE REMOTE-PAIRING SAGA CLOSED (15-10): the mesh works from another city.**
The owner, phone in NYC and hub in Denver, couldn't pair the TestFlight app while Safari on
the same phone reached the identical hub — the desk pill lied "Offline · queued" through
FIVE stacked, mutually-masking defects (full autopsy in story-10): the classic-home sheet
that never dialed (build 3 fixed the WRONG surface — the desk front door uses
`DioConnectCard`), the hub DB missing `model_manifests` (additive DDL, no v9 bump → v8 DBs
no-op the schema and `/api/sync/pull` 500s), a sync wire the Swift contract cannot decode
(`artifact_type: "run_output"` absent from the `ArtifactType` enum + `_iso()` emitting
naive microsecond timestamps Foundation's `.iso8601` rejects — `_iso` fixed this commit,
proven by compiling the real Contracts sources into a decode harness against the live pull
JSON), and the killer: a **leftover `tailscale serve` TLS-over-TCP interceptor on the hub
port** from the build-2 investigation — Safari auto-upgrades to HTTPS so it handshook fine,
while the app's honest cleartext died inside tailscaled with zero packets, zero prompts,
across reinstalls and reboots. **Build 4** (uploaded, VALID, attached) hardens the real
surface: `DioConnectCard` wears the literal `WILL DIAL` URL + the exact probe reason, the
new `PeerAddress` helper is the ONE host rule at every dial site and speaks `https://`
(a `tailscale serve` TLS front is now a first-class door), and opening the card browses
Bonjour so iOS surfaces the Local Network prompt. Riders queued: schema v9 bump, `runOutput`
+ unknown-tolerant enum decoding, honest sync-pill error states (500/401/decode/no-network
currently all wear "Offline · queued") — **all three paid later this day, see above**.
Remaining beat: the owner's on-device green run.

Earlier — **2026-07-05 (evening) — THE MESH QUEUE IS REAL: the hub's work and the hub's asks ride
the pill in your hand, and approving there IS approving on the desktop.** 15-03 closed:
the hub gained its one window (`GET /api/mesh/inbox` — the deferred intel queue + the
MIR plugin queue in flight, plus every `proposed` actuator proposal across meeting AND
desk origins via the new global pending-lister; the payload never rides), and the
QueueHUD gained the mesh lanes: hub jobs origin-labeled with the peer's name, proposals
as approve/reject rows in the HUD's own vocabulary, the pill wearing "N on <peer>" +
"N to approve", and an unreachable peer as a FIRST-CLASS state (last-known rows degrade
to `blocked · peer unreachable · auto-resumes`; never an error spinner). Proven live:
the Simulator polled a REAL scratch hub, rendered its real jobs + both proposals, and an
approve from the HUD transitioned the desk-origin row on the hub with
`decided_by: ipad-companion` through the real guarded executor (no webhook configured →
an honest `failed`, never a fake "sent"). One wire find died before shipping: a
successful desk decision would have thrown `malformed` (the shared decision envelope
requires a meeting id a desk row doesn't have) — the desk decode is now tolerant. The
same commit **wired `PresenceStore.startPolling`** (the survey's 15-08 finding) at the
one paired-peer call site. Suites: hub **2486**, Swift **479/9/0**, api-surface at 241
routes, 3 committed screenshots. Remaining buildable: 15-02's leftover rows (connector
sinks from a run / mesh source / workflow-level policy) + 15-07 docs; the owner's queue:
15-06 (the air-gapped Proof) + the cabled-iPad beats (dispatch, inbox, presence, 15-01's
live trace).

Earlier the same day — **the mesh dispatch is REAL: a Workbench node pinned to "Your Mac"
runs on your Mac.** The survey's active slice shipped the same day. The node inspector's
RUNS ON grew "Your Mac" (with the IF-UNREACHABLE row doing exactly what its hints
promise), `BPRunsOn.desktop` joined the wire (older hubs fold it to auto — same
semantics, wire-safe by construction; the hub preserves the pin in its run trail), and
the runner's stubbed seam became an injected `MeshDispatch` riding the hub's ask route:
the step's fully-resolved prompt goes over `POST /api/ask`, the output threads back into
the walk, nothing persists on the hub (a step result is intermediate), and
`StepOutcome.ranOn` + the HUD job label state where each step ACTUALLY ran (a fallback
reports on-device — it never left). No paired peer reads exactly like an unreachable
endpoint: retry → queue / fall back on-device / skip. **15-04 closed with this slice**
(its survey-set condition was precisely "dispatches per RUNS-ON"). Proven end to end:
the Simulator's pinned Decisions step landed its prompt as a receipt on a REAL local hub
and the job settled **Done · Karol's Mac**. Two latent finds died on the way: canvas-run
HUD jobs NEVER settled (the inserted job's self-generated id never matched the looked-up
one), and the job target label read the app-wide default for every step. Suites: Swift
**476/9/0** (9 new dispatch tests + 3 client tests), hub unit green (+ the `desktop`
target lock), api-surface regenerated. Remaining in 15-02: connector sinks from a run,
the mesh source, workflow-level policy. The cabled-iPad LAN beat joins the owner queue.

Earlier the same day — **resumed, survey-corrected.** Two weeks of other phases quietly paid this
one's bills: the proposal ledger decoupling (one-spine), the one egress grammar (Phase 21),
whole-graph travel + hub runs with `runs_on` on the wire (Phase 22), manifest-informed
target naming (16-08), and — as of this morning — the generic "run a capability on your
Mac" RPC itself (`POST /api/ask`, HSM-16-04). The survey records 15-05 done pre-paid with
receipts and re-scopes 15-02 to its genuinely-open heart: **the per-step dispatch**. The
runner's `dispatchToMac` seam still throws, `run()` hard-codes `.onDevice`, a node pinned
in the inspector is honoured on the wire but ignored at run time, and the Queue HUD labels
every job with the app-wide default instead of where the step actually ran — the same
class of egress lie 16-09 killed on the desk. That slice builds next, wiring the runner to
the paired peer over `/api/ask` with the IF-UNREACHABLE policy (retry → queue / fall back
on-device / skip) doing exactly what its inspector hints promise. Also filed: the hub
still has no aggregated in-flight + pending-approvals endpoint (15-03 stays real), and
`PresenceStore.startPolling` has no call site (the 15-08/09 live wiring is unwired).

Earlier — **2026-06-22 — opened.** Phase authored from the owner's ratified Mesh vision. The thesis:
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
