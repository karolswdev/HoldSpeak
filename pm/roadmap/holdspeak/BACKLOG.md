# HoldSpeak — Backlog (living candidate phases)

The parking lot so good ideas do not get lost between phases. Each entry is a
**candidate future phase**, not committed work. When one is picked up it graduates
into its own `phase-NN-*/` folder with an AGENT-BRIEF + stories, and its row here
flips to "scaffolded" then "shipped".

Sourced from the Phase-48 strategic review (`.guru_meditation.md`, an untracked
scratch file, captured here so it survives) and the Phase-48 deferred decisions.

**Last updated:** 2026-06-08 (candidate **F** scaffolded as Phase 53: local activity as
pre-briefing fuel, source-cited dismissible nudges on the daily surfaces. Candidate **B**
shipped as Phase 52 (a voice command launcher reusing the actuator executor, with a scoped
slice of **E**). Candidate **H** shipped as Phase 51. Created at Phase 48 close.)

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
| D | Frontend density paydown (dictation page) | debt | review "Trouble" #4; P48 standing invariant | recurring |
| E | `WebRuntime` / `web_server` decomposition | debt | review "Trouble" #1 | watch (a **dictation-path slice** is being carved in [phase-52](./phase-52-voice-macros/) with B; the full decomposition stays a watch item) |
| F | Local activity as pre-briefing fuel | feature | review bet #6 | **shipped → [phase-53](./phase-53-activity-prebriefing/) (CLOSED 7/7)** (source-cited dismissible nudges + "Dictate with this" closes the loop, proven on a live LLM) |
| G | Privacy visible at decision points | feature | review bet #7 | delight |
| H | Public-docs hygiene (strip roadmap vocab from user-facing docs) | release/debt | this conversation (post-P50 release polish) | **shipped → [phase-51](./phase-51-public-docs-hygiene/) (CLOSED 5/5)** |

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

### D. Frontend density paydown
`dictation.astro` (~2.7k lines) and `dictation-app.js` (~2.5k lines) are large and
grew every recent phase (the standing page-density invariant). Factor into section
partials / behavior modules before the next feature makes it worse.

### E. `WebRuntime` / `web_server` decomposition — partial slice in flight (Phase 52)
The review flags `WebRuntime` as "the next central chip under thermal load" after
the DB decomposition (P31) and route split (P26/P34). A structural phase if it
keeps absorbing responsibility. [Phase 52](./phase-52-voice-macros/) carves the
**dictation-execution slice** (the inline `_maybe_run_dictation_pipeline`
orchestration, currently inside the 2,341-line `web_runtime.py`) out into a testable
module, because that is the seam the voice-macro feature lands on. The rest of the
god-object (hotkey/device/meeting/activity) stays a watch item; full E is still its
own future phase if it keeps absorbing responsibility.

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

### G. Privacy visible at decision points
Every place that could use a model, connector, actuator, device, or activity
source answers three plain-language questions: what data is used, does anything
leave this machine, what control do I have right now. A delight feature for this
category.

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

## Sequencing note

No fixed order. If the open-source *release* is the goal, **C** is the highest
leverage (everything else polishes a thing that is not formally shippable). If
deepening the product first, **A** (user-favored) or **B** continue the north
star. **D** can ride along with whichever dictation-side phase comes next rather
than being its own phase. **H** is the cheap release-facing follow-on to **C**
(scaffolded as Phase 51). The strongest remaining product bet is **B** (voice
macros), and pairing it with a scoped slice of **E** (carve only the routing seam
the macros land on, not the whole `WebRuntime` decomposition) is the way to ship a
meaningful codebase improvement *with* a feature under one thesis.
