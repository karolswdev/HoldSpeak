# Phase 69 — Web, Re-crafted (the convergence delivery)

**Status:** in-progress (opened 2026-06-22)

**Last updated:** 2026-06-29 (**cadence reconciled; full-sweep delivery underway.** The substrate
(HS-69-02/03/04/01/07) is confirmed present in `web/src/` — but it had landed inside a mixed mobile
checkpoint commit (`f64d80d HSM-14-19`) with no per-story evidence, and the desktop README still
pointed "Current phase" at Phase 67. This update fixes both: the README now points here, and the
program is resumed under the PMO gate. Owner direction (2026-06-29): deliver the **full sweep in
sequence** through the **full node canvas** (1:1 with the iPad Workbench) and the `/companion`→Agent
Desk — true two-way felt parity, multi-session. Prior: **opened + Wave 3** — the Signal-card substrate
(HS-69-02/03/04) was built.)

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

### Owner direction (2026-06-29) — the program for the rest of Phase 69

- **Full sweep, in order.** Deliver every remaining story cheapest-high-impact-first, all the way
  through the heavy node-canvas epic and the `/companion`→Agent-Desk. Multi-session; true full parity
  over a fast partial.
- **Full node canvas (not a lighter pipeline view).** HS-69-10/11 build the pannable dot-grid canvas
  with draggable typed nodes, type-colored bezier cables, palette, and inspector — 1:1 with the iPad
  Workbench. The §1c owner-confirm the parity map asked for is **answered: build the full canvas.**
- **PMO discipline resumed.** Every commit through the contract gate (7 `[x]`), one story-flip per
  commit with its `evidence-story-NN.md`, PR-per-slice merged on green CI, screenshot proof per story
  and real-metal proof for the LLM-shaped ones (the generation theater especially).

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
| HS-69-02 | The shared Signal card primitive | HIGH | **done** (composable `--signal-card-surface`; broadened to `/desk` (8 cards) + `/activity` (nudge + 4 rule cards, repairing a latent Astro-scope-on-JS-DOM gap); computed-style probes + screenshots; see [evidence](./evidence-story-02.md)) | — |
| HS-69-03 | Gradient + hairline tokens | HIGH | **built** (`--accent-gradient`/`--bg-gradient`; gradient consumed by `.glyph-chip`) | — |
| HS-69-04 | Materialize + stagger motion | HIGH | **done** (on the keyed `/activity` nudge list + dashboard recent-cards; `animation-name: hs-materialize` probed on seeded DOM; reduced-motion double-gated; see [evidence](./evidence-story-04.md)) | HS-69-02 |
| HS-69-01 | Egress badge → the cockpit | HIGH | **built** (`egress-badge.js` module + global `.egress-badge`; on the dashboard live-intel card; build green) — history/proposal cards intentionally skipped (no egress data; backend field needed) | — |
| HS-69-05 | Premium sheets / modals uplift | MED | **done** (ConfirmDialog: grab handle + contextual glyph chip + top-lit hairline + tinted-glow backdrop + accent "Done" pill; screenshot-proven danger + affirmative; see [evidence](./evidence-story-05.md)) | HS-69-02 |
| HS-69-06 | Qlippy dock into the cockpit | MED | **done** (extracted to shared `Qlippy.astro`, mounted in AppLayout; dock + cards in the cockpit with the egress badge; native HUD proven non-regressive; shell locks retargeted; see [evidence](./evidence-story-06.md)) | HS-69-01, HS-69-02 |
| HS-69-07 | The Queue HUD (shell + store) | **built** (`runtime-bus.js` + `queue-hud.js` + `QueueHud.astro` in AppLayout; derives jobs from `intel_status`/`runtime_activity` WS frames; pill→ledger; build green; **caught live** — the "1 working" pill rendered the seeded meeting's queued intel) — honest gaps: indeterminate progress bar (no per-job % in frames), 2 concurrent jobs derivable | HS-69-02 |
| HS-69-08 | Reactive mic waveform | MED | **done** (additive throttled `audio_level` broadcast wired into dictation + meeting recorders; floating canvas meter in AppLayout reacts + peak-glows + idle-hides; backend 4 tests + frontend screenshots; see [evidence](./evidence-story-08.md)) | server `audio_level` frame |
| HS-69-09 | Generation theater (orb + constellation) | MED | **done** (iPad orb reused; theater in AppLayout driven by intel_status/token/complete frames; UI screenshots + **real-metal `.43` snapshot** lighting summary/actions/topics; see [evidence](./evidence-story-09.md)) | HS-69-02 + a web `theaterorb` |
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

**2026-06-29 — cadence reconciled; full-sweep program resumed (Wave A).** A grounding pass confirmed the
true state: HS-69-02/03/04/01/07 are all present in `web/src/` (the `.signal-card` primitive +
gradient/hairline tokens in `tokens.css`/`global.css`, `egress-badge.js`, `runtime-bus.js` +
`queue-hud.js` + `QueueHud.astro`), but they had been committed inside a **mixed mobile checkpoint**
(`f64d80d HSM-14-19`) — a PMO-gate violation (multiple phases in one commit, no per-story evidence) that
is already merged, so it is recorded here as paid-down debt rather than re-litigated. The desktop
README "Current phase" pointer (stale at Phase 67) and "Last updated" line are corrected to point here.
A web-flagship polish audit (this session) confirmed the substrate is **under-applied**: `.signal-card`
rides only 5 pages; `/desk`, `/dictation`, and `/activity` lack it, and `/activity` still ships verbatim
legacy vanilla JS. That becomes Wave B. The remaining seven stories (05 sheets, 06 Qlippy dock, 08
waveform, 09 theater, 10/11 node canvas, 12 companion→desk) run in sequence per the owner direction
above, on branch `phase-69-web-recrafted`.

**2026-06-29 — Wave B: the substrate broadened (HS-69-02 done).** The primitive became composable
(`--signal-card-surface`, default unchanged) and now rides the two surfaces the audit flagged as
under-applied: `/desk` (all 8 primitive cards, surface-2 override to keep contrast inside the zones)
and `/activity` (the Alpine nudge card + the 4 JS-injected rule cards). Applying the global primitive
to `/activity` **repaired a latent bug** — Astro's default attribute-scoping meant the page's own
`.rule-item` styles never reached its `innerHTML`-injected cards; the global primitive is what styles
them now. Proven on the live seeded DOM with computed-style probes (`--elev-2` shadow, 18px radius, the
correct surface, the `::before` hairline, and `animation-name: hs-materialize` on nudge cards) plus
full-page screenshots, via `scripts/screenshot_phase69_substrate.py`. Slice green (65 passed) + route
pre-flight (2 passed). Next: HS-69-04 (flip the materialize story on this proof), then HS-69-05.

**2026-06-29 — HS-69-04 + HS-69-05 done.** Materialize flipped to done on the seeded-DOM probe
(`animation-name: hs-materialize`). Then the premium sheet: `ConfirmDialog` (the one modal every page
shares via `window.holdspeakConfirm`) gained the iPad sheet craft — grab handle, a contextual glyph
chip (accent check ↔ danger alert), the top-lit gradient hairline, a tinted-glow backdrop, and accent
"Done" pills — screenshot-proven in both the destructive and affirmative states, behaviour untouched.
Next: HS-69-06 (bring the Qlippy dock + cards off `/presence` into the main cockpit).

**2026-06-29 — HS-69-06 done.** Qlippy's dock + cards were extracted out of `presence.astro` into a
shared `components/Qlippy.astro` (one source) and mounted in `AppLayout`, so the presence enhancer now
rides every cockpit route (bottom-right; the Queue HUD is top-center — no collision). Proven both ways:
a "DECISION NEEDED" card with the ⌂ Local badge + Approve/Decline/Later on `/history`, and the native
HUD `/presence` still rendering the same shell (☁ github result card) — the extraction is
non-regressive. Shell-lock test retargeted to the component; 49 passed across the presence/web slices.
Next: HS-69-08 (the reactive mic waveform).

**2026-06-30 — HS-69-08 done.** The reactive mic waveform, source = a small **additive** server
`audio_level` WS frame (the Phase-68 decision), not an in-browser mic. The recorders already computed
a 0..1 level per chunk (discarded by stub lambdas); `_emit_audio_level` now throttles (~15 Hz) + clamps
+ broadcasts it, wired into the dictation recorder + both meeting channels. A floating Signal meter
(`Waveform.astro` + `waveform.js`) in AppLayout subscribes on the shared bus and renders gamma-expanded
mirrored bars with an accent peak glow, revealing during capture and hiding on silence. Proven both
ends: 4 backend unit tests (shape/throttle/clamp/no-server) + frontend screenshots (active meter +
cropped detail) + the idle auto-hide. 24 passed across the slices. Next: HS-69-09 (the generation
theater — proven on real metal).

**2026-06-30 — HS-69-09 done.** The generation theater: the iPad's `theaterorb.png` reused verbatim,
a centred non-blocking theater (`GenerationTheater.astro` + `theater.js`) in AppLayout driven by the
intel frames that already flow — `intel_status` reveals/hides, `intel_token` pulses the orb,
`intel_complete` lights the Summary/Decisions/Actions/Topics constellation. UI proven via simulated
frames (the streaming "THINKING…" + the ready state with all 4 nodes lit). **Real metal:** the actual
`MeetingIntel` pipeline run on `.43` (the owner's clean `.13` was down) produced a real accurate
snapshot (summary + 2 actions + 4 topics) lighting three nodes — the `intel_complete` path proven on
real metal; `.43` returned buffered (0 token chunks) so the token-pulse waits on `.13` (ready script
ships). 7 passed. **Remaining: HS-69-10/11 (the full node canvas epic) + HS-69-12 (companion → desk).**
Next: HS-69-10.
