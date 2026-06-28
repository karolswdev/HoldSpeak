# HoldSpeak — Backlog (living candidate phases)

The parking lot so good ideas do not get lost between phases. Each entry is a
**candidate future phase**, not committed work. When one is picked up it graduates
into its own `phase-NN-*/` folder with an AGENT-BRIEF + stories, and its row here
flips to "scaffolded" then "shipped".

Sourced from the Phase-48 strategic review (`.guru_meditation.md`, an untracked
scratch file, captured here so it survives) and the Phase-48 deferred decisions.

**Last updated:** 2026-06-11 (candidate **Q** shipped as [phase-58](./phase-58-front-door/) (CLOSED 6/6) — the story is a decision now. Earlier today: **P** shipped as [phase-57](./phase-57-transcript-import/) (CLOSED 5/5) — transcripts import as real meetings. Earlier today: **J** shipped as [phase-56](./phase-56-qlippy/) (CLOSED 7/7), **G** absorbed-shipped with it; **K** is next per the agreed sequence. Prior: post-Phase-53 strategic review: candidate **D** promoted
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
| M | Dictation preview-before-commit (review before it types) | feature | post-P53 strategic review | parked |
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
