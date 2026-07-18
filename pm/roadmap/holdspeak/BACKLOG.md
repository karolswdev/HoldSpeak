# HoldSpeak — Backlog (living candidate phases)

The parking lot so good ideas do not get lost between phases. Each entry is a
**candidate future phase**, not committed work. When one is picked up it graduates
into its own `phase-NN-*/` folder with an AGENT-BRIEF + stories, and its row here
flips to "scaffolded" then "shipped".

Sourced from the Phase-48 strategic review (`.guru_meditation.md`, an untracked
scratch file, captured here so it survives) and the Phase-48 deferred decisions.

**Last updated:** 2026-07-07 late (candidate **U** SCAFFOLDED — B1 opens as
[phase-86 — The Delivery Belt (read-only)](./phase-86-delivery-belt/): the
AI-Headquarters floor, registry-shaped from day one. The B0 substrate turned
out to already exist upstream (delivery-workbench v1.12: `dw state`/`sessions`/
`events`, the stamped gate, the workbench belt, the Telegram interface); what
was missing was a reader that survives THIS repo's 86 phases of dialect —
shipped upstream the same day as delivery-workbench phase 16 ("the flagship
tree", PR #2): 397 spurious `dw check` errors → 31 real desyncs, which
HS-86-01 now consumes. Earlier the same day: candidate **U** FILED — the Delivery Belt: delivery-workbench as a desk-native conveyor-belt surface on DeskOS + the web desk, rendering from receipts only; owner direction quoted in the section. Earlier the same day: candidate **T** SHIPPED: [phase-85 — The Mesh Edge (CLOSED 5/5, same day)](./phase-85-the-mesh-edge/) — a meshNode profile relays a run through the hub to the node hosting the provider; pull worker + liveness from its polling, fast named refusal, egress scope `mesh`, proven live end to end with a second-process worker; the Apple worker + consent toggle is the HSM follow-up. Earlier the same day: candidate **S** SHIPPED: the remaining hub slice closed as [phase-84 — One Runtime (CLOSED 5/5, same day)](./phase-84-one-runtime/) — both hub pipelines on the profile layer, pickers instead of typed endpoints, one egress derivation, the "Runtime profiles" doctor check, proven live on `.43`. Earlier the same day: the code survey found S's majority already shipped under other flags — the RuntimeProfile contract + `SyncKind.profile` + per-agent `profile_id` + the `/profiles` and Apple authoring surfaces landed with HSM Phase 24 / the mesh / Phase 83. Prior: candidate **Q** shipped as [phase-58](./phase-58-front-door/) (CLOSED 6/6) — the story is a decision now. Earlier today: **P** shipped as [phase-57](./phase-57-transcript-import/) (CLOSED 5/5) — transcripts import as real meetings. Earlier today: **J** shipped as [phase-56](./phase-56-qlippy/) (CLOSED 7/7), **G** absorbed-shipped with it; **K** is next per the agreed sequence. Prior: post-Phase-53 strategic review: candidate **D** promoted
to its own phase and scaffolded as [phase-54](./phase-54-dictation-frontend-decomposition/)
— the dictation frontend is now 6,101 coupled lines and lost the density invariant five
phases running. New candidates **I** (meeting import + faceted history search), **J**
(Qlippy presence enhancer, absorbing **G**), **K** (languages + spoken-symbol
dictionary), and parked rows **L–O** added from the review. The agreed sequence is
**54 (D) → I → J → K**, with the hardware day closing Phases 25/24 whenever in-person
access returns, then Phase 15. Prior: candidate **F** shipped as Phase 53; **B** as
Phase 52 (with a scoped slice of **E**); **H** as Phase 51. Created at Phase 48 close.)

## Why not one mega-phase

Tempting, but the repo's cadence is one coherent phase -> one PR -> evidence per
story -> merge on green. A single phase bundling a release gate, two features, and
a refactor has no single thesis, makes a giant long-lived branch, and never all
goes green at once. So: keep every idea alive here, ship them as focused phases in
sequence. This file is the "all of them" container; the phases are how they land.

## Candidate phases

| # | Candidate | Type | Source | Signal |
|---|---|---|---|---|
| A | Meeting aftercare ("close the loop") | feature | review bet #5 | **shipped → [phase-49](./phase-49-meeting-aftercare/) (CLOSED 6/6)** |
| B | Voice macros / command grammar | feature | review bet #2; deferred from P48 | **shipped → [phase-52](./phase-52-voice-macros/) (CLOSED 7/7)** (a voice command launcher; with a scoped slice of E) |
| C | Release-readiness gate (schema policy + 1.0) | release | review "Trouble" #5; deferred from P48 | **shipped → [phase-50](./phase-50-release-readiness/) (CLOSED 7/7)** |
| D | Frontend density paydown (dictation page) | debt | review "Trouble" #4; P48 standing invariant | **shipped → [phase-54](./phase-54-dictation-frontend-decomposition/) (CLOSED 6/6)** (6,101 lines → largest file 576, guard-locked; two latent bugs fixed) |
| E | `WebRuntime` / `web_server` decomposition (+ `meeting_session.py`) | debt | review "Trouble" #1 | **shipped → [phase-63](./phase-63-backend-decomposition/) (CLOSED 6/6)** (web_runtime 2,635 → 555 over eight mixins; meeting_session 1,674 → a package, core 795; verbatim to one line per story; guard-locked; the live closeout caught + fixed TWO pre-existing production bugs — meeting start broken since Phase 60 and a process-fatal transcriber-construction race); watch item: routes/meetings.py (1,525) |
| F | Local activity as pre-briefing fuel | feature | review bet #6 | **shipped → [phase-53](./phase-53-activity-prebriefing/) (CLOSED 7/7)** (source-cited dismissible nudges + "Dictate with this" closes the loop, proven on a live LLM) |
| G | Privacy visible at decision points | feature | review bet #7 | **absorbed-shipped → [phase-56](./phase-56-qlippy/)** (the three privacy answers verbatim on every actionable card, doc-locked) |
| H | Public-docs hygiene (strip roadmap vocab from user-facing docs) | release/debt | this conversation (post-P50 release polish) | **shipped → [phase-51](./phase-51-public-docs-hygiene/) (CLOSED 5/5)** |
| I | Meeting import ("bring your archive") + faceted history search | feature | post-P53 strategic review | **shipped → [phase-55](./phase-55-meeting-import/) (CLOSED 6/6)** (proven on real metal: real Whisper + real intel on `.43`) |
| J | Qlippy, the presence enhancer (absorbs G) | feature/delight | post-P53 review + [proposal](./proposals/qlippy-presence-enhancer.md) | **shipped → [phase-56](./phase-56-qlippy/) (CLOSED 7/7)** (dock + cards on real broadcasts; native HUD proven on real Linux metal; two latent presence bugs fixed) |
| K | Speak the world's languages + spoken-symbol dictionary | feature | post-P53 strategic review | **shipped → [phase-59](./phase-59-languages/) (CLOSED 4/4)** (99 languages, one knob, auto byte-identical; the spoken-symbol dictionary; proven on real German speech) |
| L | Export connectors (Notion / Slack / Docs) on the connector-pack framework | feature | post-P53 strategic review | **scoped by the owner to one easy connector** ("Export Connectors are fine…, but let's just choose an easy one") → **Slack incoming webhook, shipped → [phase-61](./phase-61-send-to-slack/) (CLOSED 4/4)** (Send to Slack on the aftercare digest + follow-up draft; propose→approve→the real gated POST, proven against a real local receiver byte-equal to the preview); Notion/Docs stay parked |
| M | Dictation preview-before-commit (review before it types) | feature | post-P53 strategic review | **scaffolded → [phase-75](./phase-75-preview-before-type/)** (2026-07-02; the P60 arms-not-types seam generalized to hold-key dictation, opt-in) |
| N | Windows port | strategic | post-P53 review; `CODEX_IDEAS.md` | **rejected by the owner** ("Absolutely not. Not by me. If someone wants it, they will port it.") — community contributions welcome; not roadmap work |
| O | Wake word ("local + private" positioning) | strategic | post-P53 strategic review | **shipped → [phase-60](./phase-60-wake-word/) (CLOSED 6/6)** (arms-not-types with the preview default; 0 false accepts in 57 ordinary utterances measured; two latent production crashes fixed: GGML lldb auto-attach + the process-fatal cross-thread MLX call) |
| P | Transcript import (`.vtt`/`.srt`/`.txt` → real meetings) | feature | user direction, post-P56 conversation | **shipped → [phase-57](./phase-57-transcript-import/) (CLOSED 5/5)** (real speakers + timestamps from the file; proven on `.43` intel; recording path untouched) |
| Q | The Front Door (positioning + user-facing docs revision) | release/community | user direction, post-P57 conversation | **shipped → [phase-58](./phase-58-front-door/) (CLOSED 6/6)** (positioning canon + README pitch + named comparisons + the voice guard) |

### A. Meeting aftercare ("close the loop") — shipped as Phase 49 (CLOSED 6/6)
The meeting side has plugins + artifacts; the next value is follow-through, not
more artifact types. "What changed since last meeting?", "what did we decide?",
"what is still open for me?", "draft the follow-up", "turn accepted actions into
issues", "show me the transcript moment that justifies this action." A beautiful
artifact that never changes the user's next action is decoration.
*Lands on:* the meeting/history surface + the actuator system (P37/P38) for
"actions -> issues".

### B. Voice macros / command grammar — shipped as Phase 52 (CLOSED 7/7, voice command launcher + scoped E slice)
Originally framed as a deterministic text-transform layer inside dictation. The user
re-envisioned it (2026-06-08) as a **voice command launcher**: map a spoken keyword to
a real system action (open a URL, launch an app, run a shell command, type a snippet)
in the web UI; speaking the keyword fires the action instead of typing. Deterministic
and inspectable, not LLM magic. Scaffolded as [phase-52](./phase-52-voice-macros/),
which **reuses the actuator guarded executor** (Phase 37/38) with new local connectors
rather than reinventing execution, and pairs the feature with a scoped slice of **E**
(carve the dispatch seam out of the `web_runtime` god-object). Safety model (user's
call): a configured macro is auto-approved (configuring is consent), off by default,
deterministic and bounded by a per-macro permission manifest, every fire audited.

### C. Release-readiness gate — shipped as Phase 50 (CLOSED 7/7)
The DB is intentionally `SCHEMA_VERSION = 1`, greenfield, **not release-stable**.
Before a tagged/PyPI release, define and ship the policy: supported config/DB
versions, whether destructive migration is ever allowed, backup/export before
upgrade, and what `doctor` reports on unexpected schema state. This is the bet
that actually lets the open-source push *ship* publicly.

### D. Frontend density paydown — shipped as Phase 54 (CLOSED 6/6)
`dictation.astro` (3,134 lines) and `dictation-app.js` (2,967 lines) grew every recent
phase (the standing page-density invariant lost five rounds running: P40, P45, P47,
P48, P53). Promoted from "ride along with the next dictation feature" to its own phase:
6,101 coupled lines is now the thing that makes every future dictation phase slower and
riskier. Scaffolded as [phase-54](./phase-54-dictation-frontend-decomposition/): section
partials + behavior modules, behavior-preserving (tests unmodified, screenshot-verified
per tab), locked by a density guard. Defines the frontend decomposition pattern
(`history.astro` / `index.astro` are the follow-up candidates).

### E. `WebRuntime` / `web_server` decomposition — partial slice in flight (Phase 52)
The review flags `WebRuntime` as "the next central chip under thermal load" after
the DB decomposition (P31) and route split (P26/P34). A structural phase if it
keeps absorbing responsibility. [Phase 52](./phase-52-voice-macros/) carves the
**dictation-execution slice** (the inline `_maybe_run_dictation_pipeline`
orchestration, currently inside the 2,341-line `web_runtime.py`) out into a testable
module, because that is the seam the voice-macro feature lands on. The rest of the
god-object (hotkey/device/meeting/activity) stays a watch item; full E is still its
own future phase if it keeps absorbing responsibility. *Added 2026-06-11:*
`meeting_session.py` (1,659 lines, mixing recording / transcription / intel /
diarization / persistence) has the identical disease and belongs to the same future
phase — it is the un-flagged sibling.

### F. Local activity as pre-briefing fuel — shipped as Phase 53 (CLOSED 7/7)
Turn the abstract browser/activity layer into concrete, dismissible, source-cited
nudges: "here is what you touched since last time" before a meeting; "want to
dictate a reply with this GitHub issue as context?" Ambient without being creepy.
Shipped as [phase-53](./phase-53-activity-prebriefing/): a small reader over the
source-cited activity records that already exist (no new watcher), gated by the
existing activity privacy toggle, read-only (it surfaces and offers, never acts),
every nudge citing its source, one action feeding the selected record into dictation.
The "Dictate with this" loop is closed end to end and proven on a live LLM (the `.43`
Qwen3.5-9B-Q6 endpoint): a server-side one-shot selection pin reaches the dictation
runner, and the project-rewriter grounds the rewrite in the selected record — a
control vs. treatment dogfood shows the selection demonstrably changes the model output.

### G. Privacy visible at decision points — absorbed-shipped with J (Phase 56)
Every place that could use a model, connector, actuator, device, or activity
source answers three plain-language questions: what data is used, does anything
leave this machine, what control do I have right now. A delight feature for this
category. *2026-06-11:* absorbed into candidate **J** — the Qlippy card is exactly
the per-decision surface where those three answers belong (an actuator-approval card
that names what data is used and what egresses *is* G, with a face). Shipped with J as Phase 56: every actionable
card answers the three questions verbatim, locked by a doc-drift test.

### H. Public-docs hygiene — shipped as Phase 51 (CLOSED 5/5)
Net-new, surfaced in the post-Phase-50 between-phases conversation. The release gate
is down and strangers now install from the public repo, but the deeper user/operator
guides still narrate the product by its build history: "Phase 9 shipped the
connectors", "Periodic tick (HS-17-05)", "the HS-19 closeout", "the current
roadmap". That roadmap vocabulary means nothing to a new user and reads as
half-finished. Strip it from user-facing docs, rewrite phase-relative claims into
product-tense, keep legitimate product nouns (`actuator`) and named specs
(`MIR-01`/`DIR-01`), and lock the clean state with a doc-drift guard (scoped to
user-facing docs, never the internal corpus) plus a codified `DOCS_STYLE.md` rule.
Docs-and-test only, behavior-preserving. *Lands on:* `docs/*.md` +
`tests/unit/test_doc_drift_guard.py`. Cheap and release-facing; the natural polish
after the release gate.

### I. Meeting import ("bring your archive") + faceted history search — shipped as Phase 55 (CLOSED 6/6)
The single highest-ROI feature gap from the post-P53 review: meeting intelligence is
live-capture-only. There is no "import this recording" path anywhere (verified:
`MeetingRecorder` only handles live audio; no import in CLI or web). An import flow
(audio file → Whisper → MIR → the 14 plugins → `/history` with aftercare) reuses the
entire existing pipeline and turns meeting intelligence retroactive — users have
archives. Pairs naturally with **faceted history search** (date / speaker / topic /
action-status; today `/history` has a single text box), because import is what makes
the archive big enough to need it.
*Lands on:* the meeting capture seam + `/history`.

### J. Qlippy, the presence enhancer (absorbs G) — shipped as Phase 56 (CLOSED 7/7)
Give the presence layer a face and a voice: an ambient Qlippy dock reflecting runtime
state, and a sliding card that makes the two least-visible high-stakes moments —
actuator approval and the learning loop — actionable in the moment, without stealing
focus. The full RFC lives at [`proposals/qlippy-presence-enhancer.md`](./proposals/qlippy-presence-enhancer.md)
(grounded in the real seams: the `/ws` broadcast, `RuntimeActivityTracker`, existing
REST decision routes; asset pack already built). Absorbs **G**: every actionable card
answers the three privacy questions (what data, does anything leave, what control).
Opt-in, off by default, never acts on its own — the card is a faster path to the same
approval as the dashboard.
*Lands on:* the presence layer (P41/P43) + the actuator flow (P37/P38) + the learning
loop (P48).

### K. Speak the world's languages + spoken-symbol dictionary — shipped as Phase 59 (CLOSED 4/4)
Confirmed absent: no language config, no Whisper language param, no per-session
override — yet Whisper supports ~99 languages, so this is mostly one settings knob,
pipeline plumbing, and honest docs. The cheapest reach-expansion available. Rider in
the same thesis ("the input layer adapts to you"): a **custom spoken-symbol
dictionary** ("tilde" → `~`, "arrow" → `→`) — the punctuation table is hardcoded
today, and personal vocabulary is classic daily-driver value.
*Lands on:* settings + the transcription path + the punctuation layer.

### L. Export connectors — owner-scoped to Slack; scaffolded as Phase 61
"Meeting notes land in Notion" is the most-requested shape of this product category.
The connector-pack + actuator framework is proven; these are new write connectors
behind the existing permission-manifest gate. Parked until the queue above clears.

### M. Dictation preview-before-commit — parked
A "show me what you're about to type, edit, confirm" mode for high-stakes targets
(emails, shell). Today the pipeline types immediately. Small, safety-flavored.

### N. Windows port — rejected by the owner (community port welcome)
The largest reach unlock (voice-typing demand is Windows-heavy); weeks of OS-level
work (hotkey, synthetic typing, audio capture). Already noted in `CODEX_IDEAS.md`.
A commitment, not a phase rider — park until deliberately chosen.

### O. Wake word — shipped as Phase 60 (CLOSED 6/6)
Table-stakes in the category, and on-brand only if local + private. High
false-positive risk; needs an always-listening pipeline done carefully. Park until
the product wants hands-free as a thesis.

## Sequencing note

**Agreed sequence (2026-06-11, user-picked):** **54 (D) → I → J → K.** Pay the
dictation-page debt before any feature touches it again, then alternate a meeting-side
bet (I), a presence bet (J, absorbing G), then the cheap reach unlock (K). The
hardware day closes Phases 25 (HS-25-07) and 24 (HS-24-03/04/05) whenever in-person
access returns; Phase 15 opens after Phase 25 closes. **E** stays a watch item that
graduates if `web_runtime.py` / `meeting_session.py` keep absorbing responsibility;
**L–O** are parked until deliberately chosen.

The original (pre-2026-06-11) note for the record: no fixed order; **C** was the
release unlock; **D** could ride along with a dictation-side phase; **B** paired with
a scoped slice of **E** was the strongest product bet. All three shipped that way.

---
### P. Transcript import — shipped as Phase 57 (CLOSED 5/5)
Most meeting tools export a transcript, not audio; the user has transcripts
("I often have transcripts, rarely do I have recordings"). Upload `.vtt`/`.srt`/`.txt`
and get a real meeting through the exact Phase-55 import pipeline — real cue
timestamps + multi-speaker labels when the file carries them (a genuine upgrade
over single-label audio import), honest synthetic ordering for plain text. The
recording upload stays untouched (explicit user constraint).
*Lands on:* the Phase-55 import engine/route/UI seams; everything downstream of
`TranscriptSegment`s is already format-agnostic.

---
### Q. The Front Door — shipped as Phase 58 (CLOSED 6/6)
Decide what HoldSpeak's story IS and tell it everywhere: a positioning canon
(the user fixed the angle: "one copilot, two modes", pitched to developers,
with named honest comparisons), README rewritten as the pitch, every
user-facing guide re-framed with why-ledes + canonical feature names + the
humanizer voice (and the em-dash cleanup the pre-P55 corpus never had), and
a voice drift guard. The pitch stays as honest as the product.
*Lands on:* the Phase-51 docs hygiene lineage + the per-phase docs-story culture.

---
### R. Core AI provider (mobile / Apple on-device, iOS 27) — PARKED (toolchain-blocked)
Apple shipped **Core AI** (the iOS/macOS 27 on-device inference runtime) + the open
`apple/coreai-models` repo (HF→`.aimodel` export recipes + a Swift runtime) + the
**Foundation Models** `LanguageModel`/`LanguageModelExecutor` protocol that lets a custom
model plug into `LanguageModelSession` exactly like Apple's system model. This is the durable
answer to the llama.cpp-xcframework treadmill: Apple owns the runtime + a maintained catalog
(Gemma 3, Qwen2.5/3, Qwen3-MoE, Mistral, Mixtral, GPT-OSS), with ANE acceleration.

**The play (NOT a rewrite):** add `CoreAIProvider: ILLMProvider` as a new Mode behind the
existing seam, gated `@available(iOS 27)` + `#if canImport(CoreAI)`, wrapping
`CoreAILanguageModel`/`LanguageModelSession`. llama.cpp/GGUF stays the path for iOS 17–26;
Core AI is additive for 27+. Optionally route the app boundary through `LanguageModelSession`
so Apple-system / PCC / cloud / Core AI all sit behind one protocol.

**Why parked (do not start until cleared):**
- **Toolchain:** needs Xcode 27 + iOS 27 SDK. We're on Xcode 26.5 / iOS 26.5 — `CoreAI.framework`
  is not in our SDK (only `FoundationModels.framework`). Cannot compile/verify until installed.
- **Different artifact pipeline:** Core AI runs Mac-exported `.aimodel` bundles, NOT GGUF — so the
  in-app HF GGUF downloader feeds llama.cpp, not Core AI. Core AI needs its own `.aimodel`
  distribution story (bundle or host exported assets).
- **Beta risk:** `CoreAI.framework` is device-SDK-only (needs `canImport` guards), `AIModelCache`
  cache-honoring bugs, and a reported Gemma-4-12B MPSGraph scratch-heap overflow on macOS 27 beta.
  Not accepting PRs.

*Lands on:* the existing `ILLMProvider` seam (Contracts/RuntimeCore depend on the protocol, not the
engine) + the per-device model policy. Owner action gates the start: install Xcode 27 / iOS 27.

---
### S. Runtime / connectivity profiles (cross-surface, pre-GA) — SHIPPED (the arc completed by [phase-84 — One Runtime, CLOSED 5/5](./phase-84-one-runtime/))

**Reconciliation (2026-07-07):** when this row was picked up, the code survey
found the design below largely built — it shipped incrementally without this
row being updated. The map: the `RuntimeProfile` contract
(`ProfileRecord`, `profile.schema.json` shape-only with the key-never-syncs
invariant, `SyncKind.profile` on hub + Swift) and the hub CRUD
(`/api/profiles`) landed with **HSM Phase 24**; per-agent assignment
(`RecipeRecord.profile_id`, honored by recipe chat/workflows, pickable in the
desk editor) with **Phase 24 + the mesh**; the web authoring surface
(`/profiles`, HSM-24-05) and the Apple Basic/Advanced surface on the mobile
track; the context gauge reading the picked profile's window and the models
front door with **Phase 83**. Keys resolve hub-side from
`HOLDSPEAK_PROFILE_<ID>_KEY` env vars (the desktop analog of the Keychain
rule — never on the wire or in the browser). What never adopted the layer:
the hub's OWN two pipelines — meeting intel (`intel_cloud_*`) and dictation
(`openai_compatible_*`) still hand-type the same endpoint shape in parallel.
That remaining slice shipped as **[phase-84 — One Runtime (CLOSED 5/5,
2026-07-07, one day)](./phase-84-one-runtime/)**: both hub pipelines resolve
through the profile layer (`intel_profile_id`, `dictation.runtime.profile_id`,
one `_apply_runtime_profile` rule), the settings sections author by picking
(raw endpoint inputs gone from the UI), one egress derivation feeds badges +
doctor, and the "Runtime profiles" doctor check names per-pipeline
resolution — proven by a six-beat live walk on the real hub → `.43` (one
profile authored once drove an agent chat, a meeting-intel reroute, and a
dictation rewrite). The legacy config fields stay as the documented fallback
shape (deliberate; see the phase final summary).

The original entry, for the record:

---
### T. The Mesh Edge (run where the node is) — **SHIPPED** as [phase-85 (CLOSED 5/5, same day)](./phase-85-the-mesh-edge/) (2026-07-07)

**Shipped:** the hub relay queue + pull worker (`holdspeak mesh serve` —
running it is the consent), the meshNode profile kind mirrored three ways,
liveness on every surface with fast named refusal, egress scope `mesh`,
and the six-beat live walk (agent chat / meeting intel / dictation all
executed on the second-process node, worker log as proof). The per-device
Apple worker + consent toggle is the HSM track's follow-up, recorded in
the phase's final-summary.

Owner direction (2026-07-07, post-84 conversation): *"if a provider is
available on a mesh device, why can't we ask for the request to go through
that mesh edge? That way we use powerful models without any friction on
synchronizing."* The generalization of the shipped device→hub relay
(HSM-15-13, the iPad chatting with the desktop's model): make ANY node's
providers callable from ANY surface. A profile that only one device can host
(its on-device model) or reach (its network, its Keychain key) serves the
whole mesh — the KEY and the model never move; the REQUEST goes to where
they live. This strengthens the key rule rather than bending it.

**The substrate that already exists:** per-node capability rows
(`ModelManifestRecord`, availability-only), the RuntimeProfile layer +
`_apply_runtime_profile` (Phase 84's one resolver), `endpoint_egress` (one
badge constructor), the pull-queue precedent (the coder-companion queue —
devices are mesh CLIENTS; an iPhone cannot be dialed into), and the
`ILLMProvider` seam on the Apple side.

**The hard constraint (named honestly):** transport topology. Mesh devices
sleep, background, and sit behind NAT — so "route through the edge" means
relay-through-hub with a device-side pull worker, and availability is
honest-but-soft: a node's provider is runnable only while its session is
live. Pickers must show LIVENESS, not existence; runs against a sleeping
node must refuse fast, never hang.

**Shape:** a mesh-node profile kind (node + model) resolving through the
Phase-84 seams; a hub relay queue (enqueue → the node's worker pulls →
executes on its local provider → returns; TTL + fast refusal); egress scope
`mesh` naming the node (a run that leaves this machine for YOUR device is
neither `local` nor `cloud` — say so); doctor liveness; a per-device
"serve my models to the mesh" consent toggle, off by default.

*Lands on:* the profile layer (Phase 84), the sync/manifest contract
(HSM-16-08), the companion queue pattern, the Apple `ILLMProvider` seam.
Today the app conflates "where intelligence runs" into ONE global choice (`InferenceConfigStore`:
mode = local | endpoint, a single endpoint URL/model/key). Owner's call (pre-GA): split it.

- **Basic configuration** = today's experience, reframed: pick ONE active profile ("Run on: [This
  iPhone ▾]"). Zero new concepts for the casual user.
- **Advanced configuration** = a LIST of named **runtime profiles** (e.g. on-device Qwen3-4B; an
  OpenRouter endpoint + key; a Claude endpoint + key; a LAN box) AND **per-agent assignment** so
  agent A runs local, agent B on OpenRouter, agent C on Claude.

**The model — `RuntimeProfile`** (a reusable connectivity target):
`{ id, name, kind: .onDevice | .openAICompatible, onDevice: modelFile, openAICompatible: {baseURL,
model, apiKeyRef}, contextLimit, egressScope }`. This is a clean generalization of the EXISTING
`ILLMProvider` seam: `makeProvider(profile)` → `LlamaProvider` (onDevice) or `OpenAIEndpointProvider`
(openAICompatible). The seam already exists; profiles turn the single config into a list + a default.

**Ties to the context gauge (just shipped):** `AgentRecord.profileId` (empty = active/default). The
GROUNDING CONTEXT ring then reads THAT profile's `contextLimit` — "Scout on Claude (200k) = 1% full;
Scout on a local 3B (8k) = 22% full." Closes the loop.

**Hard security rule (robustness):** API keys are credentials and MUST NOT sync across the mesh. The
profile SHAPE (name/kind/baseURL/model/contextLimit) syncs as a primitive; the **key lives only in
the device Keychain, referenced by profile id, never in the synced payload** — each surface holds its
own key for a shared profile. (Matches the existing "API key never leaves this store" + the connector
"credential stays on the desktop" pattern.)

**Equilibrium (cross-surface, the whole point):** add `SyncKind.profile` so desktop hub / iPad /
iPhone / web share the same named profiles (shape only). Each surface honors the profile CONTRACT via
its own runtime (desktop → web_runtime; web → its inference path; Apple → the seam), honest `n/a`
where a surface can't host a kind (an on-device GGUF profile is n/a on web). The egress badge reads
`profile.egressScope` so trust stays honest per profile. See EQUILIBRIUM.md.

**Why pre-GA:** retrofitting a profile contract AFTER sync + GA solidify means a migration; land it
before. **Suggested phasing:** (1) `RuntimeProfile` contract + `SyncKind.profile` + Keychain key
store; (2) Apple Basic (pick active) + Advanced (manage list + per-agent `profileId`) + gauge reads
profile; (3) desktop hub honors profiles; (4) web authors/uses them. Each surface proven (parity).

*Lands on:* the `ILLMProvider` seam (Contracts/RuntimeCore), `InferenceConfigStore`, the sync
primitive framework, the per-agent `AgentRecord`, and the egress-badge canon.

---
### U. The Delivery Belt — delivery-workbench as a desk surface (the conveyor-belt builder) — [full proposal](./proposals/delivery-belt.md) — **B1 SHIPPED → [phase-86](./phase-86-delivery-belt/) (5/5)**; B2 expanded by owner direction into the **Steering Desk charter, scaffolded → [phase-87](./phase-87-steering-desk/)** (attach/steer/classify/ground under the Telegram consent spine, contract-shaped for the Apple surfaces); B3 (the factory), B4 (DeskOS) remain

*2026-07-07 (late):* B0 reconciled against reality — the substrate already
shipped upstream richer than the RFC guessed; the flagship-tree reader work
landed there (phase 16). B1 scaffolded here with the owner's wider frame
pinned in the AGENT-BRIEF: *"my AI Headquarters — build out projects, steer
projects, finalize projects"* — the belt is registry-shaped (never
single-project) from the first commit. B2 (the nod), B3 (the factory), B4
(DeskOS) remain future phases per the RFC.

Owner direction (2026-07-07, the post-85/25 conversation): *"the desire was
for the delivery-workbench integration to be incredibly well integrated into
the UI/UX philosophy of Desk OS on iOS, and of course, its Web Equivalent…
it's almost like a conveyor belt builder with rich interaction affordances."*

Expanded the same day (owner): an **app of DeskOS** — start a repository
scaffolded with the delivery framework from the desk, an AI agent (Claude
Code / codex / any paired runner) scaffolds it properly from the user's
input, projects live as desk primitives AND separate entities, and many
such processes run controllable alongside. The factory floor. Slices B0–B4
and the two non-negotiables (receipts-only; every consequential act is an
actuator) are pinned in [the proposal](./proposals/delivery-belt.md).

**The reframe (recorded from the same conversation's honest audit):** the
framework's agent integration today is markdown-as-database plus hand-typed
contracts — six prose surfaces per shipping commit, edited by text surgery.
CLI verbs and a machine-readable state file are SUBSTRATE, not the product.
The product is the delivery pipeline as a desk-native, manipulable surface:

- **Each phase is a BELT; stories ride it as primitives through STATIONS**
  (candidate → scaffold → story → evidence → contract gate → PR → CI →
  merge → close) — the cadence already IS this pipeline; the belt makes it
  tangible.
- **A refusing station stalls the belt honestly, wearing the refusal** —
  the pre-commit hook's stderr as an in-world chip, CI conclusions as
  station lights, the walk rig as a station that stamps receipts.
- **Evidence is filed objects that stay openable** (the owner's video-review
  rule); the working agent is VISIBLE at its station (the run-story frames,
  Phase 74); rich affordances in the desk grammar — no prose, no modals,
  voice on inputs.

**The hard rule (canon):** the belt RENDERS from receipts — git, PRs, CI
conclusions, evidence files — and never keeps a parallel truth. Interactions
drive the real seams (`gh`, the hook, the rigs). Badges reported, never
inferred — the house rule applied to the delivery process itself.

*Lands on:* the Workbench node canvas (`/workbench`, Phase 69) + the
Blueprints exec/data-pin vision (mobile), DioStage + the Desk Primitive
contract, the run-story frames (Phase 74), the hub as the one spine
(Phase 72). *Substrate prerequisite:* a machine-readable roadmap state the
markdown renders FROM (the pmo-roadmap side), so the desk reads state, not
regex. Spans three repos deliberately — the belt is the flagship consumer
that forces the substrate honest.


---
### V. The Rails-Aware Desk — rails objects as grounding kinds + the ambient dw observer — **SHIPPED → [phase-88](./phase-88-rails-aware-desk/) (CLOSED 5/5, 2026-07-08, same day)**; one deferred rider (the remote-events worker daemon) recorded in the phase's decisions

Owner direction (2026-07-08, verbatim, during the Phase-87 charter
conversation): *"having the ability to natively offer parts of, e.g.,
open phases, open roadmaps, open stories, to use as context for any of
the agent definitions, and so on, and the ability to construct agent
chains so the local model keeps a note of everything happening with dw
in the background, happening on another computer, for example."*

Two capabilities, one thesis (the rails are desk-native material):

- **Rails objects as grounding kinds.** An open phase, a roadmap, a
  story, an evidence file — pickable in the grounding picker exactly
  like a meeting or a note, hydrated with provenance into ANY agent
  run: an ask, a recipe/persona turn, a chain step, or a Phase-87
  steer. The content comes CLI-mediated per repo (the
  `missioncontrol_bridge` posture: `dw context` names the paths, the
  read is contained, state is never re-parsed from markdown), so a
  grounded story is a receipt, not a scrape. *Lands on:* the Phase-87
  factored hydration helper (`grounding_hydrate`), the grounding
  picker (`GroundingSection`), the project map, `dw context`.
- **The ambient dw observer.** A chain/workflow subscribed to rail
  events (`dw events`, the `dw hook` push seam, `scope:"belt"`
  frames) so a LOCAL model (RuntimeProfile-resolved — on-device, LAN,
  or a mesh node) keeps a running journal of what the rails did:
  story flips, gate refusals, evidence captures, phase closes —
  including repos living on ANOTHER machine, over the proven mesh
  relay (Phase 85) with the same honest liveness rules. The journal
  is a desk primitive (openable, ropeable, groundable in turn); the
  observer is read-only and off by default; anything it wants to DO
  is a proposal through the actuator flow. *Lands on:* the
  chains/workflows primitives, the one bus, `dw events`/`dw hook`,
  RuntimeProfile + mesh relay, the run-story frames.

**Sequencing note:** graduates after Phase 87 ships (it consumes the
factored hydration seam and the steering audit vocabulary). The
cross-machine leg needs the rails repo's `dw` reachable on the far node
— the mesh worker precedent covers execution; rail-event RELAY is the
new wire and should be scoped honestly (likely: the remote node's
worker tails its own `dw events` and pushes envelopes, mirroring the
coder-queue pull pattern).

---

### W. JIRA Desk Sync (pull reports as Desk primitives) — **PLAN FILED** ([`docs/internal/PLAN_PHASE_JIRA_DESK_SYNC.md`](../../../docs/internal/PLAN_PHASE_JIRA_DESK_SYNC.md))

Owner direction (2026-07-11): a plugin that, after configuration (API
token, JIRA base URL, etc.), uses the JIRA REST API to pull reports as
Desk primitives — TODO / IN PROGRESS stories and items. The full RFC
lives in the plan doc above; this entry is the backlog handoff.

The gap is specific and half-built already. HoldSpeak ships a JIRA
connector (`connector_packs/jira_cli.py` + `activity_jira.py`) but it
is narrow on three axes: it runs `jira issue view KEY --plain` against
tickets already referenced in local activity (no JQL reports); its
output is `activity_annotations` (never reaches the Desk); and it is
CLI-mediated with no credentials of its own. Nothing sinks external
data into Desk primitives, and no connector speaks REST with its own
credentials. JDS-01 fills both.

One thesis, pull-only: a new `desk_sync` connector kind that, after the
operator configures base URL + token (secret store, joined at request
time), polls a named JQL report on a cadence and materializes the
result as one Note per issue (stable id `jira:<slug>:<KEY>`, tagged by
`statusCategory` lane) grouped into a KB per report. The Desk's existing
diorama renders them as ordinary objects badged `cloud · <host>` with a
"refreshed N min ago" line. Lanes key off `statusCategory.key`
(`new`/`ind`/`done`), stable across every team's custom workflow; the
granular `status.name` rides as a tag. A provenance sidecar
(`primitive_sources`, mirroring `artifact_sources`) makes synced notes
read-only until the operator detaches them, so a refresh never
clobbers a hand edit (there is no hand edit to clobber until detach).

The design reuses the most machinery and invents the least: the
`connector_sdk` manifest + `Enrich`/`Preview`/`Clear` protocols, the
`PermissionGate` (`network:outbound`, host-pinned against redirect
SSRF), the existing `NoteRepository`/`KBRepository`, the `settings_secrets`
secret-store rule, and the Desk's existing primitive renderers. No new
primitive type, no new rendering surface. Write-back (transition an
issue, comment) is deliberately deferred to a later `jira_issue_actuator`
sibling of `github_issue_actuator` on the `gated_connector`+
actuator spine — the pull MVP needs only the `PermissionGate`, never
the propose-approve-execute gate.

*Lands on:* `connector_sdk.py` (one new kind + capability +
permission), `connector_packs/jira_desk_sync.py` (the pack),
`db/primitive_sources.py` (the sidecar repo), `db/core.py` (additive
schema migration), `settings_secrets.py` (two secrets),
`web/routes/primitives/notes.py` (read-only 409 + detach),
`commands/doctor.py` (the check).

**Sequencing note:** independent of the current phase; can graduate
whenever a slot opens. No dependency on the iPad/Apple surfaces beyond
what every synced primitive already assumes (the sync wire contract is
untouched). The one live-verification requirement is a real JIRA
instance (Cloud or DC) with an API token/PAT; unit and integration
tests use a fake opener and need no network.

---

### X. Control-posture completion — the HS-93-07 remainder (full family matrix + grant surfaces + owner/device proof)

Owner decision (2026-07-15): HS-93-07 closed at its two delivered
authority families — configured Integration writes (Slack, Webhook,
GitHub) and registered Coder text/allowed-key steering — so Phase 93
could proceed to the cross-client UI consistency remediation. This
entry preserves the descoped remainder verbatim; none of it is claimed
by the closed story.

What remains, all on the existing `operation-policy/v2` spine (no new
resolver, registry, or receipt store):

- **Family coverage.** Classify dictation delivery, inference (local,
  paired, external), Coder factory operations (spawn's optional
  command, rename, kill — each with its own consequence class),
  Mission Control/workflow runs, sync, cadence/background work, and
  destructive Desk mutations through policy v2, honoring the
  `control-mode-contract.md` matrix. `current_behavior` stays
  unacceptable for any consequential primary-journey operation; YOLO
  gives zero HoldSpeak prompts for eligible configured/registered
  operations in every one of these families and never auto-allows an
  unknown one.
- **Grant surfaces.** Secure/Normal bounded grant issue/use/revoke
  presentation: actor, operation, destination, data/resource scope,
  TTL/count, remaining uses, revoke; every use mints a source-linked
  Receipt.
- **Shared treatment.** Qlippy, Mission Control, and Cadence consume
  the same commitment/reason result with no consequential fallback
  `Approve`/`Apply`/`Run`; Qlippy supplies no banter or personality
  prose around consequential decisions.
- **Proof.** Owner control/treatment production walks with exact
  prompt counts and prediction/Receipt-findability verdicts, plus
  physical Web/iPhone/iPad evidence with build, device, destination,
  and operation provenance.

**Sequencing note:** the natural next slice was already named in the
HS-93-07 progress record — classify Coder factory/destructive
operations first, because spawn/rename/kill have materially different
consequences and must not inherit text-steering posture authority by
accident. HS-93-08/09 do not depend on this entry's completion, but
the Phase-93 exit criterion "every control mode passes the invariant
matrix" cannot be satisfied without it; the phase close must link
back here honestly.

---

### Y. The physical proof program — owner + device evidence continued from Phases 93/94

Owner decision (2026-07-16): Phases 93 and 94 close their stories at
the delivered, machine-verifiable scope (implementation, bounded
suites, API-backed production Web walks, simulator builds, two-process
node proofs, real linked-worktree fixtures). Every criterion that
requires the owner's body or physical hardware moves here verbatim so
it is scheduled work, not a fiction. Nothing in this entry is claimed
by any closed story.

**Phase 93 residue (per story):**

- HS-93-01: owner first-glance explanation + moved-tool discovery walk
  on the exact production build; physical iPhone/iPad VoiceOver walks.
- HS-93-02: physical iPhone/iPad contextual-entry + pasted-direct-link
  walks (cancel and failure legs); owner confirmation that no journey
  ends orphaned and Studio does not feel like a second home.
- HS-93-03: owner copy read-through of the ten primary journeys on
  Web + physical iPhone/iPad with zero misunderstood noun, state,
  destination, or commitment; forced-failure walks observed.
- HS-93-04: owner discovery-time and irrelevant-control measures on
  the production Desk; physical-device inspector/connector/Coder/
  Runs-on/relaunch walks.
- HS-93-05: real-microphone fault matrix on production Web + physical
  iPhone/iPad including interruption during active capture; per-walk
  provenance records (device, build, audio route, model, destination).
- HS-93-06: 5/30/60-minute native and 5/30/120-minute desktop
  RSS/checkpoint traces on real hardware; disk-full/permission/route/
  call/lock/kill/relaunch fault walks; airplane-mode capture with
  exactly-once cross-device sync; owner conflict decisions on both
  production entry points and both devices.
- HS-93-07: already parked as candidate X (posture family matrix and
  owner/device proof).
- HS-93-08: physical iPhone/iPad VoiceOver screen-curtain, Dynamic
  Type, Reduce Motion, and orientation walks (the Web keyboard-only
  and scale legs are machine-verified in the story).
- HS-93-09: the five-working-day owner dogfood with full provenance,
  the ten-journey direct observation on production Web + flagship
  Swift, posture prompt-count verdicts, and the owner copy verdict.
  The two live owner sessions of 2026-07-15 (LAN iPhone + desktop,
  findings R2-01..R2-10, fixes verified the same night) are recorded
  in the story as the first real lived-use evidence; they do not
  substitute for the sustained window.

**Phase 94 residue:** the second physical machine over Tailscale
(real transport, clock skew, tailnet latency budgets), the physical
iPad native + iPad Safari tailnet-HTTPS legs (Tailscale Serve, secure-
context microphone), real GitHub PR/CI receipts where the two-process
walks used local substitutes, and the HS-94-10 owner walk on all three
surfaces. The upstream reusable-processes Delivery Workbench repo
adopting the counterpart contract (capabilities, cursored events,
evidence manifest/asset) mirrors what this repo's vendored dw now
implements.

**Sequencing note:** one sitting on real hardware can burn down most
of the Phase-93 list; the Phase-94 legs need the second machine and
the iPad reserved. The UAT framework (holdspeak-uat) is the natural
conductor for the owner sittings.

### Z. The Desk OS owner leg — Phase 95's live verdict (continues Y's program)

Phase 95 closed at machine-verifiable scope on 2026-07-18 under the
standing close directive: the WebGL stage at the frame budget, one window
chrome with dock/snap/cycling, every surface in-world, fifteen routes
demoted, the no-exit lock, docs under the Constitution, and the assembled
production walk — all green. What no machine can cast is the verdict the
phase was born from: the owner at the desk, on the production build,
judging whether it now FEELS like a native OS.

The criterion, preserved verbatim from HS-95-10: *"The owner completed
the walk on the production bundle and the verdict is recorded;
walk-blocking defects fixed and re-walked, or the phase does not close"*
— rescoped by the standing directive to this row plus **UAT Campaign 13**
(`uat/campaigns/owner-13-desk-os.yaml`, seven scenarios, ~45 minutes,
loaded by the conductor). Run the sitting, record the verdict verbatim,
triage findings per TRIAGE.md. The Article VII Dialog-grammar drift in
re-homed cores and Article IV mic coverage ride the same triage.
