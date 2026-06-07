# HoldSpeak — Backlog (living candidate phases)

The parking lot so good ideas do not get lost between phases. Each entry is a
**candidate future phase**, not committed work. When one is picked up it graduates
into its own `phase-NN-*/` folder with an AGENT-BRIEF + stories, and its row here
flips to "scaffolded" then "shipped".

Sourced from the Phase-48 strategic review (`.guru_meditation.md`, an untracked
scratch file, captured here so it survives) and the Phase-48 deferred decisions.

**Last updated:** 2026-06-07 (created at Phase 48 close).

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
| B | Voice macros / command grammar | feature | review bet #2; deferred from P48 | strong |
| C | Release-readiness gate (schema policy + 1.0) | release | review "Trouble" #5; deferred from P48 | **scaffolded → [phase-50](./phase-50-release-readiness/)** |
| D | Frontend density paydown (dictation page) | debt | review "Trouble" #4; P48 standing invariant | recurring |
| E | `WebRuntime` / `web_server` decomposition | debt | review "Trouble" #1 | watch |
| F | Local activity as pre-briefing fuel | feature | review bet #6 | exploratory |
| G | Privacy visible at decision points | feature | review bet #7 | delight |

### A. Meeting aftercare ("close the loop") — shipped as Phase 49 (CLOSED 6/6)
The meeting side has plugins + artifacts; the next value is follow-through, not
more artifact types. "What changed since last meeting?", "what did we decide?",
"what is still open for me?", "draft the follow-up", "turn accepted actions into
issues", "show me the transcript moment that justifies this action." A beautiful
artifact that never changes the user's next action is decoration.
*Lands on:* the meeting/history surface + the actuator system (P37/P38) for
"actions -> issues".

### B. Voice macros / command grammar
A small, visible, deterministic spoken-command layer alongside the LLM rewrite:
"new paragraph", "bullet list", "code block", "send it", "copy only", "make it
concise", plus user-defined phrases ("standup update", "bug report template").
Inspectable and editable in the UI, not LLM magic. Stays on the daily-dictation
north star (Future A).

### C. Release-readiness gate — scaffolded as Phase 50
The DB is intentionally `SCHEMA_VERSION = 1`, greenfield, **not release-stable**.
Before a tagged/PyPI release, define and ship the policy: supported config/DB
versions, whether destructive migration is ever allowed, backup/export before
upgrade, and what `doctor` reports on unexpected schema state. This is the bet
that actually lets the open-source push *ship* publicly.

### D. Frontend density paydown
`dictation.astro` (~2.7k lines) and `dictation-app.js` (~2.5k lines) are large and
grew every recent phase (the standing page-density invariant). Factor into section
partials / behavior modules before the next feature makes it worse.

### E. `WebRuntime` / `web_server` decomposition
The review flags `WebRuntime` as "the next central chip under thermal load" after
the DB decomposition (P31) and route split (P26/P34). A structural phase if it
keeps absorbing responsibility.

### F. Local activity as pre-briefing fuel
Turn the abstract browser/activity layer into concrete, dismissible, source-cited
nudges: "here is what you touched since last time" before a meeting; "want to
dictate a reply with this GitHub issue as context?" Ambient without being creepy.

### G. Privacy visible at decision points
Every place that could use a model, connector, actuator, device, or activity
source answers three plain-language questions: what data is used, does anything
leave this machine, what control do I have right now. A delight feature for this
category.

## Sequencing note

No fixed order. If the open-source *release* is the goal, **C** is the highest
leverage (everything else polishes a thing that is not formally shippable). If
deepening the product first, **A** (user-favored) or **B** continue the north
star. **D** can ride along with whichever dictation-side phase comes next rather
than being its own phase.
