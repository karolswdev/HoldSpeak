# Phase 68 — Convergence: the Design Map & Parity Plan

**Status:** in-progress (opened 2026-06-22)

**Last updated:** 2026-06-22 (**opened.** The owner: the iPad Swift app's interface is finally not
embarrassing — a real "Signal" depth system, a node-graph Workbench, an app-wide Queue HUD, a
generation theater, tactile sheets, the egress badge, PixelLab assets, a reactive waveform. The web
UI — *the original flagship* — has fallen behind on craft, and "we can't leave the web UI behind."
This phase **maps the Swift app's design patterns, audits two-way feature parity, and designs the
steps** to make the web UI equally rich. It is the discover/design phase; the **delivery** phase
(Phase 69) is generated from this one's parity backlog — you cannot author good delivery stories
before the parity map exists, which is why this phase comes first.)

## The thesis — why this phase

HoldSpeak started as the web cockpit. The iPad came later and, after a hard craft push, overtook the
web on *felt* quality. That is a **divergence**, and it is two-way:

- **Web is behind on craft.** Grounding (2026-06-22) confirmed the web has **no** node-graph builder,
  **no** drag interactions at all, **no** app-wide Queue HUD, **no** generation theater / materialize
  motion, **no** reactive waveform, and Qlippy's rich dock/cards are **stranded on `/presence`** (the
  native HUD), absent from the main browser cockpit. Its mature motion/elevation tokens are
  **under-applied**.
- **Web is ahead on breadth.** It has surfaces the iPad lacks: the full config cockpit (`/settings`),
  the 3,000-line history + faceted search (`/history`), the correction journal + memory/telemetry,
  activity + routing rules (`/activity`), the onboarding funnel (`/welcome` + `/setup`), the Voice
  Commands board (`/commands`), the Companion portal (`/companion`).

Crucially, the web is **not** a blank slate: it already runs a real **"Signal" token system**
(`web/src/styles/tokens.css`, Phase 30) — the *same* accent `#FF6B35`, the *same* top-lit hairlines,
the *same* "settle" motion easing as the iPad. So convergence is mostly **apply + port specific
patterns onto an existing language**, not a redesign. "1:1 parity" is therefore **bidirectional**:
web gains the iPad's craft; the iPad's roadmap gains the web's breadth (tracked, delivered later on
the mobile roadmap).

## Goal

Produce three authored artifacts that make web richness executable:

1. **A cross-platform design-pattern catalog** — the Swift app's patterns, named and specified, mapped
   onto the **existing** web Signal tokens (what's reusable as-is vs what's genuinely new). The shared
   source of truth for both platforms.
2. **A two-way parity map** — a surface-by-surface, feature-by-feature inventory of iPad vs web, with
   the gaps in both directions and an **ordered 1:1 parity backlog** (the input to the delivery phase).
3. **A web technical design** — how each high-value pattern (node canvas, Queue HUD, generation
   theater, Qlippy-in-cockpit, the motion pass) is actually built in the web stack
   (Astro + Alpine + vanilla ES modules + the Signal tokens) — the concrete steps, de-risked.

## Scope

- **In:** the design-pattern catalog (HS-68-01); the two-way parity map + ordered backlog (HS-68-02);
  the web technical design for the marquee patterns (HS-68-03). These are **documents/specs**, the
  deliverable of a design phase. The delivery phase (Phase 69) is scaffolded from HS-68-02's backlog.
- **Out:** building the web patterns themselves (Phase 69). Changing the iPad app. Re-theming the web
  from scratch (the Signal tokens stay; we apply and extend them). New product features (parity is
  about *presentation* reaching the iPad's bar, plus closing feature gaps both ways).

## Exit criteria (evidence required)

- [ ] **The catalog** — every Swift design pattern named + specified + mapped to the web Signal tokens
      (reuse vs new), traced against real files on both sides (HS-68-01).
- [ ] **The parity map** — a complete two-way surface/feature inventory with the gaps and an **ordered
      delivery backlog** that becomes Phase 69's stories (HS-68-02).
- [ ] **The technical design** — a concrete, de-risked build approach for the node canvas, the Queue
      HUD, the generation theater, Qlippy-in-cockpit, and the motion pass in the web stack (HS-68-03).
- [ ] **Phase 69 scaffolded** from the backlog (stories named, sequenced), so delivery can start.

## Stories

| Story | Title | Status | Depends on |
|-------|-------|--------|------------|
| HS-68-01 | The cross-platform design-pattern catalog | **done** (`design-pattern-catalog.md`) | none |
| HS-68-02 | The two-way parity map + ordered delivery backlog | **done** (`parity-map.md` — 11 Phase-69 stories) | HS-68-01 |
| HS-68-03 | The web technical design (how the marquee patterns get built) | **done** (`web-technical-design.md`) | HS-68-01 |

## Where we are

**2026-06-22 — opened, grounded both sides.** Independent analyses mapped (a) the iPad's shipped
design patterns and (b) the current web UI. Headline: the web already runs the same Signal token
system — it is **under-applied**, not absent — and the divergence is two-way (web behind on craft,
ahead on breadth). So this is convergence onto a shared language, not a rebuild. The phase is
deliberately a **design phase**: its output (the catalog + the parity backlog + the technical design)
is what lets Phase 69's delivery stories be written well. Authoring starts at HS-68-01 (the catalog),
since both 68-02 and 68-03 build on it.

**2026-06-22 — HS-68-01 done; status-palette decision made.** The catalog confirmed the foundation is
byte-identical across platforms; the one real drift was the **status palette**. **Owner decision:
web-wins** (the web's `ok #34D399` / `warn #FBBF24` / `danger #F87171` / `info #56C7F5` have documented
WCAG contrast). These become the **canonical** status colors for both platforms; the iPad re-tunes
`Sig.ok/warn/bad/local` to match on the mobile roadmap (a small follow-up unit, tracked in
MASTER-EXECUTION). Wave 2 (HS-68-02 parity map + HS-68-03 web technical design) dispatched, both
treating the web status palette as canonical.

**2026-06-22 — HS-68-02 done (parity-map.md).** A two-way inventory + an ordered **Phase-69 backlog of
11 stories**, sequenced cheapest-high-impact-first: HS-69-01 egress-badge-into-cockpit, -02 the shared
Signal card primitive, -03 gradient/hairline tokens, -04 materialize/stagger motion, -05 premium
sheets, -06 Qlippy-into-cockpit, -07 the Queue HUD, -08 reactive waveform, -09 generation theater,
-10/-11 the node-canvas epic (foundation + wiring, sequenced last as the heaviest). The
iPad-gains-breadth list is recorded for the MOBILE roadmap (config cockpit, faceted search, the
learning-loop surface, activity/routing, commands board, onboarding, the palette re-tune). **Two open
owner-calls surfaced (not guessed):** (1) the **companion portal direction** — iPad CompanionBoard and
web `/companion` are peers in different roles; whether the web portal adopts iPad craft or stays a
control panel is undecided; (2) **does the web need the full node canvas at all** vs a lighter pipeline
view — HS-69-10 must confirm before the heavy lift (HS-68-03's technical design informs this).

**2026-06-22 — HS-68-03 done (web-technical-design.md); design foundations COMPLETE.** All three
HS-68 deliverables are authored. Key finding: the runnable `Workflow`
(`apple/Sources/RuntimeCore/Workbench/Workflow.swift:102-142`) is a **linear, Codable** pipeline and
the iPad node-canvas is presentation over it — so the web "canvas" is a layout+interaction problem
over a serializable shape, **not** a graph engine. This **resolves owner-call (2):** build the node
canvas via a **linear-renderer-first** path (read-only renderer → drag → inspector → optional wiring);
the "lighter pipeline view" and the "full canvas" converge, so we build the one thing. **Orchestrator
decisions (within remit; owner may override):** (a) Workbench = **pure-vanilla SVG** cables + HTML/CSS
node cards in one CSS-transform world layer (no graph lib — preserves the framework-free, un-minified
stance); (b) reactive waveform source = **a small additive server `audio_level` WS frame** (Option B —
matches server-side capture; avoids a brand-new in-browser mic surface); (c) Queue HUD jobs =
**derived from existing `intel_*`/`runtime_activity` WS frames** via a shared `runtime-bus.js` (no
backend message-type change). Substrate-first build order: the `.signal-card` primitive + gradient
tokens + `hs-materialize` land first (HS-69-02/03/04), then the rest per the backlog.

**Phase 68 exit criteria:** catalog ✓, parity map ✓, technical design ✓ — only **Phase 69 scaffolded
from the backlog** remains, then this phase closes (via PR).

Owner bar carried across: no prose in the product (the egress badge, not sentences); premium/native
craft; PixelLab for bespoke assets; **show it**; and the standing grounding lesson — *read what each
platform already does before planning new work* (this phase exists because we applied it).
