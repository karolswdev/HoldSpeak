# The Grounding (HS-100-01)

What HoldSpeak is for, evidenced. This document is the ground truth the
Phase 100 judgment and thesis stand on. It is subordinate to
[CONSTITUTION.md](CONSTITUTION.md) and cites every claim; an unsourced
claim here is a defect. Sources: the Constitution (read whole), the
positioning canon, the founding RFCs, the public README and user guide,
all thirteen owner campaigns and ~160 UAT scenarios, the recorded
sitting database, the 2026-07-04 dogfood run (the only complete
end-to-end walk on file), and the owner-verdict trail across phases
67–100.

## 1. The identity, as ratified

The one-liner (identical in canon and public README): *"One local
copilot, two modes: dictation that types anywhere and learns how you
work, and meetings that end with decisions, actions, and follow-ups
instead of a recording. Nothing leaves your machine."*
(POSITIONING.md:13-15; README.md:7.)

Three owner-set founding decisions (2026-06-11, "not up for
relitigating," POSITIONING.md:3-9, 21-40): the lead is **one copilot,
two modes** (privacy and learning are pillars one rung below); the
audience is **developers** ("write for someone who will read the code
if the doc is wrong"); comparisons **name names honestly**.

Since 2026-07-17 the Constitution's Preamble extends the identity: the
copilot has *a place to live* — the Desk — and "your agents, terminals,
and delivery work sit on the same surface you do" (CONSTITUTION.md:13-16).
Article I makes the Desk the operating surface outright and explicitly
supersedes the older page-based information architecture
(CONSTITUTION.md:18-28).

## 2. The jobs HoldSpeak is hired for, ranked

Ranking method: scripted-usage weight (scenario/campaign counts) ×
proven end-to-end value (the dogfood walk's PASS grid, not the
feature ledger — `uat/features.yaml` marks all 285 cells "live" and
discriminates nothing) × owner attention in the verdict record.

### Job 1 — Say it, and it lands where you work
Hold a key (or wake word, or a device mic), speak, and grounded text
types into the focused app — or into a waiting coding agent. The
single largest scenario pack (15, pack-c + Campaign 2), the guide's
mode 1, and the walk's own words for T2-17: "THE product thesis on
real metal" — speech became a brief citing `LL-118`, a test file, and
all four `.hs/memory.md` invariants, typed where the user was.
**Felt-value moment:** rambling speech → a precise, file-citing brief
in the app you were already in.
**The loop that keeps it:** every dictation journaled; one tap teaches
a correction; "learned from N similar" is honest at zero; replay shows
improvement instead of promising it (POSITIONING pillar 2; walk T2-24
PASS).

### Job 2 — A meeting becomes filed outcomes
Record or import; transcript becomes typed artifacts (ADRs, actions,
decisions, diagrams — 14 plugins); aftercare shows open/decided/
changed; an accepted action leaves as an issue/Slack post through
propose→approve→execute. Thirteen scenarios (pack-a + Campaign 3);
the strongest end-to-end evidence on file (six real meetings through
real Whisper + the .43 model, dogfood 2026-07-04; the imported-meeting
artifact seam is young — F-05 was the walk's one MED-HIGH finding,
closed same day by Phase 80).
**Felt-value moments:** the accepted ADR appearing as a typed artifact;
the approved Slack proposal leaving as exactly one byte-equal POST
(walk T2-15).

### Job 3 — Steer the agents that work for you
Live Claude/Codex sessions surface on the desk; the blocked one
demands you; an answer (typed, spoken, or AI-drafted then approved)
lands as keystrokes in the real pane; spawn/rename/kill ride the same
consent spine; delivery work (stories, PRs, attempts) rides the same
surface. Thirteen steering scenarios + the delivery-runtime campaign;
deeply built and audit-hardened (the steering chokepoint owns a whole
architecture section); glass-proven live in phases 87–90 though
outside the headless walk's reach.
**Felt-value moment:** a waiting coder answered by voice from the desk.

### Job 4 — Live at the Desk (the job that hosts the others)
Arrive, understand in ten seconds (POSITIONING's stated legibility
bar), keep and find work (notes/KBs/zones/piles), lasso a pile and ask
one grounded question, keep the answer with lineage. The largest
single pack (21, pack-desk + Campaign 1) — and the object of every
owner verdict since 2026-07-15. This job is WHY the application layer
matters: jobs 1–3 produce the value; job 4 is where it is seen,
reached, and trusted.

### The cross-cut — Trust the boundaries
Not a job but a posture the owner tests constantly (12 honest-failure
scenarios seeded into every campaign's exit gate): egress is a badge
at the point of decision, never prose; runs-on names every real
boundary; keys never ride back; failures are named, not softened
(Articles III, V, VI).

### The long tail (real, secondary, or gated)
Cadence's daily brief (live-proven, all Tier-C green, off by default);
activity nudges (partial — needs real ambient input); voice macros
(dry-fire proven); mesh relay + delivery belt + devices/wake hardware
(wired and tested, physically gated in walks); iPhone/iPad flagship
(21 scenarios scripted, **zero completed device verdicts** — promised,
essentially unwitnessed).

## 3. The seams that produce each job's value

| Job | Seam (code) | Wire surface | Maturity |
|---|---|---|---|
| 1 | dictation pipeline + learning (`dictation_runner`, `plugins/dictation`, `dictation_learning`) | `/api/dictation/*`, `/wake/*` | live-proven headline |
| 2 | meeting session + plugin host + aftercare + gated connectors (`meeting_session/`, `meeting_plugins`, `plugins/host`, `meeting_aftercare`, `gated_connector`) | `/api/meetings/*`, `/api/intel/*` | live-proven (artifact seam young) |
| 3 | steering chokepoint + factory + relay (`coder_steering`, `coder_factory`, `tmux_transport`) | `/api/coders/*` | built + audited, glass-proven |
| 4 | primitive store + grounding hydrator + projections (`db/*`, `grounding.py`, `primitives/_shared`) | `/api/notes|kbs|ask|grounding/*` | foundational; ask lightly walked |
| cross | operation policy + authority + egress surfaces (`operation_policy`, `authority` routes) | `/api/authority/*`, badges | ratified + walk-tested |

## 4. The postures at the desk

The record shows four distinct postures, and they want different
things from the interface:

- **Working** (jobs 1 and 3, minute-to-minute): the product should
  nearly disappear — a held key, a landing brief, a blocked agent
  answered. Latency and non-intrusion are the craft.
- **Reviewing** (job 2 aftermath + the journal + receipts): reading,
  judging, approving. Density, honesty, and provenance are the craft.
- **Arranging** (job 4): keeping, filing, finding, grounding. The
  spatial world earns its keep here or nowhere.
- **Configuring** (rare, high-stakes): runs-on, credentials, toggles.
  Clarity over boundaries is the craft; the owner's recorded verdict
  on the first-run screens: "way too full with noise… absolutely
  confusing" (sitting DB, 2026-07-17).

## 5. Who actually sits here

A developer (founding decision 2), overwhelmingly on desktop web —
the iPhone/iPad record is scripted but unwitnessed; secondary native
shells are quarantined to a conditional campaign; the TUI is retired
(WFS supersession note). The conductor data is honest about itself:
20 sittings, most never completed, six cast verdicts total — the real
usage signal is the owner's prose verdicts, which is itself a finding
about the review tooling.

## 6. Named drifts, for the owner's ruling

1. **The front door.** POSITIONING (Phase-70 era, lines 108-115) still
   places the Desk inside the Studio tier with Home + "the two modes"
   as the front door; the README markets "the browser opens on the
   Desk"; Constitution Article I.4 already rules the Desk IS the
   surface and orders POSITIONING amended. The amendment has not been
   written. The thesis must write it.
2. **Vocabulary split-brain.** Canon fixes **agents** (banning
   persona-drift) and **coders**; the shipping UI and README say
   **Personas**. Canon fixes **voice typing**; DOCS_STYLE tells guide
   writers to say "dictation." Canon bans user-facing **intel**;
   DOCS_STYLE prescribes it. One pass must reconcile the table, the
   guides, and the UI strings.
3. **The ledger flatters.** `uat/features.yaml` marks everything
   "live"; the walk's PASS/PARTIAL/SKIP grid is the only honest
   maturity signal. Article VI applies to our own instrumentation.
4. **Sittings don't complete.** The UAT conductor produces almost no
   structured verdicts; the owner reviews by screenshot and prose.
   Either the sitting tool earns its keep in the new layer or it
   admits what it is.

## 7. Non-goals (stated, so the thesis doesn't drift)

Not hands-free grammar control (Talon is credited as deeper there);
not a cloud service, account, or subscription; not Windows today; not
a TUI; never egress without a named, badged, human-approved boundary
(POSITIONING comparisons; Articles III and V).

## Appendix A — the owner's verdicts, verbatim and chronological

The bar this phase must clear, in the owner's own words:

- **2026-07-04** (dogfood run): 40 PASS / 14 PARTIAL / 1 FAIL / 8
  SKIP; F-05 "imported meetings never receive typed plugin artifacts"
  (fixed same day, Phase 80).
- **2026-07-15** (first lived-use spin, desktop + iPhone): "floating
  desk areas are glued in place — not movable, not resizable… the
  experience is not streamlined."
- **2026-07-17** (first live sitting; births the Constitution): "the
  desk experience is confusing and convoluted, because the desk is a
  front door that keeps throwing you out of it… it feels clunky
  rather than native." On first-run: "way too full with noise…
  absolutely confusing, overloaded with content."
- **2026-07-18** (on the 96/97 build): "the windows are ugly, there is
  zero cohesion between the desk and the windows it opens, zero 'I'm
  sitting in an operating system' feeling — so zero incentive to use
  what HoldSpeak offers."
- **2026-07-18** (chartering 98): "none of the Desk OS feels like an
  OS — windows feel like glued-in HTML panes, zero consistent look
  and feel."
- **2026-07-18** (on the staged 98 build, chartering 99): "a step, but
  holy shit do we still have soooo much work to do to even begin
  dreaming of this looking and feeling like a OS. There's still loads
  of unstyled selects… those windows still deserve a huge, and I
  really mean huge... overhaul."
- **2026-07-19** (on the 99 close): "It stil looks like ass… not those
  fucking barren and boring HTML windows… the 'innards' of a lot of
  these windows? FUCKING HIDEOUS. AGAIN, FORMS ON TOP OF FORMS ON TOP
  OF HTML."
- **2026-07-19** (on the first spike round): "it still looks like
  major ass… More OS-native-primitive integration feeling, less of
  this janky ass basic bitch-ass HTML… GET INSPO FROM ALL THOSE
  WONDERFUL OSS WEB-BASED OSs!!!!"
- **2026-07-19** (materials round): "Better. But you can do even
  better." Then: "Make it look more like an OS. For god's sake."
- **2026-07-19** (Trust window screenshot): "honestly - terrible… no
  margins? … fucked up buttons? … overlaps? 0 margins? Where things
  look like shit inside windows?"
- **2026-07-19** (KB pull-out screenshot): "super basic HTML buttons…
  'tags' also not of equal size… overall extreme laziness."
- **2026-07-19** (persona pull-out screenshot): "You can't be serious
  with this."
- **2026-07-19** (the directive that charters this phase): "THIS HAS
  BEEN ENOUGH. RIGHT NOW, WE PLAN ON A PHASE THAT WILL CAUSE A DEEP,
  DEEP, DEEP GROUNDING IN THE PHILOSOPHY, SEAMS, USE CASES, TO THEN
  FORM AN OPINION ON THE ENTIRE UI/UX WITH REGARDS TO ITS
  APPLICABILITY TO DESK OS, AND THEN, WE WILL FINALLY DELIVER
  SOMETHING BEAUTIFUL, NOT MANGLED, EASY TO USE, A PROPER, EASY TO
  USE APPLICATION LAYER ON OUR DESK OS TO DRIVE THE VALUE OF
  HOLDSPEAK!"

**Reading of the record:** no verdict faults the capabilities. Every
verdict faults the layer they wear — first its physics (fixed by 93/
95/97), then its consistency (fixed by 96/98), then its material
(bettered by the spike), and throughout, its *legibility as a place
to work*. The thesis must answer that last one; chrome alone has
three phases of evidence that it cannot.

## Appendix B — source index

CONSTITUTION.md (whole); POSITIONING.md:3-206; README.md:7-189;
docs/USER_GUIDE.md; PLAN_ARCHITECT_PLUGIN_SYSTEM.md:5-52,265-301,
474-494; PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md:3-18,106-117;
PLAN_PHASE_DICTATION_INTENT_ROUTING.md; PLAN_PHASE_MULTI_INTENT_ROUTING.md;
DOCS_STYLE.md:12-108; uat/campaigns/owner-01…13; uat/scenarios/** (by
pack, counts cited in §2); uat/_runs/uat.db (step_verdicts, sittings);
dogfood/results/2026-07-04.md (whole, incl. addenda);
docs/ARCHITECTURE.md:14-32,309-348; ARCHITECTURE_BACKEND_RUNTIME.md;
pm/roadmap/holdspeak/phase-{67,92,93,95,96,97,98,99,100} status and
final-summary files; HANDOVER-2026-07-03-desk-era.md:36-37,142.
