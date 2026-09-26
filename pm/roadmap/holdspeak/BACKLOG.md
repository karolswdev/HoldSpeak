# HoldSpeak — Backlog (living candidate phases)

## Phase 200 takes delivery priority

**Updated:** 2026-09-05, on the owner's request for a major Phase 200 roadmap.

[Phase 200: The Working Practice](./phase-200-the-working-practice/README.md)
is the current delivery program.
Its [disposition map](./phase-200-the-working-practice/BASELINE.md#earlier-roadmap-accounting)
assigns the relevant work from Phases 170–180 and the architect-assistant package.
Its six gates carry forty scoped stories and a measured owner pilot.

This is the explicit owner-directed exception to the historical argument against one large phase below.
Delivery still uses small PRs and incremental release gates.
Existing implementation is reused and proved before replacement work is proposed.
Earlier stories retain their actual status; this entry does not close or discard them.

New portfolio surfaces, extra connectors, native parity, and additional worker adapters
need a measured Phase 200 pilot gap before they take delivery capacity.
The outcome review in HS-200-37 records each expansion decision.

## Phase 201 parked summary follow-through

**2026-09-19 — Astra, ratified by Muad'Dib.** The first-use summary gesture
runs only the disclosed `meeting.deferred_analysis` route. Web Record and Stop
no longer enqueue live/deferred intelligence. This deliberately removes the
Phase 200 plugin chain → `ProposalBridgeService` → Review face production entry
on that path. It is a regression accepted to make one truthful meeting result,
not an inherited failure or deleted feature. All plugin/bridge code remains.

The smallest return path is to admit a plugin member only when its frozen
`deployment_revision_id` and `profile_revision` already occur among the
disclosed legs, and map its actual attempts into the run receipt by deployment
identity. Skip other members. If sequential destinations need a wider route
contract, both brains must first settle a `capability_id` per leg. Do not add
ambient destinations behind the existing summary gesture. Retained strict
expected failures cover five proposals and partial-chain retry; their live
summary-ready preconditions must continue to pass.

Also parked: retire or reconcile old automatic-intelligence settings and their
doctor/setup/trust projections. `meeting_import.py:_persist_import` and
`db/meetings.py:recover_capture` retain old hashless enqueue paths
for imports and historical displaced work. Fence or disclose these before
restoring automatic summary behavior. The first-use Web Record/Stop path is
fenced separately. Lane B must render an unexecuted Review chain as absent or
“Not run”, never as “no proposals found”.

## Earlier backlog record

The parking lot so good ideas do not get lost between phases. Each entry is a
**candidate future phase**, not committed work. When one is picked up it graduates
into its own `phase-NN-*/` folder with an AGENT-BRIEF + stories, and its row here
flips to "scaffolded" then "shipped".

Sourced from the Phase-48 strategic review (`.guru_meditation.md`, an untracked
scratch file, captured here so it survives) and the Phase-48 deferred decisions.

**Last updated:** 2026-08-30 — candidate **AF** Desk Chat graduated through
Phase 152, while the handover-menu candidate [Live Intelligence Proof](./phase-151-live-intel-proof/current-phase-status.md)
also graduated and completed 7/7. Those parallel branches independently reused
the Phase 151 number; their historical paths remain intact and PR #511
consolidates both workstreams. DC-03–05 stay parked. Earlier — candidate
**AF. The Desk Chat**
filed with its full RFC
([`docs/internal/PLAN_PHASE_DESK_CHAT.md`](../../../docs/internal/PLAN_PHASE_DESK_CHAT.md)):
the warpdrv chat grammar (threads, streamed parts, kernel-admitted
tool loop, modes/guardrails/annotations, voice call, subthreads)
ported as capabilities onto HoldSpeak's own machinery — five
phases, DC-01 The Thread first. Earlier the same day (two entries. First, the record made
honest retroactively per the owner's catch: **Event → one-tap
record** never had a row here — it lived only in the Phase 146
handover menu as the twice-deferred "rail's natural next verb" —
and graduated directly as [Phase 147 — One-Tap
Record](./phase-147-one-tap-record/current-phase-status.md)
(COMPLETE 7/7, merged 2026-08-29 as PR #501, main `16477660`).
Recorded here so the parking lot stays the "all of them" container;
future menus source from THIS file first. Second, candidate **AA**
partially GRADUATES: its "window-head menus and keyboard
equivalents on the verb registry" row rides into **Phase 148 — the
menu-glyph craft pass** (owner direction 2026-08-29: the Amiga
tribute deserves menus with craft — "if you now go and expand the
top menu toolbar... they are really poor, right?"; scope = top-bar
menus + context menus + window-head menus, keycap-glyph grammar,
ghosting/separators/toggle marks, restrained sprite glyphs where
meaning is earned; AA's OTHER rows — drag-reorder, cross-window
re-filing, record-orb drop target, per-object Receipts, pull-down
screens, in-place icon editor — stay parked here).)
Earlier: 2026-08-28 (candidate **AE** GRADUATED and SHIPPED the
same day it was filed — the Calendar Snapshot adapter landed as story
HS-146-07 inside [Phase 146 — Multiple
Calendars](./phase-146-multiple-calendars/current-phase-status.md)
(CLOSED 7/7, merged as PR #500): screenshot → router vision extraction →
anchor-gated review → generated `.ics` registered as the "O365 SNAPSHOT"
file source through the one bounded parser. The two counsel ledger items
(422 upload-refusal surfacing; vision-capable pre-filter in the
direct-dispatch fallback) carry in the Phase 146 handover ledger, and no
real-vision-model probe has run yet — named honestly in the story's
Out-scope.)
Earlier: 2026-07-30 (candidate **Y** GRADUATED and CLOSED as
[Phase 108 — The Locked Room](./phase-108-the-locked-room/current-phase-status.md),
CLOSED 7/7: the post-ruling 15-row register is empty, the corrected machine
closeout passes 8/8, and the owner's verdict was "'s all's good, moyt.").
Earlier: candidate Y was filed at Phase 107 close with §5b confinement
and the audited remainder. Earlier: 2026-07-07 late (candidate **U** SCAFFOLDED — B1 opens as
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
| Y | §5b Confinement + the audited remainder (the register to empty) | security/architecture | Phase 107 closeout; the HS-107-05 audit | **graduated → [Phase 108](./phase-108-the-locked-room/), CLOSED 7/7** — 15 debt → 0; corrected machine closeout 8/8; owner verdict "'s all's good, moyt." |
| Z | The Inherited Ledger (96 backend repairs + walk deepening) | repair | Phase 129 full-suite triage + Sol counsel | **filed** — see §Candidate Z; owner ruling at the 129 sitting |

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

### Y. §5b Confinement + the audited remainder — graduated as Phase 108

**Current disposition (2026-07-30):** [Phase 108 — The Locked
Room](./phase-108-the-locked-room/current-phase-status.md) implemented
the full post-ruling work list. T01/T02 now route universally through
`process.input@1`; C02/C03/C05 require authenticated principals; A01-A09
sit behind the spawned warrant executor and A10 was deleted. The debt
register is zero. Generic executor liveness and the mandatory live-bus CI
gate also landed. The machine closeout passes 8/8 in one session; the
phase closed 7/7 after the owner's verdict: "'s all's good, moyt."

Phase 107 closed 23 of 38 audited debt sites; the register
(`holdspeak/kernel/effect_ledger.json`) now carries **15 debt rows,
each with a machine-asserted closing condition** — the next phase
inherits a work list, not a mystery:

- **A01-A10** — the raw-desktop primitives in `typer.py`: RFC §5b
  confinement (a privileged executor process holding kernel warrants
  instead of imports; A10's AppleScript helper may instead be
  deleted). This is what finally lets Article XI clause 6 self-repeal
  and upgrades `docs/SECURITY.md` beyond "cooperating code".
- **T01/T02** — make every `coder_steering.deliver`/`deliver_keys`
  transport act kernel-routed; delete the preflight and direct
  web-route paths the HS-107-05 audit found.
- **C02/C03/C05** — make an authenticated principal mandatory at
  every read entry point; remove the `LOCAL_OWNER` defaults.

The owner's 2026-07-29 sitting resolved the held rulings: N10-N12 are
clause-5-exempt computation, an explicitly configured wake action is
armed by that configuration, and the ~25 ms kernel admission price is
accepted with the baseline re-pinned.

The other carryovers have also landed: Phase 109 shipped the second
userland program and process window; HS-108-05 shipped the generic
liveness seam and made `tests/e2e/test_live_bus.py` a built-bundle,
Chromium-backed, no-skip CI gate.

## Candidate Z — The Inherited Ledger (the 96 + the walk deepening)

**Type:** repair · **Source:** Phase 129's first-ever full backend run + Sol's
acceptance counsel (phase-129-one-grammar/SOL-COUNSEL.md) · **Signal:** filed
2026-08-09, owner ruling pending at the Phase 129 sitting.

The 96 backend test failures that reproduce on pre-129 main
(exact list: phase-129-one-grammar/assets/hs-129-11/inherited-ledger-96.txt;
raw logs beside it) — inherited Phase 118–128 integration debt across
companion actuators (slack/github/webhook), intel streaming, dictation
surfaces, history slack, decision records, live bus, sync/primitive
contracts, and guards. Sol's conditions for the graduated phase, adopted:
an owner, an exit condition (the ledger reaches zero or each residual is
individually owner-ruled), and **no baseline expansion** — a red-CI merge
comparison is an exception per PR with the failure-name diff attached
(precedent artifacts: assets/hs-129-11/ci-*.txt), never a default; any NEW
name entering the set blocks.

Riders from the same counsel: the walk deepening (fresh-home pass,
hostile-content pass, interaction pass incl. mic/edit/error forcing, a
second browser engine, occlusion assertions — SOL-COUNSEL.md finding 6)
and the commandDeck target-specific test cases (finding 8). The 14
workbench-walk e2e ERRORs are NOT in this ledger — proven environmental
(all pass with a hub at HOLDSPEAK_HUB_URL; evidence-story-11.md,
2026-08-09 capture).

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

### AA. Workbench remainders — the Phase-105 grammar's next notches

Recorded at the HS-105-07 close (law: `docs/internal/DESK_GRAMMAR.md`
§7). Drawer-window drag-reorder (unlocks the Clean up and Snapshot
verbs plus free member arrangement inside the icons view);
cross-window drag re-filing; the record orb as a drop target
(Speak-with-context); multi-object drops; per-object Receipts once
the kernel journal serves a per-object route; window-head menus and
keyboard equivalents on the verb registry; artifact ("paper") sprite
regeneration per the icon discipline; pull-down screens/workspaces;
the in-place icon editor. Each lands the Phase-105 way: mock, owner
gate, guard, live walk.

### AB. The watched hand's parked candidates — cut or deferred by the Phase-104 council

Recorded at the HS-104-07 close (charter:
`phase-104-borrowed-fire-ii/current-phase-status.md` §"Decisions
deferred"). Three named candidates, each with the scope the council
left it:

- **Observed-archives adapter** — an opt-in scanner over
  `~/.claude/projects` exposing last-seen + confidence per archived
  session; materializes NO desk objects until correlated with a live
  pane or Work attempt (the census-as-desk-objects idea was cut: an
  archive proves neither liveness nor attachability).
- **Context gauge on the selected session** — a quiet,
  Reduce-Motion-safe gauge labeled `reported` / `estimated` /
  `unavailable`, paired with a REAL compact/handoff verb; blocked on
  the capability ledger declaring context reporting per adapter
  first (drift-with-context physics was cut as an Article I
  violation).
- **The merge actuator** — bound to PR + head SHA + merge method,
  stale-head refusal, a Receipt; a clean story on the Phase-37/61
  executor spine now that PR receipts exist. Read stays read-only
  until this lands as its own consented actuator.

### AC. Sync clocks drift on arrival — FIXED 2026-07-26 (same day)

Fixed at the Phase-104 close after a third CI strike:
`create_project`/`update_project` accept the incoming sync clock and
the push merge passes `meta.last_modified` through (matching what
the relationship buckets already did); pinned by
`test_project_merge_preserves_the_incoming_sync_clock` with a frozen
2020 instant that fails the naive restamp design deterministically.
Original diagnosis, kept for the record:

Diagnosed 2026-07-26 while it flaked CI twice (integration
`test_one_place_relationships`, `assert 200 == 409`). The push merge
(`web/routes/sync.py`) creates/updates projects through repository
calls that stamp the DESTINATION's own `updated_at` instead of
preserving the incoming `last_modified`; when the write crosses a
second boundary relative to the source's stamp, a later conflicting
push at the source's clock reads `local newer` and silently returns
200 where the equal-clock rule should 409. Fix shape: the merge
passes the incoming clock through to the write (repositories accept
an explicit `updated_at`), keeping cross-device clocks comparable;
the flaky test then pins the boundary with a frozen clock instead of
racing the wall.

### AD. Phase 106 remainders — the kernel's unfinished business

Filed at the Phase 106 close (2026-07-29, CLOSED 10/10, owner's
sitting passed 8/8). The kernel is real and the census delta was
**zero** — see [final-summary.md](./phase-106-the-kernel/final-summary.md).

**Historical disposition:** [Phase 107 — Close the Side
Doors](./phase-107-close-the-side-doors/current-phase-status.md) closed
7/7 and moved the corrected census from 38 debt to 15. Its remainder
graduated as [Phase 108 — The Locked
Room](./phase-108-the-locked-room/current-phase-status.md), now closed
7/7 with the register empty, corrected machine closeout 8/8, and the
owner's verdict recorded. The list below records the original handoff
rather than current open work.

1. **RFC §5b confinement — the ten raw-desktop primitives.** All ten
   remaining `raw_desktop` sites live in `holdspeak/typer.py`: the
   actual keyboard, Accessibility, clipboard and AppleScript calls.
   Routing their callers through the kernel does not cover them —
   any in-process Python still reaches them directly. They close only
   when raw effect primitives move into a privileged executor process
   holding broker-minted warrants instead of imports. **This is what
   finally lets Article XI clause 6 self-repeal**, and what would let
   `docs/SECURITY.md` say something stronger than "an audit and consent
   boundary for cooperating code."

2. **The second userland program** — project memory, and meetings and
   decisions becoming artifacts you can query years later. Named in the
   owner's original charge alongside PR follow-through; parked so
   Phase 106 shipped one visible program well rather than three thinly.

3. **The process window** — "what is running" as a pure `read` +
   `events` projection over the journal. Deferred out of Phase 105,
   then out of 106; it is now honestly a kernel consumer and cheap.

4. **The generic liveness seam** (found at HS-106-06, weighed at
   HS-106-07). An executor that never returns leaves an operation
   pending or running forever. **Pending forever is not indeterminate**
   — `unknown` means a previously running attempt lost the observer
   that could establish its state, which is a different fact. Needs a
   deadline or reaper with an honest terminal outcome.

5. **The CI blind spot.** `tests/e2e/test_live_bus.py` skips without
   Playwright and a built web bundle, and the bundle is gitignored — so
   three of its tests sat red on `main` across three merges before #390
   caught them, and CI never noticed. Either build the bundle in CI, or
   make the skip loud.

6. **Send-latency discrepancy, unresolved.** The HS-106-10 machine
   sitting measured **772.55 ms** for a gated send against the
   Phase-104 unarmed budget of 250 ms; HS-106-05 measured **84.76 ms**
   for the same path on an unloaded machine. The closeout ran with
   eight hubs live, so load is the likely explanation — but it is
   unproven. The owner did not report it as slow on his walk. Worth one
   clean measurement.

### AE. The Calendar Snapshot adapter — screenshot → reviewed events → a file CalendarSource (O365-without-the-server) — **GRADUATED → SHIPPED as HS-146-07 ([Phase 146](./phase-146-multiple-calendars/current-phase-status.md), CLOSED 7/7, PR #500)**

**Disposition (2026-08-28):** shipped the same day it was filed, folded
into Phase 146 by owner ruling with a required design beat. All five
shape points below landed as designed; the review surface became the
anchor-gated SurfaceWindow (week never silently guessed, CANCEL writes
nothing), and the vision call routes through `calendar.snapshot_extract`
(vision=True) with the named refusal `no_vision_model_assigned` when no
vision-capable model is assigned. Residue: the two counsel ledger items
and the not-yet-run real-vision-model probe, carried in the Phase 146
handover. The original filing, for the record:

Filed 2026-08-28 from the owner's direction, mid-Phase-146: *"most of
the time I will certainly not have access to the server my work's
O365's. Any way we could somehow build an adapter? e.g., I take a
screenshot of my whole week, and the adapter essentially translates
that into individual .icses."*

The shape (grounded in what ships with 146):

1. The owner drops one or more screenshots of the O365/OWA week view
   into HoldSpeak (desk drop / a dedicated affordance beside the
   calendar list editor).
2. A vision-capable model — through the intelligence router's
   assignments, so local-first with the egress badge telling the
   truth if a cloud model reads the owner's work calendar — extracts
   events: title, weekday, start, end, location.
3. **Week anchoring:** the screenshot's date header is read when
   visible; otherwise one confirm field ("week of …"). Never guessed
   silently.
4. **Review before commit** (the preview-before-type doctrine): the
   extracted events render as an editable list; the owner confirms.
   No silent writes from a model read of a screenshot, ever.
5. HoldSpeak writes a local `.ics` and registers/updates a
   **file-based CalendarSource** (label e.g. "O365 SNAPSHOT"). From
   there Phase 146's machinery does everything: the bounded
   hostile-input parser stays the one trust boundary (the model's
   output is parsed like any feed), replace-on-success means each new
   snapshot batch replaces that source's projection, provenance chips
   name it on the rail, per-source last-good protects the other
   calendars.

Why this beats the Phase-135-era "black-box OWA/Playwright" ruling
for the no-server case: corporate SSO/2FA makes driven-browser
automation brittle and credential-adjacent; a screenshot is something
the owner already can take on any locked-down machine, and the
adapter never touches work credentials at all. Zero new wire surface;
zero schema beyond 146's.

Open questions for the charter: which vision assignment (local .43
capability vs cloud with badge); multi-screenshot stitching for
overflowing weeks; whether the review step reuses the Thought/refine
surface or gets a small dedicated one.

---

### AF. The Desk Chat — the warpdrv chat experience, ported as capabilities — **DC-01 GRADUATED → [Phase 151 — The Thread](./phase-151-the-desk-chat/current-phase-status.md)** (plan: [`docs/internal/PLAN_PHASE_DESK_CHAT.md`](../../../docs/internal/PLAN_PHASE_DESK_CHAT.md)); DC-02 The Hands, DC-03 The Practice, DC-04 The Call, DC-05 The Crew stay parked here

**Disposition (2026-08-30):** the owner said "Let's impl it!" the same day the plan
was filed; Phase 151 chartered DC-01 (eight stories) and shipped it in one
sitting — the persisted thread ledger, `chat.turn` replacing `recipe.chat`,
the streaming seam inside the frozen-plan envelope, the turn route with
message-level People redaction at the coordinator's payload reconstruction
(close counsel M5), the Thread primitive + pullout + composer on the Desk,
threads as desk memory, the localStorage chat retired. Proven on real metal
(`.43` llama.cpp: first delta 0.98 s / 0.93 s over the bus) and on glass
(rig at 1440 + 393). DC-02+ remain candidates; the RFC §4.1 table is their
charter seed. The original filing, for the record:

Owner direction (2026-08-29): "how could we, realistically, port the
chat feature that warpdrv is based on into HoldSpeak? Basically,
augment HoldSpeak with the abilities this chat interface and features
really present themselves." The full RFC lives in the plan doc above;
this entry is the backlog handoff.

The short answer: no code moves (warpdrv is AGPL-3.0, HoldSpeak is
Apache-2.0) — the *grammar* moves onto machinery the desk already
owns. Roughly two-thirds of warpdrv's chat stack already exists here
under other names: the kernel's tool-turn lifecycle IS its approval
loop (with receipts), the Intelligence Router IS its server/preset
picker, the 82-tool MCP server IS its `warpmcp` (except ours knows
meetings, people, decisions and the Door), the WebSocket bus IS its
SSE fan-out, the FTS memory corpora ARE its workspace RAG, the
click-to-toggle mic IS its dictation. What HoldSpeak genuinely lacks
is small and named: a persisted thread/message model (today's chat is
`localStorage` only), token streaming end to end (the provider layer
returns blobs), a Thread primitive on the Desk, the chat-side tool
loop wired to the kernel, and TTS.

Five phases, each its own arc: **DC-01 The Thread** (tables,
streamed turns over the router, Thread primitive + pullout, composer
with mic/@-refs/attachments, branch on edit, Keep, FTS; ~8 stories,
one open-throttle arc) → **DC-02 The Hands** (model tool calls as
kernel tool turns over the in-process MCP families; receipt box in
yolo, Allow-once/always/Deny in safe; elicitation as a kernel
decision; desk-kind result renderers; status line) → **DC-03 The
Practice** (slash verbs on the registry, modes as recipes,
guardrails as a second cheaper assignment, annotations by voice,
`/compact`, todo = action items on the Door) → **DC-04 The Call**
(Kokoro TTS server-side, VAD, voice-call mode with visible state) →
**DC-05 The Crew** (subthreads on the conductor's run loop,
parent↔child notifications). NOT ported: llama-server lifecycle,
checkpoints, proxy, code graph, shell/file tools, nested thread
folders, sampler editors, external `mcp.json` client (optional
rider), Tauri/Chakra/assistant-ui.

Value-era fit: a chat is worth building only as a chat OVER the desk
— "what did I promise Ania last 1:1, is it done?", "draft Monday's
note from this week's three meetings", "move Tuesday's two open
items onto Marek's ledger" — answered in one thread, every effect
admitted and receipted, talkable on a walk. Feeds candidate A
(delegation lane) and W (Jira notes become groundable refs).

*Lands on:* `holdspeak/db/schema.py` (one additive block: `threads`,
`thread_messages`, `thread_message_parts`, `thread_refs`,
`thread_tool_policy`, FTS), `holdspeak/intel/providers.py` +
`InferenceRunner.run_stream` (the streaming seam),
`holdspeak/realtime_frames.py` (+3 frames), the sealed capability
registry (`chat.turn`, later `chat.guardrail`/`chat.compact`/
`chat.subthread`), `holdspeak/web/routes/threads.py` (new),
`web/src/lib/primitives.ts` + `web/src/desk/pullouts/ThreadPullout.tsx`
(new), the verb registry; retires `web/src/desk/chat.ts`.

**Open questions for the charter (§14 of the plan):** window vs.
pinned wing; yolo default for effect tools in chat; DC-03 before or
after DC-04; Kokoro server-side vs in-browser; any external MCP server
wanted on day one.


### AG. Phase 176 remainders — counsel-on-built's P2s (parked 2026-09-06, from assets/counsel-on-built-176.md)

- **HS-176 C5:** `APPLIED` can name a text rule that changed nothing (a case-only rule fires on already-correct text and is still recorded, corrections.py `apply_text_corrections`). Record a text rule's id only when the replacement differs from the matched span.
- **HS-176 C6:** the intent nudge's reinforce branch sets `corrected=True` even when the block and the confidence are unchanged (intent_router.py `_apply_correction_nudge`), so `APPLIED` can mark a nudge that did nothing. Mark only when it raised the confidence or changed the block.
- **HS-176 C7:** 17 of the 24 `MIC_ALLOWLIST` entries suppress nothing (the rule's `type` filter already excludes them). Trim to the load-bearing entries or fence that every entry suppresses at least one element.
- **HS-176 C8:** a pure insertion or deletion becomes a whole-sentence rule that fires only on that exact sentence, and the receipt still reads `TAUGHT`. Say `TAUGHT · PHRASE` for a whole-sentence rule, or refuse it by name.
- **HS-176 C9:** the Learned wing subscribes to `learning_event`, which a `text` teach never emits (`similar` is 0 for text and the broadcast is gated on it). Emit a frame for every stored rule, or subscribe to the journal frame.
- **HS-176 C10:** after `Forget`, an unresolved id in a still-mounted run renders an empty HEARD/SAID well (useSpeakDeck `appliedRules`). Drop unresolved ids.
- **HS-176 C11:** the footer receipt (`REHEARSED · NOT DELIVERED`) survives a wing switch and masks `N TODAY` on the Journal and Learned wings. Clear it on a wing switch.
- **HS-176 C12:** a teach that 500s after the store already wrote (`mark_corrected` unguarded) shows `REFUSED · nothing written` though a rule exists. Guard the post-write steps and report honestly.
- **HS-176 C13:** `Pipeline.run` returns before the correction seam when the pipeline is disabled, and the hotkey path returns before `run()` when the runtime is not loaded, so a purely lexical text rule silently does nothing on both. State it on the face or apply text rules on the passthrough too.
- **HS-176 C15:** the Journal row shows the transcript while search also matches `final_text`, so a hit's visible text can lack the needle (a `MATCHED · FINAL` token was added in the C2 fix; revisit the row's primary).
- **HS-176 C16:** a frame arriving between the initial GET and `setRows` was discarded (buffered in the C2 fix; keep an eye on the order).
- **HS-176 walk finding (his desk, read-only leg):** a journal row with an EMPTY transcript (Aug 21, 08:04, 357 MS, BROWSER) renders a blank primary on the Journal wing. Show the token `NO TEXT` in the primary when the transcript is empty (the opened row's preview already does).
- **HS-176 walk finding (his desk):** the Speak face reads `DICTATION · GPT 5 mini · API.OPENAI.COM · KEY NOT SET` — his dictation engine is a cloud engine without a key, so Talk cannot land until he sets the key or picks a local engine; the face says it honestly (the EgressChip and the KEY NOT SET token), nothing to build; noted for his attended walk's beat 0.
- **HS-176 counsel re-read N2:** a spoken Speak-face utterance journals with source `browser` (voice_stream.py) while the desktop hotkey journals `dictation`; ruled to keep, but the two names may deserve one word for "his voice" (SPOKEN) vs the typed dry run. Revisit with the owner.
- **HS-176 counsel re-read C3 note:** the widened secret guard (`_looks_secret`) drives the journal's whole-field redaction and the project-doc suggestions product-wide; zero false positives on fifteen architect sentences, but name it if a redaction surprises him.
- **HS-176 docs:** `docs/DICTATION_PIPELINE_GUIDE.md` §12 still describes the retired `/dictation` tabbed page and its Memory tab shots; a full rewrite is its own story. Two stale code comments: useSpeakDeck.ts calls the TEXT well "one StringGadget" (it is a PadGadget); DictationCore.tsx says Learned is imported outside the barrel (it is exported there).

### AH. PR #526 relationship-aware memory — merged 2026-09-06 with two notes

- **#526 footer receipt says the face's name twice:** the Desk memory face's footer reads `DESK MEMORY · RELATIONSHIP-AWARE` under a title bar that already says Desk memory (UX-CANON A.7). Kept at merge because it names the retrieval contract and the branch's test pins the string; rename the receipt to the contract alone on the next touch.
- **#526 Continuity charter parked as Phase 190** (renumbered from a colliding 162): 0/14, HS-190-01 blocked on owner ratification; not on the road (Phase 200 is).

### AI. Phase 200 G0 remainders (parked 2026-09-06 from HS-200-05's proof)

*Reconciled 2026-09-19 when HS-200-05 closed.* The owner ruled "all walks may be considered as passed", which closes the STORY. It does not close gaps 1-3: each is a code defect found by reading, not a walk beat, and the ruling accepts unwalked physical legs rather than repairing the journal/receipt link, the dropped target profile, or the mislabelled `failed`/`uncertain` outcome. They stay open and still want a destination. The walk question below was already retired on 2026-09-08 and is closed.

- **HS-200-05 gap 1:** the dictation journal row carries no delivery outcome; the delivery receipt lives in the kernel (desktop_typing.py's operation_id / state / target_ref) and nothing links the two. Closing it is a schema move (an operation_id column) after story 02 baked schema 76 into the runtime identity. Destination: a G1 story or a G0 addendum on his word.
- **HS-200-05 gap 2:** a pipeline-off hotkey row drops the target profile (`_journal_passthrough` in dictation_runner.py passes none; target detection runs only in the enabled branch).
- **HS-200-05 gap 3:** desktop_typing.py classifies an adapter exception as `failed`, not `uncertain`; the route above parks the claim pending so nothing double types, but the kernel receipt misnames a genuinely unknown outcome.
- **HS-200-05 walk question — RETIRED 2026-09-08 on the owner's word** ("I seriously don't give a shit"): an uncertain delivery stays never-automatic; the words wait in the well. Kept here as the record of the ruling, not as an open item.
- **HS-200-08 follow-up (the drafter's fallback receipt on the face):** the update face's FALLBACK_REASON_LABELS (web/src/features/project-room/update/model.ts) knows model_unavailable · no_output · unparseable_output but not `route_unresolved`, and does not yet show the row's `fallback_receipt` token (`DETERMINISTIC · ROUTE UNRESOLVED`). One web edit; story 11's face touch.
- **HS-200-04 note (from the census fence):** holdspeak/services/route_probe.py wraps `preview_route` and `adoption.admit` in a bare `except Exception`; the refusal is always named (the class name as a backstop) but a genuine resolver bug reaches the face as UNREACHABLE with a Python class name for a reason. Narrow to the resolver's typed errors.
- **HS-200-03 residual:** tests/integration/test_cadence_routes.py's fixture races the database singleton (reset then get as two steps); build the Database directly in the fixture.

### AJ. Phase 200 audit-story remainders (parked 2026-09-18 from HS-200-44/45/46)

- **Reach `bind_host` is decorative:** stored and echoed by the settings route, applied by nothing; no CIDR/peer check exists (`docs/SECURITY.md:277` stays `known_false` in the doc-claims registry). Wants the remote auth model story that HS-200-45 kept out of scope.
- **Verb-catalog mirror:** `holdspeak/mcp/resources.py` `_VERBS` is 45 of the face's 67 (22 missing, 0 phantoms once `go.*` from `applications.ts` is resolved); no parity test. Registry row unowned. The cheap half of the X11 read face.
- **`desk_snapshot` advertises "and layout"** and returns seven lists of rows. Either return layout or stop advertising it. Registry row unowned.
- **`holdspeak/doctor.py:251`** builds a bare `PrimitiveService(get_database())`; a CLI path with no hub to borrow from. Could report through the hub when one is running.
- **Restore under a live hub in `delete` journal mode still proceeds** (only the WAL case needed exclusivity; the lock-owner gate covers a cooperative hub). Consider refusing on any open connection regardless of mode for symmetry.
- **`ResourcefulService` is not composed on `WebContext`** (built in the conductor and a route), so its `on_changed` defaults to `composition.notify_desk_changed` rather than the hub's bound callback. Works; not the one-root shape.

## The model-era collapse (parked 2026-08-31, from the owner's question)

The #511 revolution collapsed the WEB platform's parallel authorities;
the BACKEND model system still runs two eras side by side: the legacy
`profiles` table (migrated intel/speech rows, `legacy-*` assignment
ids, its own freeze path) and the 143 Model Library/Assignments
(`model_profile_revisions`, versioned DeploymentRevision shapes — the
"v1/v2" seam INSIDE the new system). Every P0 found on 2026-08-31
lived in that seam (context_ceiling=0 from from_identity defaults, the
legacy route-freeze FK 500, swapped migration markers, downloads that
create artifacts but no assignable profile). The collapse: ONE profile
authority, legacy rows migrated forward and the legacy path deleted,
one DeploymentRevision shape, downloads that always yield an assignable
profile. Charter after Phase 156 proves the front door on the current
seams (156's apply is the natural migration driver). Owner's words:
"didn't we get rid of the whole compat kind of thing with that big
revolution?" — the backend still owes him that revolution.

- **Concierge apply in one transaction** (from HS-170-03, 2026-09-05): `POST /api/concierge/apply` writes per group through the `set_assignment` CAS path like the front door; an atomic seven-group write needs a new InferenceAssignmentService method. Fold into the next Settings→Models pass.

- **The Monday brief carries the kernel operation ledger as "waiting" items** (found on the owner's real desk 2026-09-05 by live170_walk.py: 1837 `Service.method` rows). The arrival filters them client-side (ChairHome.tsx RAW_ID_RE) and caps at 3 + `N more`; the SOURCE fix — the brief service must not emit kernel operations as owner-facing items — belongs to Phase 171 story 06 (the brief recurring).

- **settingsModels.tsx (`ModelsModule`) is dead code** after HS-170-03 (its SettingsCore import is parked; nothing else imports it; frontDoor.tsx renders its own FrontDoorView). Park under `_parked/` in the next Settings pass — never delete.

- **The Concierge rig inherits the retired Models/Assignments rig intents** (HS-170-07, 2026-09-05): 25 tests across test_hs141_models_setup / hs142_model_acquisition / hs143_assignments / hs143_model_library were retired with module skips when the faces were parked. Their intents — download → verify → add WITHOUT assigning; the assignment editor's next-run preview + conflict (409) path; keyboard-only owner paths + accessibility; zoom 200% + reduced motion; provider custody retaining retries + assignment heads; a broken engine's repair visible — must be re-asserted on the Concierge (tests/e2e/test_hs170_concierge_glass.py) in the next Settings pass.

- **Notification click target needs the app bundle** (HS-171-05, 2026-09-05): `osascript display notification` cannot carry a click action; `UNUserNotificationCenter` requires a bundled app identity. When HoldSpeak ships as a .app (174/179 packaging), route the banner through the bundle so one click opens the shade.

- **The dock status rail truncates** (`RAILS NEEDS Y… 8 RUNS 200` on the owner's desk, seen by live171_walk.py 2026-09-05) — a pre-170 surface the census did not rank; a face with a truncated label and bare numbers. Fold into the next pass (171-10 close notes it; 178 The Portfolio touches the rail).

- **HS-172 auto-run on import.** The auto-intel trigger (routing_glue.py `_maybe_auto_enqueue_intel`) fires only on capture stop; imported transcripts (meeting_import.py) do not pass the same save flow. Wire the same setting there when import earns a Tuesday.
- **HS-172 two "proposals" vocabularies on the meeting.** `GET /api/meetings/{id}/proposals` is the aftercare ACTUATOR proposals (Slack/GitHub/webhook effects); follow-through proposals live at `/api/meetings/{id}/follow-through-proposals`. One word, two tables; rename the actuator route when the actuator era is revisited.
- **HS-172 `Run all` on Settings → Meetings.** Cut from 172 by counsel finding F7: a batch intelligence run may egress to a paid host. Per-meeting `Run intelligence` stands. Revisit with a host-named confirm row.
- **People window prose caption.** The 138 People window still carries `Encrypted · Local storage · Notes only` under its title bar (seen in the 172 build shots). UX-CANON says no prose and no privacy novels: fold it into the footer's `THIS DEVICE` chip + a `NOTES ONLY` token when the People face next gets a pass.
- **Room Ask-well MODEL chip shows a profile label.** Seen on the owner's desk in the 173 walk: `MODEL · MIGRATED INTEL ENDPOINT` in the Room's Ask well (169 face) — 172's law says a chip names the host via `egressFor(host)`; route the Ask well's chip through the same helper and the recorded host.
- **`NA · CAN'T CHECK · Remove` source row.** The meeting-activity pseudo-source row (`No local adapter for meeting activity yet`) still renders a prose caption and a `Remove` verb on the owner's desk; fold it into a token or retire the pseudo-source.
- **CI runner environment is red on main** (seen 2026-09-05 while merging #553–#556 on the owner's word): the GitHub Actions Unit job fails on a fixed environment set — no speech engine on the runner (`SpeechSessionRefused: no_assignment`, `mlx_whisper` missing, PortAudio missing), the Q6 model file absent (`test_ask_runner_migration`), the two kernel broker density fences, product-copy drift, `test_web_runtime_warms_transcriber_on_start` — plus a rotating flaky family (hs144 door glass, hs153 practice glass, the workbench preset facade). DeskOS Web Quality also exits 1 on main. The merge gate is the local CI-shape suite (6 inherited) + his word; Actions is not read as a gate until this is paid. A phase of its own: mark the speech/model tests as `requires_local_speech` skips on the runner, pay or baseline the two fences, and make the web quality job's failure legible.
- **HS-175 Settings → Meetings: the Intelligence row overlaps its caption at 393.** Pre-existing from 172 (evidence: phase-172 `build-settings-meetings-nomodel-393.png` and phase-175 `story-03-shots/settings-calendar-393.png`): the `AFTER ROOM MEETINGS` CycleGadget + `Choose model` Button run inline over the `CAPTURE + EXPORT` caption under the `surface` container query. More than placement — the GadgetRow child layout at narrow widths is systemic across Settings modules (SettingsCore.tsx ~:1207). Re-target: the next face pass that owns the GadgetRow species.
- **HS-175 calendar sources carry no per-source refresh status.** `GET /api/calendar/sources` reports `success` when events exist and `idle` when never read; a failed HTTPS fetch is not persisted per source, so the row's StateChip cannot say `failure` honestly. Pay by persisting last-refresh outcome per source in the ingest conductor. Re-target: 176's hygiene lane or the next calendar touch.
- **HS-175 the `Snapshot` verb on the Connect calendar row is a board deviation.** The ratified SettingsMeetingsCalendar board shows `Add` only; the build keeps the existing vision-adapter entry (`/api/calendar/snapshot` → `review-calendar-snapshot`) beside it as a ghost dense Button because a working verb is never dropped. Counsel-on-built rules whether it stays there or moves.
- **HS-175 `matched_this_week` counts on UTC week boundaries** (calendar_sources.py); the owner's local week can straddle differently at the edges. Pay when the desk gains a single week-boundary helper shared by the strip, the Room row and the brief.
- **HS-175 walk finding: earlier walks seeded the owner's REAL database.** Two `Sprint Review · 2026-08-20` meetings on his arrival are seed rows (`m-glass-167-walk`, `m-168-walk-001`) left by the 167/168 walks. The 175 runner is read-only and found them. They are his rows to delete (never ours); the law stands — a walk on his desk writes nothing, and a rig seeds only an isolated HOME. Sweep other walk-era ids (`%-walk%`, `%glass%`) with him at his sitting.
- **HS-175 walk finding: the arrival's recorded-meetings row prints `0 MIN`** (`Already titled · AUG 22 · 0 MIN · QUEUED`, 172's row grammar) — a counter of zero (UX-CANON A.8) on a real desk. Omit the duration token at zero. Re-target: the next arrival touch.
- **HS-175 counsel C10, second face:** `CalendarSnapshotReviewCore.tsx` (the snapshot review) does not yet show the vision model's EgressChip before the upload; Settings' `Snapshot` verb does (`calendar-snapshot-egress`). Pay on the next snapshot touch with the same `snapshot_egress` field.
- **HS-175 board text vs build:** the ratified SettingsMeetingsCalendar mockup still reads `2 CALENDARS` while the build (counsel C9) says `N EVENTS` (it counts distinct event uids). The board's PNG was re-exported; the `.dc.html` text was left as ratified. Reconcile at the owner's sitting.
- **HS-175 the Room's meeting row has no `Retire` on the face** (the board shows `Pause` only); Retire is proven via the API in the rig and is a tombstone (a retired meeting Watch is never recreated by link or sweep). Add the verb only if the owner wants it on the row.
- **HS-175 counsel re-read P2s (parked, not paid in 175):** the brief's DUE row still carries `due_at` inside `detail` as `text | YYYY-MM-DD` (give it its own field); two ISO boundary shapes (`…Z` vs `…+00:00`) for one instant across the door/sources/Room payloads (one helper); dead `match_source != 'suppressed'` clauses after the suppression table; the manual-link rebind re-arms at −60 s instead of −lead on a time change; Disable → Enable of a source drops its manual links (if not paid by W3).
- **THE CANON GUARD IS BLIND TO THE OWNER'S OWN RULING** (found 2026-09-07 by HS-200-10's trace lane, measured by the orchestrator). Rule A1 of `scripts/ux_canon_scan.py:429` matches `r'<button[\s>/]'` **per line**, over `content.splitlines()` (`:713`) — so the newline is already stripped, and a tag Prettier wrote as `<button` alone on its line never matches. Prettier writes almost every raw button that way. Measured over non-test `.tsx` under `web/src`, excluding the library's own `Signal.tsx` and `gadgets.tsx`: **the scanner sees 9 of 206 raw `<button>` tags, across 77 files.** `tests/ux_canon_ceiling.json` records `A1: 4` with a four-entry allowlist, so `test_hard_zeros` and the ratchet have been passing over a census that is ~96% blind. The blindest faces: `WorkbenchWindow.tsx` (23 invisible), `DeskEditor.tsx` (11), `DeskToolInspector.tsx` (10), `window/Dock.tsx` (7), `SessionPullout.tsx` (6). This is the guard for **his** standing ruling — every verb is the library Button; a raw `<button>` is a bounce — and it has not been enforcing it. NOT paid in HS-200-10: the one-character fix (`r'<button\b'`) takes A1 from 4 to ~206 and fails the ratchet on the spot, and the honest repair is a conversion campaign, not a regex. A phase of its own: fix the regex, re-baseline A1 to the true number in one commit that states the number out loud, then convert by surface, ratcheting down. Note the ratchet does not "rise" here — the debt was always in the tree; only the count was wrong.
- **The `Promote` verb owes a board, and the Interview panel owes a canon pass** (from HS-200-10's wire design, 2026-09-07). Story 10 ships the promotion wire with no new face control, because a verb the owner clicks needs a ratified board first (face canon) and none of the 22 ratified daily-workflow artboards draws promotion. The surface it would land on, `InterviewPanel.tsx:120-131`, already renders the quote and a `Remove` Button but is pre-Surface-canon — a raw `<details>` and a `Select` where the library has `Disclosure` and `CycleGadget`. Pay both together: draw the promote row on a board, ratify it, and bring the panel onto the surface species in the same pass.
- **SPECIES BUG: two competing definitions of `secondary` inside the library Button** (measured 2026-09-07 in HS-200-41's composer lane). `web/src/styles/global.css:162` sets `:where(.btn--secondary){background: var(--canvas-raised)}` and the later materials-spike rule at `:616-621` overrides it — `.btn--secondary, .btn:not(.btn--primary):not(.btn--ghost):not(.btn--danger) { background: var(--wash-2); … }`. `--wash-2` is `rgba(255,255,255,0.05)` (`tokens.css:230`), a translucent wash, while the chip grammar beside it is the opaque `--surface-2: #1c1f27` (`tokens.css:86`, applied at `desk/components/chrome-menus.css:263-278`). So a `secondary` verb can never match the chips it sits among, and every face that needs a chip-looking verb reaches for `ghost` instead — which is why `variant="ghost" + className="desk-chip"` has become the in-tree idiom (`ThoughtContextPicker.tsx:199,202,203`, `ThoughtDocumentPane.tsx:97-99`). This is exactly the lead/primary species split the owner ruled is fixed in the species and never in the face. NOT paid in 41: blast radius counted by parsing every `<Button>` opening tag across `web/src/**/*.tsx` — **593 sites (384 ghost, 108 primary, 79 variantless and therefore secondary, 14 dynamic-variant, 6 danger, 2 explicit secondary)** plus 11 raw `className` strings carrying a bare `.btn`, so **81-106 rendered buttons would change background**. Its own pass: reconcile the two rules, decide what `secondary` means beside a chip, then retire the `ghost + desk-chip` workaround face by face with shots at both widths.
- **`.desk-next .desk-chip` has no disabled rule** (found the same day): a disabled chip-classed verb renders as if it were live. Paid narrowly for the Thread composer inside HS-200-41; the class is used elsewhere and wants the same treatment when those surfaces are next touched.
- **Auto-retrieval is invisible on the face** (found 2026-09-07 by counsel on HS-200-10's design, verified by the orchestrator). Whenever a Thread message or a Thought refinement carries no explicitly attached source, `holdspeak/grounding.py:188-197` runs a global relevance search over the owner's whole corpus, takes up to 16 hits (`GROUNDING_MAX_REFS`), hydrates note bodies **whole** through `:313-321`, and freezes them into `thread_refs.frozen_json` with `"sensitive": False` (`thread_service.py:397-408`) to be replayed to the model as a system message (`:2095-2107`). This is the product working as designed — his notes inform his prompts — but **nothing on the face distinguishes a block the desk retrieved by relevance from one he attached himself**, and on his real desk the corpus is 17 notes against 16 retrieval slots, so nearly every note is a candidate on nearly every message. Not a leak of protected material (People lives in a ciphertext sidecar with no tables in the main schema), and not this story's to fix. Pay it where the Thread and Room faces are next touched: name the retrieved set as retrieved, with its count and a way to see what was pulled. It is walkable today with no new code — type a message matching an existing note and read `thread_refs.frozen_json`.
- **Steering a coder agent with nothing picked sends up to 16 relevance-chosen notes into its pane** (found 2026-09-07 by the HS-200-10 design lane's reach sweep; the chain verified by the orchestrator). `buildGrounding` (`web/src/desk/grounding.ts:105-122`) returns **null when both the desk selection and the rails picks are empty** — its own docstring says so — which is the ordinary case of simply typing a sentence to the agent. The one production call site passes that null through (`SessionPullout.tsx:451`), the hub reads `grounding is None` (`holdspeak/web/routes/system/coder_steering_support.py:103-105`) and calls `hydrate_refs(principal, [], [], "summary", query=text)`, which is exactly the unattached condition that fires `grounding.py:188-197`'s global relevance pass. The chosen note bodies are composed into the text by `compose_steer` and delivered as `terminal.text` into the agent's pane (`coder_steering_routes.py:424-433`). The agent is third-party and forwards its own context onward, so this is the one relevance path that leaves the machine. Custody is not absent — the delivery carries a policy, a `steering_commitment`, an `audit_id`, and the receipt records `composed["refs"]` — so this is a DISCLOSURE question, not an unaudited egress: **what is not established is whether the face names the retrieved set BEFORE he presses send.** The orchestrator verified the selection chain and the receipt's existence, and did NOT verify the pre-send face. Pay it with the auto-retrieval disclosure item above, and treat this call site as the sharpest instance: name the count and let him see what was pulled, before it goes. **Counsel sharpened the obligation on re-read (2026-09-07):** the framing above is right on the ledger law — policy and commitment at `coder_steering_routes.py:418-421`, `grounding_refs` in the payload at `:431`, `audit_id` at `:434` are disclosure with provenance. Where it falls one step short is a FACE law: UX-CANON A.9 puts the badge at composition time, and because nothing was picked there are no chips on the face at the moment relevance is about to type sixteen sources into a third-party pane. That is the specific missing half the owning story inherits.
- **SYSTEMIC, UNAUDITED: does any other device-local fence fail to travel over sync?** (raised 2026-09-07 by HS-200-10's design lane while paying counsel's P0-C, and explicitly outside that story's scope.) The shape of P0-C: a guard is enforced by the presence of a row in one table, while the *content* it guards is synced by another (`SYNC_REGISTRY` syncs `note` with `body_markdown` merged — `holdspeak/services/sync_service.py:35`, `:120`, `:664-671`). On the receiving device the guard's row is absent, so the guard silently does not exist and the content lands unfenced. HS-200-10 pays its own instance by giving `context_promotions` a `SyncKindSpec` ordered before `note`, with a monotone merge in which `revoked` beats `active` regardless of timestamp and a promotion row is never tombstoned by sync. **Nobody has swept the repo for other fences of that shape** — neither the design lane nor counsel, and it is the more worrying question. Candidates to check first are every guard keyed on the existence of a row in a table absent from `SYNC_REGISTRY`, and every suppression or tombstone side-table (the calendar link suppressions of 175 are the obvious one). A pass of its own: enumerate the registry, enumerate the fences, and prove each fence either travels or is provably device-scoped by intent.
- **HS-200-07's coverage token rides the command deck's badge slot, and hs171's zero-badge law catches it** (classified 2026-09-07 while triaging HS-200-41's suite run; INHERITED on main, not that story's). `DeskToolShelf.tsx:241-243` reads `const badge = needs && needs > 0 ? \`${needs} NEED YOU\` : projectCoverage[project.id]` — so a Project with **zero** needs-you items but incomplete coverage still draws a badge. That is deliberate: `a576e178` (HS-200-07) says in its own message that "the deck badges an unobserved Room's repair token". But `tests/e2e/test_hs171_command_deck_glass.py:280-281` asserts a zero-item Project has **no** badge, and it fails at both widths, serially, on main — verified by reading the blame rather than by assumption, and `DeskToolShelf.tsx` is untouched by 200-41. Somebody must rule which law wins: a coverage state token is not a counter of zero (A.8 is not breached by showing it), so the likely answer is that hs171's assertion is now too strict and should distinguish a count badge from a state badge. Until then it is two known-red e2e legs on main. Re-target: whoever next touches the deck or 200-07's coverage surface.
- **HS-200-41 leftovers, small and named** (2026-09-07): (a) `save_ask(..., host_id=, lease_epoch=)` and `list_unfinished_asks(..., host_id=)` still accept those arguments and the routes still pass them, but custody now reads a persisted machine identity instead — so `custody_lease_epoch`, a per-process epoch, sits beside a durable machine id, which is a meaningless pairing. Nothing reads it; it is misleading to the next reader, not broken. Retire the parameters and the column on the next touch of that service. (b) `tests/e2e/glass_infra.py:178-233` `_boot` returns `server.start()` with **no readiness wait**, so a module's first `_http` call can hit a hub that is not yet listening — seen once as `urllib.error.URLError: [Errno 61] Connection refused` during HS-200-41's rig runs, distinct from the custody flake that was fixed. Every glass rig in the repo inherits it. Pay it with a readiness poll in `_boot`, where one fix serves every rig.
- **The macOS permission deep link, costed and deliberately not taken** (HS-200-05, 2026-09-07). `holdspeak/desktop_permissions.py:73-75` carries a `settings_url` per pane (`x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone` / `?Privacy_ListenEvent` / `?Privacy_Accessibility`) and the face does NOT spend it. Ruled: the path tokens are drawn instead, and the only verb is `Re-check`. Two costs decided it. (a) `?Privacy_ListenEvent` is an **undocumented anchor that has drifted across macOS releases**, so a verb built on it opens the wrong pane silently the day it breaks, misleading exactly the person who is already confused about why their hotkey is dead; the path tokens never rot. (b) Spending it from the hub crosses the privileged-effect boundary (`open(1)`/`NSWorkspace`) and would want a receipt like any other actuator; spending it from the browser as an `<a href>` avoids that entirely but is a raw anchor, which is an A1 canon bounce unless the library `Button` (`web/src/components/signal/Signal.tsx:21`) gains an href-capable variant — a library decision that should not be made as a side effect of a voice story. The URL stays on the wire unspent, so whichever way a future story rules, the edit is small. Re-target: a first-run permissions flow, if one is ever chartered.
- **A first-run macOS permissions flow is the real fix; documentation is the survivable one** (raised 2026-09-07 while paying HS-200-05's silent-hotkey defect). Voice typing needs three separate grants (Microphone, Input Monitoring, Accessibility), attributed to **the launching application** rather than to HoldSpeak, each requiring that application to restart before it takes. HS-200-05 makes the failure legible after the fact and GETTING_STARTED/USER_GUIDE now name the panes, the attribution trap and the relaunch. Neither makes it *good*: a new installer still meets three system panes with no guidance until something has already silently failed. The Concierge already walks someone through model readiness with named repair states and one verb each; the same grammar fits permissions exactly. Its own story.
- **HS-200-42 counsel leftovers, parked by the orchestrator (2026-09-14):** (a) the intel drainer's stop joins for up to 60 s **inside the async app shutdown hook** (`web_server.py` `_shutdown`), so a quit during a live model call stalls the uvicorn loop for that long — custody is correct (the database owner lock is released only after the conductors stop, `runtime/ownership.py` `_stop_writers_and_release_database`), the quit experience is the cost; the fix is to run the conductor joins off the loop thread. (b) `BoundDeferredIntelJob.egress_model_host` names route leg 1 only (`ORDER BY route_leg_ordinal LIMIT 1`) while the schema permits four legs; a run that falls through to leg 2 egresses to a host the receipt does not name — unverified whether `meeting.deferred_analysis` plans are ever multi-leg; if they are, the receipt must be restated on the leg actually taken. (c) Unknown-Stop-recovery rows still supersede once on first claim and lose `recovery_origin_job_id` from the successor's `displaced_work` (the `origin_job_id` column keeps the link); bounded to one extra row. (d) `holdspeak/db/connection.py` sets no `busy_timeout` and runs `journal_mode=delete` while the drainer is now the first CONTINUOUS writer thread — HS-200-45's territory, named in the audit.
- **A watch's chosen cadence preset never reaches the column the scheduler reads** (found 2026-09-14 by HS-200-43's research lane; verified by grep, not fixed — the story's scope excludes the cadence model). The Door, the Interview and the templates choose a preset from `github_templates.py:37-42` (`active_work` 15 min, 35, 1440, 1440) and write it into `trigger_json` as `{"kind":"poll","every_minutes":N}` (`project_service.py:2360`). `evaluate_due` reads only the `evaluation_cadence_minutes` column (`watch_service.py:911`, `:988-990`), `NOT NULL DEFAULT 60` (`db/schema.py:2492`), and nothing in the package copies `every_minutes` into it. So every Door/Interview watch runs hourly whatever the owner picked, and HS-200-43's arming fix alone does not give `active_work` its fifteen minutes. Two cadences for one watch is the defect; the fix is one cadence — copy the preset into the column at creation (and in a backfill for rows on disk) or make the column the only place the preset lives. Note also the ruling in HS-200-43: the heartbeat is the single scheduler, so the real floor is `sweep_every_minutes` (default 15) regardless of either value. Re-target: the next story that touches watch creation or the cadence row on the Room face.
- **The unattended sweep's ceiling is 40 watch evaluations an hour, and no face says so** (HS-200-43 counsel re-read, 2026-09-14). `WATCH_SWEEP_MAX = 10` per sweep × `sweep_every_minutes` (default 15) is a hard ceiling; at ~30 watches on the 60-minute column default the owner's desk sits at 75% of it, and a desk near 45 watches backlogs permanently with `watches_deferred` climbing on every heartbeat receipt and nothing on a face reading it. The owner's explicit Run now is exempt (unbounded, and it overrides quiet hours). Compounds the cadence-preset entry above (every watch runs on the 60-minute default regardless of preset). Pay together: surface `watches_deferred` on the Rhythm row, and let the preset reach the column so the ceiling is spent on the watches he chose to run often.



## HS-201-08 verification follow-ups — 2026-09-20 UTC

- **Guardrail reason on reload (Phase 153):** the persisted guardrail part is not hydrated into guardrailRows. Deny remains primary and focused, but its reason disappears after reload. Keep the ratified violation-row species; design/check this separately. Tenet 3. Evidence: [HS-201-08](phase-201-one-meeting-result/evidence-story-08.md).
- **Observer fixture writer (Phase 200 isolation):** test_124_verify_round3::test_pipeline_events_without_filters_returns_recent_events substitutes the MCP DB but not observer_or()'s default observer fallback. Unit CI HOME isolation contains the writes; the fixture leak remains open.
- **Database file identity (Phase 200 runtime identity):** inode reuse can hide replacement from database_identity(). Desk custody uses durable machine identity; that file-identity contract remains separate.
- **Philo maintenance:** #589's references were stale against merged Phase 201 source. Line and comment drift makes checks fragile; up to 57/190 Python anchors may differ from definition lines (some intentionally point into bodies). The validator checks bounds and symbol presence, not symbol-at-line. Review separately; no extra anchors or validator change in story 08. OpenAPI's existing unit guard covers a generator not listed in the docs job. The supplementary API collector misses nested router-path handlers (summary-selection has empty handler_evidence); generic contract fields correctly remain uncertified.
- **Roadmap list cost:** two DW subprocesses per project, each with a 20-second timeout. The null result is fixed; malformed producer JSON shapes are outside the current contract and remain unguarded. No generic schema layer added.
- **Startup timeout:** a thread that outlives the bounded failure join remains owned and a repeat start refuses until it exits. No process is killed.
- **Full-suite scheduling:** default xdist load left one worker with most glass work. Evaluate work stealing for the documented fast lane after story 08's complete result; CI remains serial.

### HS-201-08 — Descriptor pressure in long-lived test workers

The complete worksteal run reached a valid pipe descriptor above select’s 1,024 limit. Story 08 fixes the test’s invalid wait assumption; it does not identify or repair the source of accumulated descriptors. Follow up with per-module descriptor counts and hub/SQLite/browser/socket teardown checks. This is also an unverified long-lived-hub risk, not only suite hygiene. Before story 08, the nearby test_hs174_remote_settings_glass.py rig started servers without a stop fixture; a private four-boot probe increased descriptors 4 → 49, then explicit stops reduced them to 29. Story 08 now stops that fixture; the broader descriptor source is still untraced. That is a contributor candidate, not proof of the failing worker’s history. Home: Phase 201 evidence-story-08 and checks/story-08-send-muaddib.md.

### HS-201-08 — Credential store isolation and continuity limits

The remote-settings glass fixture now owns a private process-local AgentCredentialStore. The real runner-loopback tests are confirmed producers of leftover credentials; other multi-hub rigs still need their own isolation. No global clearing or production-store change is claimed. In-process hub restart token retention has not been ruled on; the existing store is process-scoped, not persisted to HOME.

Day 2 continuity is proven from a seeded day-1 state. The current first-use summary path does not create the decision or commitment that day 2 carries. Story 08 directly pins analysis-only output, then invokes the actual retained plugins and bridge as a labelled historical fixture. Restoring owner-created follow-through remains “Phase 201 parked summary follow-through” above; the test does not restore that production entry.

The scoped fixture scan found eight e2e `setup` methods that call `_boot` without `.stop` in the same function. HS-174 remote settings is repaired in story 08. Seven candidates remain: hs172_arrival:171, hs172_settings_meetings:63, hs170_meetings:209, hs175_settings_meetings:246, hs172_meeting:161/:306, hs175_arrival:457 (all tests/e2e files). This syntax scan does not rule out teardown elsewhere; investigate before calling them leaks.

Story 08's daily fixture records actual plugin structured output but supplies artifact type, title, status, confidence and sources as fixture envelope values; it writes no plugin-run row and bypasses `synthesize_meeting_artifacts`. Re-prove plugin-run persistence → synthesis → recording → bridge as one chain when the parked entry returns. Day-2 faces that read envelope fields see fixture values. The e2e-to-unit fixture import is an existing coupling pattern; moving plugin_dispatch_rig will also affect this e2e walk. No current owner creation path is proven by this rig.

**Evidence churn:** every full run rewrites hundreds of tracked shots. The remote-settings post-revoke shot also leaves two new PNGs in closed Phase 174. Point that rig at story-08 output or make shot writing opt-in in its next change. Story 08 restores unrelated tracked outputs with `git show` and parks new files; this cosmetic follow-up does not change the verified runtime inputs.

## PHILO-5-01 follow-ups — 2026-09-24 (Astra's check on built, finding 8)

| Item | Kind | Source | Home |
|---|---|---|---|
| The Info-window rename of a decision does nothing: the face sends `name` (`web/src/desk/components/InfoWindow.tsx:31`), `decision.update` ignores it, and the title stays (fenced as observed: `tests/unit/test_philo5_one_decision.py:155`, `tests/unit/test_philo5_compat.py:96`). Fix: send `title` for a decision, or map `name` to `title` for that kind. | bug (Tenet 3; UX-CANON A11) | `holdspeak-philo/phase-5-the-one-service-layer/checks/story-01-built-astra.md` finding 8 | parked; ledger line in the phase's "Decisions deferred" |
| The admission gap: a real Codex `desk.create kind=decisions` write made the decision and ZERO kernel operations and ZERO receipts (Astra's `admission-proof.json`). `decision.create`/`decision.update` over HTTP and MCP admit nothing. Inherited Article XI debt, not made by the contract. | admission debt (Article XI) | same check, finding 8 | named in the phase's "Discovered missing admissions"; resolution in PHILO-5-02's effects acceptance |

## PHILO-5-02 follow-ups — 2026-09-24 (Astra's check on built, finding 4)

| Item | Kind | Source | Home |
|---|---|---|---|
| INHERITED DEBT (Article XI): `decision.create`/`decision.update` leave no kernel operation and no receipt through either transport (HTTP `/api/decisions`, MCP `desk.create`/`desk.update` `kind=decisions`). Article XI.1 names "acts under Article V" as a trigger, and Article V.1 names filing; XI.4 makes the owner's own gesture approval; XI.5 exempts computation without effect, never effects. Whether a desk decision write "acts under Article V" (filing) is UNRULED. The same question stands for every other desk-primitive write and the decision lifecycle transitions. `tests/unit/test_philo5_the_loop.py:618` is CHARACTERIZATION ONLY (both transports leave the same zero). Pay: the owner rules the question; if it is consequential, a later phase admits the desk writes through the kernel (one kernel operation per write, a receipt each) and replaces the characterization test with an admission fence. | admission debt (Article XI), owner ruling owed | `holdspeak-philo/phase-5-the-one-service-layer/checks/story-02-built-astra.md` finding 4 (supersedes the PHILO-5-01 row's "resolution in PHILO-5-02's effects acceptance") | assigned to the owner's ruling, then a later phase; ledger line in the phase's "Decisions deferred" |

## PHILO-5-04 follow-ups — 2026-09-24 (Muad'Dib's counsel on built, PR #638)

| Item | Kind | Source | Home |
|---|---|---|---|
| Shelf invalid-state: the MCP transport enum (`holdspeak/mcp/tools.py:459`) refuses before the registry, while the descriptor (`holdspeak/operations.py:421-423`) says it will not pre-empt. Align transport and contract; real-producer red/green alignment fence. Never count the refused branch as registry reach. | contract drift (Tenet 3) | lane-report-story-04 ledger row 1; story-03 shelf counsel | product follow-up owed |
| Missing-decision HTTP fallback (`holdspeak/web/routes/decisions.py:58-61`) records two observer failures (PrimitiveService + DecisionLifecycleService) for one missing id; the brief collector (`monday_brief_service.py:577-593`) then says two things broke. HTTP/op parity FAIL 2:1. Settle legacy-id dispatch without dropping legacy reads; one cause, one row; fence red before the fix. | Article VI / XI compat debt | ledger row 2; `assets/story-04-shots/carried/verification/missing-*-rows.txt` | product follow-up owed |
| Failed import shown as SAVED: `web/src/desk/chair/intelBadge.ts:26` returns SAVED for unmapped intel states; `ChairHome.tsx:265` never passes the transcription status `import_failed` (`meeting_service.py:315`). No canvas needed (the existing failure idiom). The fix + a rendered fence red before the fix is owed; the fence-as-observed was NOT delivered. | the face lies (Tenets 3/4, Art. VI) | ledger row 3; story-03 glass review | product follow-up owed |
| Transient "MEETING READY · N open · 0 decided" toast: a zero count (`AmbientLayer.tsx:175`, `intelligenceAttention.ts:95-96`) breaks UX-CANON A.8; at 393 the toast covers the summary text and the capture bar (`final/…/shots/summary/393-after.png`). Omit zero tokens; no overlap; rendered transition proof. | UX-CANON A.8; the no-overlap rule | ledger row 4 | PAID by PHILO-6-03 (#649; the zero omission via #647) |
| Brief count and time conflict on every fresh arrival: "5 THINGS WAITING" vs "Brief ready · 6 items" (`briefEgress.tsx:43-52` counts raw sections; `ChairHome.tsx:875-886` filters); "GENERATED SEP 25 18:19" vs "6:19 PM" (`routes/monday_brief.py:47-58`). Made visible on every fresh read by the PHILO-5-04 receipt seam. One count, one time format; rendered red/green. | Article III receipt; Tenets 3/4 | ledger row 5; `final/…/shots/brief/1440.png` | product follow-up owed |
| Raw pipeline item `MeetingIntelService.run_intelligence` stored as a brief item (`monday_brief_service.py:500`), counted by the receipt, filtered from the Arrival (`ChairHome.tsx:884-886`); whether "2 more" renders it is unwalked. Human producer wording; a consistent-count fence. | product language (Tenet 4) | ledger row 6; `final/…/observations/brief.json` | product follow-up owed |
| MCP discoverability: the Codex client needed 25 repository reads and 201 s to learn that "a decision on my review list" is `desk.create kind=decisions status=proposed`. A client without the repo would not find it. The catalogue must name the review-list decision path in its tool descriptions. | Tenet 3 (help and accelerate) | Muad'Dib's counsel MISSED; `final/…/codex/decision_thought/events.jsonl` | product follow-up owed |
| S4 decision pullout after Done shows an empty DECISION body for ~1 s at 393 (0.95 s empty, 1.363 s readable; 1440 readable at 0.955 s); suspected seam `DecisionPullout.tsx:69-71` (leaves edit mode before the refreshed record lands). Confirm the cause; render the saved text at once. | face flash (Tenet 3) | `assets/story-04-shots/carried/s4-*/observation.json` | product follow-up owed |

## PHILO-6 follow-ups — 2026-09-24 night (Astra's check on built, lane A, PR #646; `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/checks/lane-a-built-astra.md`)

| Item | Kind | Source | Home |
|---|---|---|---|
| Inherited badge holes: `importing` (`holdspeak/services/meeting_service.py:198,297`), `refused` (`holdspeak/meeting_session/intel_admission.py:93`) and `live` (`holdspeak/meeting_session/live_readiness.py:82`) still fall to the SAVED fallback (`web/src/desk/chair/intelBadge.ts`, `map[s] ?? "SAVED"`). Only `import_failed` is mapped (PHILO-6-01). Each needs a word decision (existing idioms first) and a rendered fence red first. | the face lies (Tenet 3) | Astra's check on built, finding 2; `evidence-story-01.md` "Not claimed" | ASSIGNED: Muad'Dib (the Arrival lane, owns `ChairHome.tsx`/`intelBadge.ts`); the first repair story chartered after Phase 6 closes |
| The Phase 5 rehearsal driver (`scripts/philo5_his_words.py`) fails MCP resource-list reconciliation after a correct `desk.create` (`MCP exchange reconciliation for 'list_mcp_resource_templates' found no unused matching /api/…`). Inherited: reproduced by Astra on the unchanged driver (branch `f6c0c0d1`: MCP created `decision_d3dc1cebef9e`, then the reconciliation failed). The driver must reconcile resource-list/template calls or exclude them honestly. | rehearsal driver defect (Tenet 3) | Astra's check on built, finding 6; `assets/story-02-shots/rehearsal/blocked/` | PAID: PR #653 (fix/philo5-driver-resource-reconcile) |
| The driver's tool-selection failure (Codex chose `door.add_item`, a follow-through task, where the driver expects `desk.create`; reproduced on main `66205729`) is the existing PHILO-5-04 "MCP discoverability" row above; not a second row. | cross-reference | Astra's check on built, finding 6 | Phase 7 story 01 / story 04 (the phase status "Out" list) |
| The Brief view (the fold's destination) shows the observer's raw argument JSON (`{"meeting_id":"…","expected_selection_hash":null}`) and the raw exception repr (`LookupError('Unknown brief item: …')`, `route_unavailable: ConflictError(…)`, `KeyError('…')`) as row details; at 393 the JSON runs past the right edge (`assets/story-02-shots/after-branch/*-393/after.png`). Human detail words (Tenet 4) and no overflow at 393. | product language + overflow (Tenets 3/4) | Astra's check on built, MISSED 3; `evidence-story-02.md` "Not claimed" | ASSIGNED: Muad'Dib (lane A), the Brief-view detail story chartered after Phase 6 closes; the owner sees it at exit 4 as disclosed debt |

## PHILO-6 lane A follow-ups — 2026-09-24 night (Astra r3 on PR #646)

| Item | Kind | Source | Home |
|---|---|---|---|
| Double-Broke: a real `create_from_meeting` whose child INSERT is rejected produces TWO identical `Decision did not record` rows (dedup is by service/method, so parent and child failures both survive; `monday_brief_service.py:853`) — inflates the owner's apparent problems; pre-existing on r2 and HEAD. One cause, one row for nested failures (dedup by correlation id). | Tenets 3/7 | Astra r3 finding 5 | Muad'Dib, the Arrival lane — first repair story after Phase 6 (or Phase 6 exit 3 if the closing chain hits it) |
| The "unknown success emits nothing" claim has no committed fence (`test_philo6_02_round3_record_truth.py:286` exercises failure only; Astra's real `update_record` probe confirms the behaviour). Add the success case. | fence gap | Astra r3 MISSED 1 | Muad'Dib, with the double-Broke repair |

## PHILO-6 follow-ups — 2026-09-24 (Muad'Dib's counsel on built, PR #647)

| Item | Kind | Source | Home |
|---|---|---|---|
| Whole-desk refresh waits about 1.8 s for an unidentified slow sibling after the decision GET resolves. Instrument sibling reads before choosing a repair. The PHILO-6-05 write-version fence protects the body regardless of that delay. | pre-existing performance item; not a hole in 05 | `docs/internal/philo/phase-6/body/diagnosis.md`; lane-B counsel finding 3; phase-local ledger row 1 | two brains: scoped performance diagnosis, separate from 05 |
| An unreachable collection read empties the entire kind: `web/src/desk/api.ts:628,636` starts with empty buckets and sets `status[kind]="unreachable"`. After a failed save and failed read, the one rolled-back decision remains while other decisions disappear. | pre-existing product bug; not fixed by 05 (Tenet 3) | `holdspeak-philo/phase-6-the-honest-morning/checks/lane-b-built-muaddib.md`, MISSED 3; `docs/internal/philo/phase-6/ledger.md` | two brains: reproduce a multi-decision failed read, then repair; no round-two reproduction claim |
| Red continuous S4 logs stamp `rig=1.2.0`, but their predicate text comes from 1.3.0; green logs stamp 1.3.0. Preserve the historical evidence and make future run stamps match executed source. | cosmetic provenance debt | lane-B counsel MISSED 5; `docs/internal/philo/phase-6/body/red-s4-{393,1440}-continuous.log` | rig owner: provenance follow-up, no product repair or evidence rewriting |

## PHILO-7-02 lifecycle beat follow-ups — 2026-09-25 (Astra r1–r3 on PR #656)

| Item | Kind | Source | Home |
|---|---|---|---|
| The kernel's NON-DESK terminal writes are two-step (`transition` then `_terminal`): admission refusal (`kernel/broker.py:332`), native-admission failure (`:131`), explicit rejection (`:220`), claim refusal, `recover_invalidated` and the reaper (`kernel/liveness.py`). An interruption between the two steps leaves `state=refused` with `receipt=NULL`, invisible to receipt recovery — Astra reproduced all six through the real broker with `tool.call`. Phase 7 story 02 pays the DESK paths (T1–T9 in `phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md`) atomically via `transition_and_receipt` + `create_refused_with_receipt`; the shared sites branch on `DESK_KERNEL_OPERATIONS`. The other kinds (parent runs with their publication trigger `db/schema.py:3590-3608`; inference with its attestation `kernel/journal.py:400-420`) keep the two-step write until their own story. | receipt integrity (Tenet 3; Article XI.2) | Astra's checks on the beat, r1 finding 2 + r2 finding 1 | ASSIGNED: Muad'Dib; a kernel story after Phase 7 (or Phase 7 story 02 if the shared seam makes it free — the lane decides and records) |

## PHILO-7-02 canvas follow-ups — 2026-09-25 (Astra r1 on PR #658; `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/checks/story-02-canvas-astra-r1.md`)

| Item | Kind | Source | Home |
|---|---|---|---|
| A credential issued with palette `DESK` reads back as `ALL`. `resolve_palette("DESK") == resolve_palette("ALL")` (228 tools each), so the reverse map built in `GET /api/settings/remote` (`holdspeak/web/routes/mcp_http.py:209-214`) keeps the later name. The issue response says `DESK`, the ledger says `ALL`. Label loss, not added authority. Repair at the credential issue/store/read boundary: store the ISSUED palette name on the credential (`holdspeak/principals.py`, `AgentCredentialStore.issue`) and return it on read. Do NOT reverse the map order (that moves the wrong label to `ALL`). Fence: issue `DESK` and `ALL`, read back each name exactly. | producer defect (Tenet 3; Article VI) | Astra r1 finding 7 (reproduced: issue `DESK`, read `ALL`, both sets 228); canvas `story-02-canvas/README.md` | UNASSIGNED; a Remote Access repair story (small; can ride Phase 7 story 02 if its lane touches the read) |

## PHILO-7-02 round two follow-ups — 2026-09-25 (Astra's check on built, `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/checks/story-02-built-astra-r1.md`)

| Item | Kind | Source | Home |
|---|---|---|---|
| Filing a tombstoned Thought's note over HTTP (`PUT /api/directories/{id}/members/note:<id>`) answers **500** with `{"error": "tombstoned thought cannot be filed"}`; MCP answers the named `thought_tombstoned` conflict. Inherited from main (the route caught `NotFound` and `ValueError`, not `ConflictError`). Since PHILO-7-02 the refusal leaves a kernel receipt, and the 500 body carries `operation_id` and `receipt` (`holdspeak/web/routes/primitives/directories.py`, `api_file_member`). Repair: answer 409 `{error: thought_tombstoned, operation_id, receipt}` like the other named conflicts; fence both transports. | inherited route defect (Tenet 3) | Astra finding 3; the 7-02 evidence "Not changed" | UNASSIGNED; small |

## PHILO-7-03 follow-ups — 2026-09-25 (Muad'Dib's counsel on built, PR #663; `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/checks/story-03-built-muaddib.md`)

| Item | Kind | Source | Home |
|---|---|---|---|
| The decision-delete undo receipt is drawn ABOVE the top edge at 1440 and 393: rect `y=-12, h=27` (1440 `x=1056`, 393 `x=9`), 3 of 9 hit points off-screen, so "Removed …" / "Removal committed" is never readable. The wrapper is `position: fixed; right: 12; bottom: 12` (`web/src/desk/gl/WorldStage.tsx:245-250`); the right edge honours the viewport, the bottom does not (cause not verified). The committed phase lasts 1.2 s (`web/src/desk/hooks/useUndoReceipt.ts:43`). The hub delete itself succeeds (`GET /api/decisions/{id}` 404). Failing case: `case.p7.decision_delete.gone` (`docs/internal/philo/graph/atlas-phase7.json`), FAIL at both widths in both run folders; reproduce with `scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase7.json --case case.p7.decision_delete.gone --brain muaddib --viewport 393 --engine none`. The case turns green when the receipt is on-screen. | face defect (UX canon: the receipt where the act happens) | PHILO-7-03 evidence, face finding 1; reproduced by Muad'Dib's counsel | PAID: PR #665 (the receipt in flow above the AskBar, seat ratified by the owner; glass fence red on main, green after) |
| VERIFIED (`floor-diag/FINDING.md`; plus S1: the second unnamed zone fails 409 on every face): New Zone from the Chair leaves no rename field: the rename overlay `input.desk-zone-rename` lives only in the spatial `WorldStage`, so on the Chair (the default face) the owner makes "New Zone" and cannot name it there; the atlas case goes to the Floor first (`[data-testid=chair-floor-toggle]`). | face gap | PHILO-7-03 evidence, face finding 2 (the lane's first 1440 attempt timed out on the wait) | ASSIGNED: Muad'Dib (the Arrival/Floor lane) |
| VERIFIED (`docs/internal/philo/phase-7/floor-diag/FINDING.md`, PR #667): at 393 the Floor opens as a list (`web/src/desk/store/types.ts:65-72`) and the list view's row-menu Delete (`web/src/desk/components/DeskListView.tsx:332`, `objectMenuEntries`) appears to have no listener; the delete listener exists only in the spatial view. Read from code by the lane; not exercised by the lane or the counsel. First step: exercise it on an isolated hub at 393; file a defect only if it reproduces. | suspected face defect (UNVERIFIED) | PHILO-7-03 evidence, face finding 3 | ASSIGNED: Muad'Dib (the Arrival/Floor lane) |

## The Floor delete receipt follow-ups — 2026-09-25 evening (Astra role, Opus 5.5 stand-in, on PR #665)

| Item | Kind | Source | Home |
|---|---|---|---|
| Two Floor deletes inside one undo window silently keep the second: delete decision A, wait 1.5 s, delete decision B, wait 12 s → A 404, B 200 (B is still on the server while the owner saw it removed). On main too. Likely cause: `remove()` calls `cleanup()`, which drops the earlier pending action (`web/src/desk/hooks/useUndoReceipt.ts:27-29`), and the Floor's undo step does nothing (`web/src/desk/gl/WorldStage.tsx:144-148`); unverified which one is lost and why. A second delete must commit or queue the first, never drop it; a fence with two deletes in one window. | a delete that does not happen while the face says it did (Tenet 3) | `checks/delete-receipt-astra-role-r1.md` finding 7 | ASSIGNED: Muad'Dib, the Floor lane (with the rename-field and list-view Delete defects, `docs/internal/philo/phase-7/floor-diag/FINDING.md`) |
| The Workbench window's footer shows `writeReceipt \|\| undoReceipt \|\| copyReceipt \|\| status` (`WorkbenchWindow.tsx:1893-1897`); with the 6 s linger a delete hides the "N ITEMS · last run" line and any Copy receipt for 6 s. | minor | finding 3 | the next Workbench sitting |

## PHILO-7-04 follow-ups — 2026-09-26 (the Astra-role check on PR #661, MISSED)

| Item | Kind | Source | Home |
|---|---|---|---|
| The decision window shows an empty CONSEQUENCES heading when no consequences were written (a heading with nothing under it; UX-CANON: no empty labels). | face | `checks/story-04-built-astra-role-r1.md` MISSED | the Floor lane |
| The brief reports the people sections as "unavailable" on a fresh hub (a word for a state that is only "none yet"). | face / words | same | the Arrival lane |
| The closing "find it" turn used the note id from the session's own first turn: it proves "find it again", not "find it cold". A future rehearsal asks a fresh session to find a note it did not file. | proof gap | same; `docs/internal/philo/phase-7/file-and-find/rehearsal.md` | the next MCP slice's closing use |
