# The Application Layer Thesis (HS-100-03)

The opinion the owner asked for: what the application layer of the
Desk OS should be. Grounded in [GROUNDING.md](GROUNDING.md) (the four
jobs), convicted by [UIUX_JUDGMENT.md](UIUX_JUDGMENT.md) (what today's
UI does to them). Mockups: `pm/roadmap/holdspeak/
phase-100-the-application-layer/assets/hs-100-03-mockups/` at 1440 and
393. Nothing here ships before the owner's gate (HS-100-04).

## The thesis in one paragraph

HoldSpeak's Desk OS gets **four applications and a desk** — not
fourteen windows. Each application opens on its job's *headline
posture* (the thing you came to do or judge), carries at most two
more *wings*, and folds every ounce of configuration behind one quiet
door. Window interiors become *of the desk*: built only from the
surface kit and the spike's proven material, referring to desk
objects by chip and sprite, never presenting an API map. The dock is
the one launcher; the menu bar is system truth (place, trust, time);
arrival shows the two modes and nothing else. Every rule below ships
with a mechanical guard, because the record shows verdicts regress
without them.

## 1. The applications

### 1.1 Speak (Job 1 — the flagship)

**For:** say it, and it lands where you work — and gets better every
time you correct it.
**Opens on:** the working posture. One column: the mic (hold-to-talk,
huge, alive), the utterance, the pipeline's result, and the
Right/Wrong verdict pair with the correction ritual in place — trace
B's 5-click loop promoted from "tab two of nine" to the entire
front face. Readiness collapses to ONE status line under the mic
("Pipeline live · types into Terminal · 320 ms") that opens the door
only when something is wrong.
**Wings:** *Journal* (reviewing — the dictation record, corrections,
"learned from N similar" honesty) and *Blocks* (the block library).
**The door:** Memory / Knowledge / Runtime / Hooks / Nudges — today's
five config tabs — become grouped setting rows behind one gear.
**Dies here:** the 9-tab strip; the diagnostics-first opening; the
silent mic (see §5 guards).

### 1.2 Meetings (Job 2)

**For:** a meeting becomes filed outcomes you approve.
**Opens on:** the reviewing posture — "what your meetings produced":
aftercare first (open questions, decided, actions with their
propose→approve verbs and egress badges), the meeting list as a rail,
not a facet wall. A meeting's detail leads with outcomes; the
transcript is the receipt behind a disclosure; routing/queues demote
to the door.
**Wings:** *Record / import* (working — the live orb and the drop
target) and *Artifacts* (the typed record across meetings).
**The door:** intelligence configuration, plugin roster, queues.
**Dies here:** the seven-concept tab strip; the nine-concept path to
a filed action — approving a proposed action is one verb on the
opening face.

### 1.3 Agents (Job 3 — renamed; "Personas" dies)

**For:** steer the agents and coders working for you.
**Opens on:** the working posture — who needs you NOW: blocked
sessions first with their asked-question and the answer composer
(voice, typed, or drafted) one verb away; then running, then idle.
**Wings:** *Delivery* (the rails-as-receipts board + dossiers) and
*Chat* (the agent conversation, today's PersonaChat, inside the app
where it belongs).
**The door:** agent/recipe configuration, factory defaults.
**Dies here:** the roster-first CompanionCore; the "Personas" word
everywhere in the glass.

### 1.4 Settings (the cross-cut)

**For:** every boundary, stated once, changed deliberately.
**Opens on:** the spike's grouped setting rows, organized by boundary
(Voice · Intelligence · Egress · Devices · Hub), each group wearing
its egress badge. Absorbs: the `configure-integrations` aliases, the
Runtime guide (as inline help), Setup's residue. **Runs on** stays a
distinct surface reachable from here and from any placement chip —
trust at the point of use outranks tidiness.
**Dies here:** Studio (killed; the pre-Article-I front door),
RuntimeDocs as a standalone window, Setup as a checklist wall.

### 1.5 The desk itself (Job 4 — the operating surface)

Not an application but the ground the four stand on. Keeps: objects/
zones/piles with the 93/95/97 physics, tap→pull-out, rope→ask (trace
C stays the benchmark: 4 clicks, zero navigation concepts),
create-in-world, list mode, automatic filing of run-born artifacts.
Gains: the four applications' windows feel *of* it (§3).
**Demotes:** Workbench (a builder's tool behind search, not a daily
surface), Components (internal), Activity/Commands/Cadence (quiet
tools, right-sized already).

## 2. The interaction model

- **One launcher:** the dock. Four app chips + running marks +
  magnification; desk objects and tools do NOT ride the dock.
- **One system menu:** the menu bar keeps the HoldSpeak menu (the four
  apps + the desk), the trust badge, the clock. The room-menu/tool-
  shelf/start-action triplication dies; the shelf becomes **search**
  (⌘K) — one field that finds apps, tools, desk objects, and verbs.
- **Arrival:** an empty desk shows the two modes as the two daily
  starts (Speak · Record) plus one trust line — nothing else. Setup's
  checklist becomes Settings' door-side status.
- **Voice everywhere stands:** every text input keeps its mic, and a
  mic that cannot capture *says why* instead of vanishing.
- **Windows:** the 97 grammar and 98/99 chrome are floors. An
  application opens as one window on its headline; wings are segments
  in the window head (max three), never a tab wall; the door is the
  gear in the head. Posture rules per archetype:
  - *working*: one generous column, the verb huge, chrome silent;
  - *reviewing*: dense rows, verdict verbs inline, receipts behind
    disclosures;
  - *configuring*: grouped setting rows only — never bare forms.

## 3. The design language (what carries from the spike)

Carries as law: the vibrancy material + glass edge; traffic lights
(idle/front states); menu bar + clock; dock magnification + running
marks; DeskMenuList as the one menu; bare-control inheritance;
SurfaceGroup/SurfaceSettingRow/SurfaceToggle for every configuring
face; sprites as state (empty, refusal, celebration); the token gate.
New commitments: grounding chips — any window content that references
a desk object renders the object's chip (sprite + name) and clicking
it pulls the object out on the desk; refusals name their fix and
never leak paths; the canon vocabulary is guard-locked in the glass.
The *method* commitment: interiors are designed from the job first,
then materialized — the six-round patch-components loop is
retired.

## 4. What dies or merges (the full accounting)

| Today | Fate |
|---|---|
| Dictation (9 tabs) | → **Speak** (headline + 2 wings + door) |
| Meetings + Live meeting | → **Meetings** (one app, record is a wing) |
| Personas and coders + PersonaChat + SessionPullout | → **Agents** |
| Settings + integrations aliases + Runtime guide + Setup | → **Settings** |
| Studio | **killed** |
| Workbench | demoted to a tool (search-reachable) |
| Components | internal-only |
| Activity / Commands / Cadence | quiet tools, unchanged scope |
| Room menu + tool shelf + start actions as launchers | → dock + ⌘K search + arrival starts |

## 5. The build plan (HS-100-05, story-granular, guards named)

Written into the phase at gate time per the phase contract; the
stories below are the plan the gate approves, amends, or rejects.

- **B1 — The vocabulary guard.** A unit guard over `web/src` user-
  facing strings: banned words (intel, persona/Personas, …) fail the
  build; refusal strings must not contain absolute paths.
  *Guard: tests/unit/test_web_vocabulary_guard.py.*
- **B2 — Honest mic.** MicButton renders disabled-with-reason when
  capture is unsupported; insecure-origin reason named.
  *Guard: vitest on MicButton states.*
- **B3 — Speak.** Rebuild DictationCore per §1.1.
  *Guards: the existing surface/seam guards + a flow-budget test:
  arrival→correction ≤ 6 clicks, 1 window (extends flow_traces).*
- **B4 — Meetings.** Rebuild HistoryCore/LiveCore per §1.2.
  *Guard: flow budget — arrival→approve-an-action ≤ 5 clicks and ≤ 4
  concepts on the opening face.*
- **B5 — Agents.** Rebuild CompanionCore + fold chat/steering per
  §1.3. *Guard: blocked-session-first ordering pinned; vocabulary
  guard covers the rename.*
- **B6 — Settings + arrival.** Grouped settings absorbing §1.4;
  EmptyDesk/FirstWords to two-starts arrival; Studio killed,
  registry pruned. *Guards: judgment census re-run against the new
  registry; conductor pin.*
- **B7 — Launcher unification.** Dock as the one launcher, menu bar
  slimmed, shelf→⌘K search. *Guard: the chrome walk leg extended: one
  launcher idiom, search reaches every app/tool.*
- **B8 — The geometry walk.** The every-surface-opened walk leg
  (every registered window opened, measured against the grammar) runs
  headed in the chain. *Guard: the leg itself.*

Each story lands through the stamped gate with evidence; UI stories
carry live-viewport screenshots at 1440 and 393 (standing rule) and
nothing merges to main before HS-100-04's verdict.

## 6. Open questions for the gate

1. The front-door drift (GROUNDING §6.1): amend POSITIONING to the
   Desk-first IA as Article I orders — written as part of B6?
2. "Speak" as the flagship app's name (canon says the feature is
   "voice typing"; the app name is new surface area — the owner
   names things).
3. Cadence/Activity/Commands: quiet tools today — fold any of them
   into an app's wing instead?
4. The spike branch: cherry-pick its material commits as B0, or
   re-land them inside B3–B6 as each interior rebuilds?
