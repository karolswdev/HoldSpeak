# Phase 69 — Web, Re-crafted (the convergence delivery)

**Status:** in-progress (opened 2026-06-22)

**Last updated:** 2026-06-22 (**opened + Wave 3 building.** The delivery half of the convergence:
bring the iPad's shipped Signal craft onto the web cockpit, **substrate-first**, per the Phase-68
parity map. Generated directly from `pm/roadmap/holdspeak/phase-68-web-convergence/parity-map.md`
(the ordered backlog) + `web-technical-design.md` (the how) + `design-pattern-catalog.md` (the what).
Wave 3 dispatched: the Signal-card substrate (HS-69-02/03/04).)

## The thesis

The web is the original flagship and it already runs the same "Signal" token system as the iPad —
just **under-applied**. Phase 68 proved the foundation is byte-identical, mapped every pattern, and
sequenced the work. This phase **applies and ports** it: the web cockpit reaches the iPad's felt
quality without a re-theme or a framework swap (Astro + Alpine + vanilla ES modules stay). Cheapest
high-impact first; the heavy node-canvas epic last.

## Decisions carried in (Phase 68 + owner)

- **Web-wins status palette** (owner-approved): `ok #34D399 / warn #FBBF24 / danger #F87171 /
  info #56C7F5` are canonical; Phase-69 stories must NOT reintroduce the iPad's `Sig` status hexes.
- **Node canvas** = a **linear-renderer-first**, **pure-vanilla SVG** build over the serializable
  `Workflow` shape (no graph lib). The "full canvas vs pipeline view" question is resolved — they
  converge.
- **Reactive waveform** source = a small additive server `audio_level` WS frame (not a new in-browser
  mic surface).
- **Queue HUD** jobs = derived from the existing `intel_*` / `runtime_activity` WS frames via a shared
  `runtime-bus.js` (no backend message-type change).
- **Companion portal direction (owner-approved):** the web `/companion` **becomes the Agent Desk** —
  the same desk surface as the iPad (HSM-15-08), not a plainer control panel. Added as **HS-69-12**.
- **iPad-is-a-full-peer** principle stands (this phase is desktop/web; it does not weaken on-device).

## Scope

- **In:** the 12 ordered web-delivery stories below. Substrate (`.signal-card` primitive + gradient/
  hairline tokens + materialize/stagger motion) lands first as it lifts every surface.
- **Out:** the **iPad-gains-breadth** items (config cockpit, faceted search, the learning-loop surface,
  activity/routing, commands board, onboarding, the iPad status-palette re-tune) — those are MOBILE
  roadmap, recorded in the parity map. Backend rewrites (the waveform `audio_level` frame is a small
  additive exception). New product features (this is presentation reaching the bar + the companion→desk).

## Exit criteria (evidence required)

- [ ] The substrate ships: one `.signal-card` primitive (depth + gradient top-lit hairline + glyph
      chip) + `--accent-gradient`/`--bg-gradient` + `hs-materialize` — before/after screenshots of ≥3
      surfaces (HS-69-02/03/04).
- [ ] The egress badge rides cockpit cards (not just `/presence`), structured `{scope,label}`, no prose
      (HS-69-01).
- [ ] The Queue HUD is a shell-level always-on pill → ledger, fed from the shared bus (HS-69-07).
- [ ] Qlippy dock + cards in the main cockpit (HS-69-06); premium sheets uplift (HS-69-05); reactive
      waveform (HS-69-08); generation theater on real intel (HS-69-09).
- [ ] The node canvas: linear renderer → drag → wiring + inspector, web-palette ports (HS-69-10/11).
- [ ] The web `/companion` is the Agent Desk (HS-69-12).
- [ ] Each story Simulator/browser-screenshot-verified; LLM-shaped surfaces proven on real metal.

## Stories (from the Phase-68 backlog; full per-story spec in `../phase-68-web-convergence/parity-map.md`)

| Story | Title | Priority | Status | Depends on |
|-------|-------|----------|--------|------------|
| HS-69-02 | The shared Signal card primitive | HIGH | **built + visually verified** (settings panel = raised signal-card; global-scoped; build green) | — |
| HS-69-03 | Gradient + hairline tokens | HIGH | **built** (`--accent-gradient`/`--bg-gradient`; gradient consumed by `.glyph-chip`) | — |
| HS-69-04 | Materialize + stagger motion | HIGH | **built; visual pending** (needs seeded meetings to show the card-arrival on dashboard/history) | HS-69-02 |
| HS-69-01 | Egress badge → the cockpit | HIGH | **built** (`egress-badge.js` module + global `.egress-badge`; on the dashboard live-intel card; build green) — history/proposal cards intentionally skipped (no egress data; backend field needed) | — |
| HS-69-05 | Premium sheets / modals uplift | MED | backlog | HS-69-02 |
| HS-69-06 | Qlippy dock into the cockpit | MED | backlog | HS-69-01, HS-69-02 |
| HS-69-07 | The Queue HUD (shell + store) | **built** (`runtime-bus.js` + `queue-hud.js` + `QueueHud.astro` in AppLayout; derives jobs from `intel_status`/`runtime_activity` WS frames; pill→ledger; build green; **caught live** — the "1 working" pill rendered the seeded meeting's queued intel) — honest gaps: indeterminate progress bar (no per-job % in frames), 2 concurrent jobs derivable | HS-69-02 |
| HS-69-08 | Reactive mic waveform | MED | backlog | server `audio_level` frame |
| HS-69-09 | Generation theater (orb + constellation) | MED | backlog | HS-69-02 + a web `theaterorb` |
| HS-69-10 | Node canvas — foundation | HIGH (heavy) | backlog | HS-68-03 |
| HS-69-11 | Node canvas — wiring + inspector | HIGH (heavy) | backlog | HS-69-10, HS-69-05 |
| HS-69-12 | Web `/companion` → the Agent Desk | MED | backlog | HS-69-02 |

## Where we are

**2026-06-22 — opened; Wave 3 (the substrate) building.** An Opus 4.8 agent is implementing
HS-69-02/03/04 (the `.signal-card` primitive + gradient/hairline tokens + `hs-materialize` motion) —
the additive-CSS foundation that lifts every surface at once. Verified by `cd web && npm run build` +
before/after screenshots (the Astro/Alpine JS-rendered-DOM CSS gotcha applies: JS-injected cards need
global styles + screenshot proof, not just a class in the bundle). Orchestrator integrates + commits
under the PMO gate. Build order then follows the table (egress badge, sheets, Qlippy, Queue HUD, …),
node canvas last.

**2026-06-22 (later) — Wave 3 integrated + visually verified.** The substrate landed: `tokens.css`
(+`--accent-gradient`/`--bg-gradient`), `global.css` (`.signal-card` with the `::before` gradient
top-lit hairline + `.glyph-chip` + `hs-materialize` + reduced-motion gate), applied to dashboard
home-cards, history meeting-cards, and the settings `.set-panel`. `npm run build` green (13 pages);
classes confirmed **global-scoped** in the built CSS (apply to Alpine-injected DOM). **Visual proof:**
ran `holdspeak web` locally + headless-chromium-shot the cockpit — the **settings panel now renders as
a raised signal-card** (top-lit hairline + elevation), confirmed. The dashboard `/` (its 4 home-cards)
and history meeting-cards + the `hs-materialize` arrival couldn't be shown on this fresh runtime
(empty DB → `/` redirects to onboarding; history has no meetings) — they need seeded data to screenshot
(a quick follow-up). Substrate is shipped + working; next: HS-69-01 (egress badge → cockpit).
