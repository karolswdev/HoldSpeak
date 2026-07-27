# OpenWorker → HoldSpeak integration feasibility

**Status:** study, 2026-07-26. Not a plan; a decision aid.
**Read this if:** you are deciding which OpenWorker ideas deserve HoldSpeak
stories, and how they must be reshaped to survive the Constitution.

## Sources studied

| Repo | Revision | What was read |
|---|---|---|
| `andrewyng/openworker` | `main` @ `db93d75` (shallow clone, 2026-07-26; single squashed public commit, no design history) | `coworker/` (engine, server, permissions, risk, inbox, connectors, MCP, automation, memory, providers), `surfaces/gui/` (full React app), `stt/` (Rust whisper.cpp crate), `packaging/`, `ui-mocks/` |
| HoldSpeak | `main` @ `8e2ea2f5` | Constitution, POSITIONING, DESIGN_SYSTEM, kernel RFC, phases 104–105 status, `holdspeak/` and `web/src/` inventories |

OpenWorker's `docs/` ships almost nothing; its real design canon is
`ui-mocks/redesign.html` plus dated inline comments (`§21–§42`, `UX-015…`,
"owner call 2026-07-14"). Where this doc cites `§n` that is a reference into
their mock, quoted from their code comments.

---

## 1. Executive summary

**Verdict: highly feasible, and mostly as *pattern transplants*, not code
imports.** The two products share the same spine (local Python agent server +
web UI over HTTP/WS, consent-gated tools, local secrets), so almost every
OpenWorker interaction pattern has a natural HoldSpeak home. The visual skin
does not transfer and does not need to: OpenWorker's own token layer (~25 CSS
vars driving light/dark) is proof that a palette swap is cheap, and our
Workbench 2.0 program keeps its own geometry, bevels, and icon discipline.

The three findings that matter most:

1. **OpenWorker's consent UX is the best in class we have seen, and it maps
   one-to-one onto Article V.** Humanized one-line approval titles,
   proposal-shaped previews, a five-value decision vocabulary
   (`once / deny / always_tool / always_command / always_task`), and parked
   asks that survive restarts and resolve from any surface. Our SystemShade
   and the Phase 106 kernel should adopt this dialect wholesale, minus the
   prose (Article III/VII: badges, not sentences).
2. **Their autonomy model is the missing half of Cadence.** Scheduled tasks
   run real agent turns, park their approvals in a cross-session Inbox when
   unattended, land as continuable transcript sessions, and carry standing
   grants with visible revocation. Cadence today nudges; this is how it
   *works*.
3. **MCP and descriptor-driven connectors are our two biggest feature gaps,
   and OpenWorker is a working reference for both.** Layered MCP config
   paste-compatible with Claude Desktop, fail-closed approval defaults, ~40
   connector descriptors with 159 typed tool defs, per-tool toggles, and a
   three-layer enablement hierarchy (account → persona → session).

What we must *not* take: the chat-centric app frame (Article I — the Desk is
the surface), modal scrims (Article VII), prose explanations in chrome, the
cloud OAuth broker as a dependency, and any default posture of unattended
"full access".

---

## 2. The two systems at a glance

| Axis | OpenWorker | HoldSpeak today | Transplant? |
|---|---|---|---|
| App frame | Chat-centric SPA: sidebar, glass topbar, chat column, right rail | The Desk: GL world of primitives, windows, menu bar | **No** — patterns move, frame stays |
| Agent loop | Owned `TurnEngine` (aisuite for schemas only), 150-iter cap | Personas/recipes chat, coders via tmux steering, MIR/DIR pipelines | Patterns: yes (§5.7) |
| Consent | Risk classes + permission modes + parked Inbox | Actuators, operation policy, fail-closed coder Gate, kernel (active) | **Yes — mutual fit is the headline** |
| Server | FastAPI + WS, sidecar token, Origin allowlist, caps | FastAPI + `/ws`, 346 routes, loopback + token | Hardening deltas: yes (§5.10) |
| Connectors | ~40 descriptors, two-way (Slack inbound), MCP | 5 local packs, read-mostly, outbound Slack webhook | Descriptors + MCP: yes (§5.4, §5.5) |
| Automations | Cron tasks → real runs → transcript sessions | Cadence: collect/score/nudge, Telegram surface | **Yes — the upgrade path** (§5.6) |
| Memory | Scoped store (global/workspace/session) + prompt block | KBs, grounding, corrections, projections; no agent memory store | Scoped store: yes (§5.8) |
| STT | whisper.cpp record-then-transcribe, in-composer mic | mlx-whisper/faster-whisper, hotkey + wake word, streaming | No — we are ahead; borrow provisioning UX only (§5.9) |
| Shell/update | Tauri 2 supervises PyInstaller sidecar; minisign updater | Python package; native innards are Cocoa/PyObjC | Lifecycle patterns: yes; Tauri itself: no (§5.11) |
| Skin | Flat, cobalt accent, Tailwind + 25 CSS vars | Signal tokens, Workbench 2.0 geometry, pixel icons | No — ours stays; theirs proves reskin cost (§4.9) |

---

## 3. UI/UX learnings (the primary lens)

Each item: what OpenWorker does → why it is good → its DeskOS shape → the
Constitution check → effort (S ≤ 1 story, M ≈ 2–4 stories, L = phase-sized).

### 3.1 The approval dialect — adopt wholesale, minus prose

**What.** Approval requests dock above the composer, not in scrollback
(`surfaces/gui/src/App.tsx:1545`, `Composer.tsx:340`). Each card carries:
a humanized one-line title (`humanize.ts`: "Write **report.md**"), a
plain-words scope note ("stays on this Mac" vs "leaves this Mac → Slack",
external gets a warm border), a **proposal-shaped preview** built from tool
args — the file content that *would* be written, clamped to 5 lines/420
chars with "show all N lines", the outbound message quote, the exact shell
command — and the decision vocabulary
`once / deny / always_tool (session) / always_command (this shell command) / always_task (standing grant on the automation)`
(`types.ts:34`, `ApprovalCard.tsx`). Two visual weights: routine workspace
writes collapse to a one-line compact row with inline "preview ▾";
consequential/external actions get the full card. Resolved cards fold back
into the transcript as compact `✓ approved / ✕ declined` chips. Design rule
in their comments: "**one decision, one dialect**" — the parked Inbox item
wears the exact same rendering as the live card.

**Why.** The user never approves an abstraction; they approve a preview of
the artifact. Grant tiers convert repeated friction into durable, *visible*
trust. Two weights keep routine consent cheap without hiding consequence.

**DeskOS shape.** This *is* the SystemShade
(`web/src/desk/components/SystemShade.tsx`, `gate.ts`), upgraded. In
Workbench 2.0 terms the card is a **requester**: chunky beveled panel, the
egress badge (local / local+cloud / cloud) in the title bar where OpenWorker
puts its prose scope note, preview body in a mono well, decision gadgets as
buttons. The four request kinds (tool, directory grant, plan, free-text
question) become the shade's four body layouts. Resolved receipts already
exist as session receipts; the `✓/✕` chip folding is the transcript
treatment.

**Constitution.** Article V — direct fit (executed == previewed is already
our law via `actuator_authority.py` payload hashes; their preview-from-args
is the same idea at the UI layer). Article III — **conflict resolved**: they
use a prose sentence for egress; we must use the badge, per canon ("disclosed
by a badge at the point of decision, never prose"). Article VII — their card
copy is calm enough to survive, but titles come from our honest formatters
(`deSnake`/`presentValue`), not a prose generator.

**Effort: M.** Pieces exist (shade, badges, receipts); the work is the
dialect, previews, and grant-tier plumbing.

### 3.2 The parked-asks Inbox — the missing Desk window

**What.** Unattended mode is a per-session toggle ("Send approvals to Inbox —
the agent keeps working"). Parked approvals/questions land in a cross-session
**Inbox** (`InboxView.tsx`, `inbox.py` server-side): kind filter chips,
per-persona chips, an originating-session chip per item, first-responder-wins
resolution keyed by `tool_call_id` (idempotent, awaitable **across process
restarts**), an answer-in-context card docked above the composer of the
originating session, optional mirror to a Slack channel as Approve/Deny
buttons whose replies resolve the item in-app, and an **Unrouted dead-letter
list** — "nothing vanishes silently". Attention counts bubble session →
persona → a footer Inbox chip that stays hidden until the first parked item
("sticky unlock").

**Why.** This is what makes autonomy safe: the agent runs, consequences
queue, and the queue is a first-class surface with a dead-letter net. The
restart-survival property is the difference between a demo and a tool.

**DeskOS shape.** A new Desk window on the Desk (Article I), fed by the
kernel's `decide`/`events` APIs — Phase 106's broker is *literally* the
parking primitive (`read/submit/decide/events` + hash-chained journal). The
needs-you badge already exists in the Workbench 2.0 program: the Inbox
drawer/icon wears the parked count; per-window attention marks map from
originating sessions. Mirror-to-Slack rides our existing outbound webhook
actuator when it grows buttons. "Sticky unlock" = an icon that materializes
on first use, which is pure Workbench behavior.

**Constitution.** Article V — the consent spine, extended in time. Article
XI — this is the broker's first real userland client alongside PR
follow-through; sequencing it with the kernel avoids a second parking
implementation.

**Effort: M on top of the kernel** (the broker does the hard part); L if
attempted before it.

### 3.3 Turn groups and streaming calm — adopt for persona/coder transcripts

**What.** A whole user→answer span collapses into one disclosure:
"**Running 12 steps…** · *live line truncated from the stream*" with
humanized step rows inside, raw args/result on hover, and header summaries
for "2 declined · 3 hidden by your filters" (`Transcript.tsx:84–299`).
Streaming text passes a **40-word promotion gate** (`streamGate.ts`,
owner-tuned "~1–2 s of stream") that decides: answer bubble with ▍ cursor,
quiet narration line, or hold (spinner only). Reasoning models get a
collapsed "Thinking…" disclosure. Interrupted turns flush partial text into
a durable item so live view and reload agree. Retry appears only on a
retriable *tail* error.

**Why.** Long agent runs stay legible without hiding the receipts; the
promotion gate kills the "wall of half-sentences" problem; reload-agreement
is an honesty property (Article VI).

**DeskOS shape.** PersonaChat and the coder session views
(`PersonaChat.tsx`, `SessionPullout.tsx`) adopt the group disclosure and
promotion gate verbatim in behavior, reskinned to the surface kit. Step rows
reuse the humanized-title formatter from §3.1.

**Constitution.** Article VI (honest by construction) — reload-agreement
and declined/hidden counts are receipts. Article VII — groups keep chrome
quiet. No conflicts.

**Effort: S–M.**

### 3.4 Standing grants, visibly revocable — adopt

**What.** Auto-allowed tool calls in a transcript wear a teal "auto-allowed"
chip; each automation's detail page lists "**Allowed without asking**" rules
with per-rule **Revoke** (`ScheduledView.tsx:442–469`). Grants are exact:
`tool → exact target` (e.g. send_message → #release), external-risk only.

**Why.** Consent that cannot be inspected is not consent; the chip makes
silence visible at the exact place it happened.

**DeskOS shape.** TrustWindow (`TrustWindow.tsx`) gains the standing-grant
ledger per automation/coder; transcript chips in the views from §3.3.
Backend: grants already rhyme with `operation_policy.py` scoped grants —
the steal is the *exact-target* constraint and the UI surfacing, not the
concept.

**Effort: S.**

### 3.5 Onboarding and provider setup — adopt the gallery pattern

**What.** A fixed-size 3-step wizard (600×560, header/footer never move):
(1) provider gallery of brand cards each wearing state (✓ Connected · used
2h ago / Not set up / No key needed), key form with Test = verify + save +
auto-return, per-provider "Create one at … ↗" deep links, keyless "Detect"
for Ollama; (2) tools page with benefit-framed rows and zero-layout-shift
state flips; (3) done page with two CTAs that *teach by landing*. The same
`ProviderCards/ProviderForm` components are shared with Settings ▸ Models so
onboarding and settings cannot drift. Two-tap skip with an honest warning.
Composer shows a "No model ⚠" chip that routes to Settings **and preserves
the draft**.

**Why.** Fixed geometry + shared components = the wizard can never rot
behind settings; per-card state turns setup into a dashboard.

**DeskOS shape.** SetupCore (`pages/cores/SetupCore.tsx`) is our wizard;
Runs on (`ProfilesCore.tsx`) is our model surface. Adopt: the gallery card
states, Test-with-auto-return, shared components between the two, and the
draft-preserving "no destination" chip. As Desk windows, not modals
(Article VII).

**Effort: S–M.**

### 3.6 Voice input state invariants — adopt as law

**What.** `ui-mocks/voice-input-composer-states.html` pins four states with
written invariants: **the waveform means listening, not inference** (driven
by real mic RMS at ~10 Hz — their first decorative bars "read as fake");
transcribing is intentionally quiet; **the transcript always lands as an
editable draft, nothing auto-sends**; Escape cancels mid-recording. The
settings page gates the mic behind a compatibility card, a SHA-verified
model download with progress, and a **microphone test** whose passing
transcript flips `test_passed`.

**Why.** Every invariant is already our law in spirit (Article IV: voice
arms, it does not fire); theirs is the crispest written form of it, plus the
"real RMS or nothing" detail and the test-to-unlock gate.

**DeskOS shape.** RecordOrb and the dictation cockpit already behave this
way; adopt the invariants verbatim into `ICON-DISCIPLINE`-style UI law
(candidates: DESIGN_SYSTEM or the DictationCore spec), and steal the
mic-test-unlocks-mic gate for Setup.

**Effort: S.**

### 3.7 Automations UI — adopt with Cadence

**What.** List ⇄ detail: human schedule, next run, run count, last status,
**▶ Run now** (opens a live session with the prompt pre-sent), standing-grant
list, and **run history where each row opens the run's full transcript as a
continuable session**. A quickstart grid of six templates with connector
readiness dots (brand = connected, grayscale = needs connecting) and lazy
sign-in inside the configure card. Unseen-run badges clear on view via a
window event. A single, deliberate toast exists app-wide: run-started, 5 s
drain bar, "View run ›".

**Why.** "Runs are sessions" collapses the mental model — there is no
second artifact type to learn. Readiness dots make templates self-diagnosing.

**DeskOS shape.** This is the Cadence window (`CadenceCore.tsx`) grown from
nudge board to run board; runs-as-sessions map onto our meetings/invocations
(`db/invocations`) rather than a new store. Template readiness = the same
badge vocabulary as object state-at-rest (Workbench 2.0 program: objects
carry live state, only when a named field feeds it).

**Effort: M** (paired with §5.6 backend work).

### 3.8 Connector management grammar — adopt the structure

**What.** Connectors live under one list (search; Connected group first
with live health chips; Available folded at 8) with **bespoke detail pages
for the important five and a generic fallback so every connector navigates
from day one**. Pre-connect pages state access in plain bullets ("Keys and
tokens are stored only on this computer") and show the tool list behind a
disclosure with "asks first" tags. One add-connection modal with a
**One click | Manual** pill. Per-tool enablement checkboxes with
`name · kind · asks approval` metadata (`ManageTabs.tsx:725–763`). Two-way
connectors add: allow-list chips, **parked senders** with
Allow & deliver / Allow only / Dismiss (the gateway keeps what they said),
and per-connector listening lists.

**Why.** The bespoke-five + generic-rest split is how a 40-connector catalog
stays shippable; per-tool levers are consent at the right granularity;
parked senders mean inbound trust never drops data.

**DeskOS shape.** A Connectors surface *window* (Article I) using the
surface kit's rows/sections; "asks first" tag = our egress/consent badges;
parked senders = the same Inbox dead-letter discipline as §3.2.

**Effort: M** for the UI once backend descriptors exist (§5.5).

### 3.9 Small honest-details worth lifting

- Fixed-height error lines so failures never reflow forms.
- "Loading models…" disabled chip instead of a stale baked-in list.
- Hover meta (copy + timestamp) in a zero-height strip — no layout shift;
  "Copied" only after the clipboard write lands.
- Jump-to-latest pill with follow-only-while-at-bottom and
  programmatic-scroll discrimination.
- Two-step delete confirms (we have `ConfirmVerb`; keep parity).
- Update banner as a **prompt, never silent**, bytes pre-fetched so restart
  is instant, "Later" per version.
- Sidebar quick-switch (⌘1–9) and command palette over sessions — our desk
  has Exposé/MRU; palette search over windows+objects is the analog.
- Hermetic Playwright e2e (~46 specs against a mocked server) as executable
  UX documentation — complements our Puppeteer shots.

### 3.10 Reskin cost, measured from their side

Their tailwind.config states the app "mirrors ui-mocks/redesign.html" —
**mock-parity is their method**, and it works. Palette lives in ~25 CSS vars
already theme-switched (dark = `html[data-theme]` overrides): a Workbench
pastel would be an hour. The real cost would be geometry: radii and
hairlines are scattered across ~80 files with no elevation abstraction, so
bevels would need a token sweep (days, mechanical). **For us this is
confirmatory, not aspirational:** our three-layer tokens
(`design-tokens.json` → `tokens.css` + `tokens.gen.ts`, gates that forbid
raw color/z/ms literals) are already the stricter system, and our GL world
adds a dimension they do not have. Nothing to import here — but their
mock-parity discipline is a good argument for keeping `gallery/` +
ComponentsCore wired as the living mock.

---

## 4. Feature/backend learnings

### 4.1 Risk classes — adopt into the kernel census

`coworker/risk.py`: `READ` (always allowed), `WRITE_LOCAL` (path-scoped to
writable roots + mode-gated), `EXEC` (mode-gated), `EXTERNAL` (off-machine
side effects — the Inbox hook). Classification cascade: user-local override
store → by-name base table → tool's `requires_approval` → default READ.

**Fit.** Phase 106's effect census (40 sites pinned by test, 4
chokepoint-covered) needs exactly this taxonomy to name what each site *is*.
Adopting their four classes (they are already isomorphic to our
actuator/policy vocabulary) gives the census a shared language, and the
override-store pattern is a clean escape valve.

**Effort: S** as a taxonomy adoption; the census itself is already charted.

### 4.2 Permission modes and shell allowlist hygiene — adopt details

Modes: `discuss`/`plan` (read-only), `interactive` (default), `auto`,
`custom` (config `auto_allow`). Two concrete steals inside:
(1) **shell allowlist entries reject any command containing metacharacters**
(`; & | > < \` $() ( \n`) from prefix auto-run (`permissions.py:17–25`) —
prefix matching without this is a hole every allowlist implementation
eventually falls into;
(2) writable-roots as a **shared mutable ACL object** passed by reference to
permission engine, file tools, and context injector, so a mid-session folder
grant takes effect everywhere instantly.
Modes map cleanly onto our `secure | normal | yolo` control modes
(`operation_policy.py`); theirs add the per-session dimension, which the
kernel's scoped grants should absorb.

**Effort: S.**

### 4.3 Four request kinds, one parking mechanism — adopt as the broker's decide model

Tool approvals, directory grants, plan approvals, and structured questions
are *all* the same parked Inbox item keyed by `tool_call_id`: awaited by the
engine, resolvable once, first-responder-wins, durable across restarts, and
renderable by any surface. The engine blocks on `inbox.wait` after emitting
the event; automation runs get an approver pre-seeded from the task's
standing grants.

**Fit.** This is a validated shape for the kernel's `decide` call: one
parking primitive, four payloads. Designing the broker to this shape now
(before the census grows) is the cheapest high-value adoption in this
document.

**Effort: S–M**, folded into kernel stories.

### 4.4 MCP client — the biggest net-new feature, with a reference implementation

`coworker/mcp/`: standard `mcpServers` JSON, **paste-compatible with Claude
Desktop/Cursor**, layered global (`~/.config/coworker/mcp.json`) +
per-workspace (`.coworker/mcp.json`, workspace wins); `${VAR}` secret
indirection; per-server `enabled`, `include/exclude_tools`,
`requires_approval` **default true (fail-closed)**, optional OAuth 2.1 + PKCE
+ dynamic client registration with tokens in the SecretStore and interactive
flows only from explicit connect actions, never mid-turn. Tools bridge as
`mcp__<server>__<tool>` with schemas verbatim, and connector-backed servers
obey the session's effective-connector set.

**Fit.** HoldSpeak has **no MCP anywhere in product code** (only the PMO
tooling has one). MCP is how the agent ecosystem brings tools to us instead
of us writing 40 connectors. The config-compat decision is the key steal:
users paste what they already have. All MCP tools land in
EXEC/WRITE_LOCAL/EXTERNAL risk classes and ride §4.3 parking — constitutional
by construction.

**Effort: L (one phase).** Recommend a dedicated phase after the kernel
lands, so MCP enters through the broker rather than beside it.

### 4.5 Connector descriptors + two-way discipline — adopt the architecture

One descriptor schema carries auth kind (`bot_token|socket_app|app_password|oauth|token|none`), UI fields, setup instructions, a credential validator, and flags (`managed`, `two_way`, `channels`); 159 `ConnectorToolDef` entries pin per-tool kind (read/write), approval, and `target_arg` for exact-target grants. Effective enablement is three-layered: account-connected → persona-default (seeded from manifest `recommends`) → per-session override. Inbound: **empty allowlist = nobody**; unauthorized senders are *parked* (message retained) for one-tap allow-and-deliver; unrouted inbound lands in a dead-letter list.

**Fit.** Our connector SDK (`connector_sdk.py`, five read-mostly packs) has
the right consent shape but not the descriptor breadth, the tool-def
metadata, or any inbound. The descriptor pattern upgrades the SDK without
breaking it; inbound Slack (mentions → sessions, thread replies with
standing exact-target grants so replies never re-prompt) is the flagship
two-way use case and the natural first descriptor with `two_way: true`.

**Effort: M for descriptors + per-tool metadata; L for first-class inbound
(Slack).**

### 4.6 Automations as real runs — the Cadence upgrade

Cron via `croniter` (timezone-aware, "local" = machine clock), 30 s tick,
**run-once-catch-up** for missed schedules, **skip-on-overlap**, runs spawn
as independent tasks so a parked approval never stalls the loop, artifacts =
files created since start, transcripts land as `__run__` sessions that are
hidden from lists but fully continuable, and `create_scheduled_task` is
itself an approval-gated tool (the agent writes the cron from natural
language; its requested `permissions` become standing scoped grants on
consent). Scheduler honesty: the UI states runs only happen while the server
is up.

**Fit.** Cadence today is collect → score → nudge with policy bounds — the
right consent posture, but it never *does the work*. This model turns due
loops into real runs without touching the consent spine: parked approvals +
standing grants carry it. The catch-up/skip semantics and "server must be
up" honesty line are exactly our register.

**Effort: M–L** depending on how much of Cadence's scoring UI is retained.

### 4.7 TurnEngine mechanics — adopt the hard-won details

- Interrupts checkpoint mid-stream, mid-tool, mid-approval; pending tool
  calls always receive a **synthetic tool-error result so history never
  orphans** — replay-safety for free.
- **Durable resume**: a turn parked at a prompt survives process restart.
- Mid-turn **steering messages** and mid-session **model switching** with
  persisted notices and capability-degradation warnings.
- Blocking provider streams bridged into the async loop via producer thread
  + `asyncio.Queue`; low-risk tool calls in one turn run concurrently,
  writes strictly sequential.
- Per-call **context scrubbing**: display-only sidecars (`source`, `_display`,
  `ts`, `reasoning`) and `notice` roles are stripped before every provider
  call; PDFs/images re-adapted to the *current* model's capabilities each
  call; secrets never enter context.
- An ephemeral `<system-context>` block appended to the *last user message*
  per turn (mode reminders, live directory list), never persisted.

**Fit.** Our agent surfaces (persona chat, coders, future kernel-driven
runs) will hit every one of these; the synthetic-error-on-interrupt and
scrubbing rules are cheap to adopt now and expensive to retrofit. Steering
maps onto `coder_steering.py`; model switching onto profiles.

**Effort: S–M** per item.

### 4.8 Scoped agent memory — fill the gap

`MemoryStore` ABC with scopes `global | workspace | session`, agent tools
`remember / memory_update / memory_forget`, injection as a "Known memories"
prompt block with ids, and written rules (save durable preferences *with the
why*, absolute dates, revise rather than duplicate).

**Fit.** We have KBs, grounding, correction memory, and projections — all
*topic* memory. We have no *agent preference/fact* memory; personas re-ask.
A scoped store is small, honest (it's just rows), and complements grounding
rather than competing with it.

**Effort: S–M.**

### 4.9 STT sidecar — do not adopt; borrow provisioning UX only

Their `ocw-stt` crate (whisper.cpp via whisper-rs, cpal owner thread,
SHA-256-verified model download, RMS `input_level()`, memory-only audio,
record-then-transcribe, no streaming/VAD/hotkey) is strictly behind our
stack (mlx-whisper/faster-whisper, hotkey + wake word, live levels in
RecordOrb). Borrow: the **verified-download + mic-test-unlocks-mic**
provisioning flow (§3.6) and, if a Rust capture path is ever wanted for
Linux, the owner-thread cpal pattern.

**Effort: S** for the provisioning UX.

### 4.10 Loopback hardening — adopt the deltas

Their server adds what ours lacks: a browser-**Origin allowlist** on HTTP
*and* WS (closes "any website can drive your loopback agent"), WS auth via
token in `sec-websocket-protocol`, 16 MiB frame cap, 30 msgs/10 s WS rate
limit, 200k-char message and 15 MB attachment caps, CORS pinned to the same
allowlist.

**Fit.** We already refuse non-loopback binds without a token
(`web_auth.py`); adding the Origin gate and caps is a small, high-value
hardening of `web_server.py` that matches Article VI's "honest by
construction" posture toward the threat model.

**Effort: S.**

### 4.11 Sidecar lifecycle and updates — patterns, not framework

Their Tauri shell: picks a free port, mints an in-memory token, spawns the
PyInstaller sidecar with `EXIT_WITH_PARENT` + parent-PID watch (orphan-proof),
rotates logs, single-instance, close-to-tray, LaunchAgent autostart,
keep-awake so schedulers fire, and minisign-signed `latest.json` with
background pre-download + prompt-to-restart.

**Fit.** Phase 101 (native innards) is Cocoa/PyObjC — **do not switch
frameworks**; adopt the lifecycle checklist (orphan-proofing, log rotation,
keep-awake, prompt-not-silent updates with pre-download) into the native
shell's requirements verbatim.

**Effort: S** as requirements adoption.

---

## 5. What NOT to take, and why

| OpenWorker choice | Why it dies at our border |
|---|---|
| Chat-centric app frame (sidebar + chat + rail as *the* app) | Article I: the Desk is the operating surface; features never own the frame. Their patterns move into windows; the frame does not move. |
| Modal scrims (FolderGate, WorkspaceTrustPrompt, Onboarding overlay) | Article VII: no modals. Gates become Desk windows or shade states. |
| Prose explanations in chrome ("leaves this Mac → Slack" sentences) | Article III: egress is a badge, never prose. The *information* transfers; the prose does not. |
| Cloud OAuth broker as the happy path | Local-first pillar. Their manual-key path proves the broker is optional; we ship manual keys first and treat any broker as future work with an egress badge. |
| `auto` / full-access as a default posture | Article V: consent is the spine. Unattended exists (as it does for us via control modes) but only with parked asks + standing grants visible. |
| Tauri | Phase 101 committed to Cocoa/PyObjC native innards. We take the lifecycle requirements, not the framework. |
| Their STT | Ours is ahead (hotkey, wake word, streaming-capable, 99 languages). |
| Their visual skin (flat cobalt, Tailwind utilities) | The Workbench 2.0 program stands. Their token layer merely confirms reskin economics. |

---

## 6. Constitutional tension log (honest conflicts and resolutions)

1. **"One decision, one dialect" vs. quiet chrome (Article VII).** Their
   approval cards are wordier than our chrome allows. Resolution: keep the
   *structure* (title, preview, grants), express egress as the badge, and
   let the honest formatters write titles. Dialect survives; prose does not.
2. **Autonomy vs. consent (Article V).** OpenWorker comfortably runs
   unattended with an Inbox; our canon says reach never outruns consent.
   Resolution: unattended is a *mode*, parked asks are the mechanism, and
   the kernel journal makes every grant auditable. Autonomy becomes a
   consent *schedule*, not a consent waiver — which is exactly how their
   standing grants work (`tool → exact target`, revocable).
3. **Chat-first vs. Desk-first (Articles I–II).** Their session is the
   product; our sessions are windows over primitives. Resolution: every
   adopted pattern is recast as a primitive affordance or window (Inbox
   window, run transcripts as invocations, connector surface window). The
   no-exit lock test (`test_desk_no_exit_guard.py`) is the enforcement
   backstop.
4. **Broker-first sequencing.** Several adoptions (Inbox, grants, MCP
   gating) would duplicate the kernel if built beside it. Resolution:
   sequence §3.2/§4.3/§4.4 through the broker APIs as they land; the UI
   dialect work (§3.1, §3.3–§3.5) is independent and can start immediately.

---

## 7. Proposed sequencing

| # | Item | Lands in | Size |
|---|---|---|---|
| 1 | Approval dialect upgrade for SystemShade (humanized titles, proposal previews, grant tiers, two weights, resolved chips) | Phase 104/105 workbench stream | M |
| 2 | Risk-class taxonomy + request-kind model adopted into kernel design | Phase 106 (now, while the broker is on paper) | S |
| 3 | Turn groups + stream promotion gate in persona/coder views | any UI story | S–M |
| 4 | Standing-grant ledger in TrustWindow + auto-allowed chips | with #1 | S |
| 5 | Loopback hardening (Origin allowlist, WS caps) | any hardening story | S |
| 6 | Setup gallery + Test-with-auto-return + mic-test gate | Setup/Runs-on refresh | S–M |
| 7 | Parked-asks Inbox window on the kernel decide/events APIs | Phase 106 userland (after broker) | M |
| 8 | Cadence → automations (runs-as-sessions, catch-up/skip, Run now) | follow-on phase | M–L |
| 9 | MCP client phase (config-compat, fail-closed, per-tool levers) | dedicated phase post-kernel | L |
| 10 | Connector descriptors + per-tool metadata; first two-way connector (Slack inbound) | dedicated phase | L |
| 11 | Scoped agent memory store | with or after #9 | S–M |
| 12 | Native-shell lifecycle checklist (orphan-proof, pre-download updates) | Phase 101 requirements | S |

Quick wins (#2, #5, #12, plus #3 if a UI story is open) are independently
shippable. #1 is the highest-visible-value UI work. #9 is the biggest
feature bet and is deliberately sequenced after the kernel so MCP tools are
born inside the consent chokepoint.

## 8. Risks

- **Rescope creep.** Each adopted pattern must enter as a story-sized slice;
  the full set above is roughly three phases of work. Do not bundle.
- **Divergence drift.** We are importing *patterns*, not code (their engine
  is async/aisuite-shaped; ours is a synchronous mixin runtime with tmux
  steering). Every adoption needs a local owner who re-expresses it against
  our runtime rather than transliterating.
- **Consent dilution.** Grant tiers and unattended mode are the two places
  where a careless port quietly weakens Article V. Mitigation: exact-target
  grants only, revocation always visible, kernel journal on every grant.
- **OpenWorker is a moving target** (open beta, squashed public history).
  Re-pull before implementing any item; this study pins `db93d75`.
- **License** is MIT — pattern adoption is clean; direct code lifts need
  attribution.

## 9. Bottom line

Feasible and desirable. OpenWorker has independently built, and in two areas
(consent UX dialect, unattended autonomy with parking) *bettered*, the
things HoldSpeak's Constitution demands. The integration path is not a merge
but a translation: their chat-app patterns become Desk windows, their prose
becomes badges, their inbox becomes the kernel's first userland client, and
their connector/MCP machinery fills our two clearest feature gaps. Start
with the approval dialect (#1) and the kernel taxonomy (#2); let MCP (#9)
follow the kernel.

---

## Appendix A. Key source references (OpenWorker @ db93d75)

- Approvals: `surfaces/gui/src/components/ApprovalCard.tsx`, `DirectoryRequestCard.tsx`, `PlanCard.tsx`, `InboxItemCard.tsx`, `surfaces/gui/src/types.ts:34`, `surfaces/gui/src/humanize.ts`
- Inbox/unattended: `coworker/inbox.py`, `coworker/unattended.py`, `coworker/unrouted.py`, `coworker/interactions.py`, `surfaces/gui/src/components/InboxView.tsx`, `InboxConfigure.tsx`
- Risk/permissions: `coworker/risk.py`, `coworker/permissions.py`, `coworker/roots.py`, `coworker/workspace_trust.py`, `docs/config.example.toml`
- Engine: `coworker/engine.py`, `coworker/events.py`, `coworker/agent.py`, `coworker/server/manager.py`
- Server/auth: `coworker/server/app.py` (Origin allowlist `:32–64`, WS `:1459`), `coworker/server/run.py`
- Connectors: `coworker/connectors/descriptors.py`, `tool_defs.py`, `integration_tools.py`, `gateway.py`, `adapters.py`, `relay_client.py`, `parked.py`
- MCP: `coworker/mcp/config.py`, `client.py`, `tools.py`, `oauth.py`
- Automations: `coworker/automation/{models,store,scheduler,tools}.py`, `coworker/selfwake.py`, `surfaces/gui/src/components/ScheduledView.tsx`, `AutomationQuickstart.tsx`
- Memory: `coworker/memory/{base,sqlite_store,tools}.py`
- Providers: `coworker/providers/{registry,router,matrix,capabilities}.py`
- Voice UX: `ui-mocks/voice-input-composer-states.html`, `ui-mocks/voice-input-settings.html`, `stt/src/lib.rs`, `surfaces/gui/src/components/Composer.tsx:287–515`
- Onboarding/settings: `surfaces/gui/src/components/Onboarding.tsx`, `SettingsView.tsx`, `providers/ProviderSetup.tsx`
- Transcript/stream: `surfaces/gui/src/components/Transcript.tsx`, `surfaces/gui/src/streamGate.ts`
- Shell/packaging: `surfaces/gui/src-tauri/src/lib.rs`, `packaging/`

## Appendix B. HoldSpeak anchor points (@ 8e2ea2f5)

- Consent: `holdspeak/plugins/actuators.py`, `actuator_executor.py`, `actuator_authority.py`, `operation_policy.py`, `coder_gate.py`, `docs/AUTHORITY.md`
- Kernel: `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md`, `pm/roadmap/holdspeak/phase-106-the-kernel/`
- Desk UI: `web/src/desk/` (`SystemShade.tsx`, `TrustWindow.tsx`, `PersonaChat.tsx`, `verbRegistry.ts`, `dropMatrix.ts`), `web/src/pages/cores/`, `web/design-tokens.json`, `web/ICON-DISCIPLINE.md`
- Cadence: `holdspeak/cadence/`, `web/src/pages/cores/CadenceCore.tsx`
- Connectors: `holdspeak/connector_sdk.py`, `holdspeak/connector_packs/`, `docs/CONNECTOR_DEVELOPMENT.md`, `holdspeak/slack_export.py`
- Server: `holdspeak/web_server.py`, `holdspeak/web_auth.py`, `docs/API_SURFACE.md`
- Agents: `holdspeak/db/primitives.py` (recipes), `web/routes/primitives/recipes.py`, `holdspeak/coder_steering.py`, `holdspeak/agent_capabilities.py`

## See also

- [CONSTITUTION.md](CONSTITUTION.md) — the articles every adoption above is measured against.
- [POSITIONING.md](POSITIONING.md) — pillars and canonical names.
- [PLAN_KERNEL_OPERATION_BROKER.md](PLAN_KERNEL_OPERATION_BROKER.md) — the broker this study routes half its findings through.
- [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) — why the skin stays ours.
