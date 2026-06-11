# HoldSpeak — Backlog (living candidate phases)

The parking lot so good ideas do not get lost between phases. Each entry is a
**candidate future phase**, not committed work. When one is picked up it graduates
into its own `phase-NN-*/` folder with an AGENT-BRIEF + stories, and its row here
flips to "scaffolded" then "shipped".

Sourced from the Phase-48 strategic review (`.guru_meditation.md`, an untracked
scratch file, captured here so it survives) and the Phase-48 deferred decisions.

**Last updated:** 2026-06-11 (post-Phase-53 strategic review: candidate **D** promoted
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
| D | Frontend density paydown (dictation page) | debt | review "Trouble" #4; P48 standing invariant | **scaffolded → [phase-54](./phase-54-dictation-frontend-decomposition/)** |
| E | `WebRuntime` / `web_server` decomposition (+ `meeting_session.py`) | debt | review "Trouble" #1 | watch (a **dictation-path slice** was carved in [phase-52](./phase-52-voice-macros/) with B; the full decomposition stays a watch item) |
| F | Local activity as pre-briefing fuel | feature | review bet #6 | **shipped → [phase-53](./phase-53-activity-prebriefing/) (CLOSED 7/7)** (source-cited dismissible nudges + "Dictate with this" closes the loop, proven on a live LLM) |
| G | Privacy visible at decision points | feature | review bet #7 | absorbed into **J** (the Qlippy card is the decision-point surface) |
| H | Public-docs hygiene (strip roadmap vocab from user-facing docs) | release/debt | this conversation (post-P50 release polish) | **shipped → [phase-51](./phase-51-public-docs-hygiene/) (CLOSED 5/5)** |
| I | Meeting import ("bring your archive") + faceted history search | feature | post-P53 strategic review | **queued — next after Phase 54** |
| J | Qlippy, the presence enhancer (absorbs G) | feature/delight | post-P53 review + [proposal](./proposals/qlippy-presence-enhancer.md) | queued after I |
| K | Speak the world's languages + spoken-symbol dictionary | feature | post-P53 strategic review | queued after J |
| L | Export connectors (Notion / Slack / Docs) on the connector-pack framework | feature | post-P53 strategic review | parked |
| M | Dictation preview-before-commit (review before it types) | feature | post-P53 strategic review | parked |
| N | Windows port | strategic | post-P53 review; `CODEX_IDEAS.md` | parked (large; biggest reach unlock) |
| O | Wake word ("local + private" positioning) | strategic | post-P53 strategic review | parked (high false-positive risk) |

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

### D. Frontend density paydown — scaffolded as Phase 54
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

### G. Privacy visible at decision points — absorbed into J
Every place that could use a model, connector, actuator, device, or activity
source answers three plain-language questions: what data is used, does anything
leave this machine, what control do I have right now. A delight feature for this
category. *2026-06-11:* absorbed into candidate **J** — the Qlippy card is exactly
the per-decision surface where those three answers belong (an actuator-approval card
that names what data is used and what egresses *is* G, with a face). If J is never
picked up, G reverts to its own candidate.

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

### I. Meeting import ("bring your archive") + faceted history search — queued
The single highest-ROI feature gap from the post-P53 review: meeting intelligence is
live-capture-only. There is no "import this recording" path anywhere (verified:
`MeetingRecorder` only handles live audio; no import in CLI or web). An import flow
(audio file → Whisper → MIR → the 14 plugins → `/history` with aftercare) reuses the
entire existing pipeline and turns meeting intelligence retroactive — users have
archives. Pairs naturally with **faceted history search** (date / speaker / topic /
action-status; today `/history` has a single text box), because import is what makes
the archive big enough to need it.
*Lands on:* the meeting capture seam + `/history`.

### J. Qlippy, the presence enhancer (absorbs G) — queued
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

### K. Speak the world's languages + spoken-symbol dictionary — queued
Confirmed absent: no language config, no Whisper language param, no per-session
override — yet Whisper supports ~99 languages, so this is mostly one settings knob,
pipeline plumbing, and honest docs. The cheapest reach-expansion available. Rider in
the same thesis ("the input layer adapts to you"): a **custom spoken-symbol
dictionary** ("tilde" → `~`, "arrow" → `→`) — the punctuation table is hardcoded
today, and personal vocabulary is classic daily-driver value.
*Lands on:* settings + the transcription path + the punctuation layer.

### L. Export connectors (Notion / Slack / Docs) — parked
"Meeting notes land in Notion" is the most-requested shape of this product category.
The connector-pack + actuator framework is proven; these are new write connectors
behind the existing permission-manifest gate. Parked until the queue above clears.

### M. Dictation preview-before-commit — parked
A "show me what you're about to type, edit, confirm" mode for high-stakes targets
(emails, shell). Today the pipeline types immediately. Small, safety-flavored.

### N. Windows port — parked (strategic)
The largest reach unlock (voice-typing demand is Windows-heavy); weeks of OS-level
work (hotkey, synthetic typing, audio capture). Already noted in `CODEX_IDEAS.md`.
A commitment, not a phase rider — park until deliberately chosen.

### O. Wake word — parked (strategic)
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
