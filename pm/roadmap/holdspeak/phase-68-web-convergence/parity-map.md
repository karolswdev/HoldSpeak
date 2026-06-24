# The two-way parity map + ordered delivery backlog (HS-68-02)

**Phase:** 68 — Convergence. **Status:** authored 2026-06-22.

The surface-by-surface inventory of the iPad Swift app vs the web cockpit, the gap in
**both** directions, and the **ordered delivery backlog** that becomes **Phase 69 (web
delivery)**. It is the bridge between HS-68-01 (the design-pattern catalog) and Phase 69's
stories: you cannot sequence delivery well until you know, per surface, who is ahead and on
what axis.

Source-of-truth inputs, all already grounded:
- the design-pattern catalog: `pm/roadmap/holdspeak/phase-68-web-convergence/design-pattern-catalog.md` (the 9 patterns, the byte-identical-foundation finding, the port-priority table).
- the phase thesis + the **web-wins status-palette** decision: `pm/roadmap/holdspeak/phase-68-web-convergence/current-phase-status.md`.
- POSITIONING canon (the egress badge, no privacy prose, two modes): `docs/internal/POSITIONING.md:140-147`.
- iPad surfaces: `apple/App/MeetingCaptureApp.swift` (one 4,942-line file).
- web surfaces: `web/src/pages/*.astro` + `web/src/scripts/*`.

Two principles this map honors (non-negotiable, from the phase + memory):
- **The iPad is a full peer, not a thin client.** It does on-device capture →
  transcription → intelligence end-to-end (Phases 6/7/8); the mesh/companion is *additive*.
  So "iPad-behind-on-breadth" means *it lacks a desktop-class management surface*, never
  "it can't do the work."
- **Web-wins status palette.** The web's `--ok #34D399 / --warn #FBBF24 / --danger #F87171 /
  --info #56C7F5` (`web/src/styles/tokens.css:61,64,67,70`) are the **canonical** status
  colors for both platforms (documented WCAG contrast). Any new web surface uses them
  directly; the iPad re-tunes on the mobile roadmap. No Phase-69 story should reintroduce the
  iPad's `Sig.ok #3ECF8E / warn #F2A33C / bad #E5544B / local #5B8DEF`.

---

## 1. The two-way inventory

Columns:
- **iPad** — has it? + craft level (`flagship` = full Signal craft / `solid` = functional and
  themed / `none`).
- **Web** — has it? + craft level (`flagship` / `solid` / `basic` = present but flat/under-applied
  / `none`).
- **Gap direction** — `web←craft` (web should get iPad's polish), `iPad←breadth` (the iPad
  roadmap should gain this surface), `parity` (both adequate), or `owner` (genuinely ambiguous).
- **Notes** — the catalog pattern(s) at play, `file:line` for non-obvious claims.

### 1a. Surfaces where the WEB is behind on craft (Phase 69 scope)

| Feature / Surface | iPad | Web | Gap | Notes |
|---|---|---|---|---|
| **Signal depth — the shared card primitive** | flagship — one `.signalCard()` modifier + top-lit gradient hairline + glyph chip + press-spring everywhere (`MeetingCaptureApp.swift:433-474`) | basic — has `--elev-*` tokens but **no** `.signal-card` utility, **no** gradient hairline, glyph icons in ad-hoc containers (`web/src/styles/tokens.css:191-196`) | `web←craft` | Catalog §1. Foundation is byte-identical; the missing thing is the one composing primitive. Lifts every surface at once. |
| **Egress badge in the cockpit** | solid — still the **pre-badge prose idiom** (`cfg.egressLabel`, on-device chips) (`MeetingCaptureApp.swift:1570-1571, 4552-4558, 4934-4941`) | flagship-but-stranded — the **canonical** `{scope,label}` badge exists, only on `/presence`/Qlippy (`web/src/scripts/qlippy.js:134-146`, `web/src/pages/presence.astro:280-302`) | `web←craft` | Catalog §6. POSITIONING obligation (`POSITIONING.md:140-147`): cockpit cards must carry the badge, not sentences. The fix is *placement*: lift `q-egress` into a shared component, apply on history/meeting/intel cards. |
| **Queue HUD (app-wide job ledger)** | flagship — Dynamic-Island pill → full panel, status orbs, progress bars, target chips, blocked-auto-resume (`MeetingCaptureApp.swift:2631-2748`, mounted at root `:36`) | none — state is per-page WS in `dashboard-app.js`; no shared store, no floating HUD | `web←craft` | Catalog §3. Status vocabulary maps 1:1 onto web status tokens. Needs a new shared front-end run-queue store + the floating shell. |
| **Generation theater (model-thinking)** | flagship — plasma orb (PixelLab `theaterorb`) + concentric rings + type constellation lighting up per artifact (`MeetingCaptureApp.swift:4526-4614`) | none — has live intel WS streaming to drive it, but no orb asset, no theater | `web←craft` | Catalog §4. Depends on a web `theaterorb` export + live-intel-streaming UX. |
| **Node-graph Workbench** | flagship — pannable dot-grid canvas, draggable typed nodes, bezier cables, palette, inspector sheet (`MeetingCaptureApp.swift:1809-2363`) | none — no canvas, no drag interactions anywhere | `web←craft` | Catalog §2. The largest new build; HS-68-03 owns the technical de-risk. Likely a multi-story epic. |
| **Premium sheets / modals** | flagship — grab handle, glyph-chip header, accent "Done" pill, tinted glow background (`MeetingCaptureApp.swift:2398-2433`) | solid — `ConfirmDialog.astro` / `Panel.astro` focus-trapped dialogs, but flat chrome | `web←craft` | Catalog §5. Reuse + uplift: add a grabber element + a glow-background + glyph-chip header to existing dialogs. Touches every modal at once. |
| **Reactive mic waveform** | flagship — gamma-expanded perceptual level meter, per-bar wobble, peak glow (`MeetingCaptureApp.swift:3438-3466`) | none — no audio visualization anywhere | `web←craft` | Catalog §7. New Web Audio `AnalyserNode` → rAF canvas. More plumbing than the depth/badge ports. |
| **Materialize / settle motion** | flagship — cards glow+insert on arrival, staggered entrances, settle springs, reduce-motion gated (`MeetingCaptureApp.swift:472, 2645, 4610`) | basic — settle ease + `hs-pulse` exist but applied only to live dots (`web/src/styles/global.css:97-106`) | `web←craft` | Catalog §8. Add one `hs-materialize` keyframe + a stagger helper; apply where cards arrive. Connective tissue for §1–§4. |
| **Qlippy dock + cards in the cockpit** | flagship — CompanionBoard + presence cards on the iPad | basic-but-stranded — rich Qlippy dock/cards exist only on `/presence` (the native HUD), absent from the browser cockpit (`current-phase-status.md:19-22`) | `web←craft` | Catalog §6/§9. The Qlippy sprite pipeline + assets already ship on web (`web/src/scripts/qlippy.js:123-125`). Bring the dock into the main cockpit. |
| **PixelLab bespoke assets (orb/crystal)** | flagship — `theaterorb.png`, `crystal.png` via `pixelAsset()` (`MeetingCaptureApp.swift:4579`) | partial — Qlippy sprites ship; no orb/crystal | `web←craft` | Catalog §9. A *dependency* of the theater (§4) / node canvas, not a standalone win. Generate via PixelLab when §4 lands. |

### 1b. Surfaces where the IPAD is behind on breadth (mobile roadmap, NOT Phase 69)

These are real two-way gaps. They are recorded here so the parity is honest, but they belong
to the **mobile roadmap**, not Phase 69. The iPad does the underlying work on-device already;
what it lacks is the desktop-class *management surface*.

| Feature / Surface | iPad | Web | Gap | Notes |
|---|---|---|---|---|
| **Full config cockpit** | none — `SettingsView` is inference-target only ("where intelligence runs") (`MeetingCaptureApp.swift:1589-1601`) | flagship — 6-section searchable cockpit: appearance / voice typing / wake word / presence / meetings / cloud (`web/src/pages/settings.astro:155-307`) | `iPad←breadth` | Every dictation/meeting knob. The iPad exposes a fraction. |
| **The archive (history) + faceted search** | solid — a meeting list (`MeetingListView` `:2764`), no faceted search | flagship — 3,032-line `/history`: meeting+action list/detail + server-side date/speaker/tag/open-action facets (`web/src/pages/history.astro`, `web/src/scripts/history-app.js:57-289`) | `iPad←breadth` | The archive is web's heaviest breadth surface. |
| **Correction journal + memory/telemetry** | solid — `VoiceCorrectionSheet` captures corrections in-moment (`:4305`) but no journal/digest/replay surface | flagship — the dictation journal + replay + correction memory + the "What HoldSpeak learned" digest (`web/src/scripts/dictation-app.js:9-11`) | `iPad←breadth` | The visible learning loop, as a management surface. |
| **Activity / routing rules** | none | solid — `/activity` routing rules + pre-briefing config (`web/src/pages/activity.astro`, 588 lines) | `iPad←breadth` | — |
| **Onboarding funnel** | solid — in-app first-run flows | flagship — `/welcome` cinematic wizard + `/setup` guided fresh-clone → first dictation (`web/src/pages/welcome.astro`, `setup.astro`) | `iPad←breadth` | — |
| **Voice Commands board** | none | solid — `/commands` voice-macro board (`web/src/pages/commands.astro`, 340 lines) | `iPad←breadth` | — |
| **Companion / AI-PI portal** | flagship — CompanionBoard is *native* on the iPad (it's the companion device) | solid — `/companion` AI-PI portal (`web/src/pages/companion.astro`, 428 lines) | `parity` (different roles) | The iPad is the companion *client*; the web is the host-side portal. Not a gap, a role split. |
| **The dictation cockpit (10-section)** | partial — dictation knobs live in inference settings only | flagship — the `/dictation` cockpit (`web/src/pages/dictation.astro`) | `iPad←breadth` | — |

### 1c. Genuinely ambiguous — owner calls

| Surface | The ambiguity |
|---|---|
| **Companion portal direction** | The iPad *is* the companion device (native CompanionBoard); the web `/companion` is the host-side portal. They're peers in different roles, not a craft/breadth gap. Whether the web portal should adopt any iPad CompanionBoard craft (or stay a control panel) is an **owner call** — left out of Phase 69's scope until decided. |
| **Node-graph Workbench on the web at all** | The Workbench is the iPad's marquee, but it is also the heaviest build (catalog §2) and the web cockpit has never been a visual-builder surface. Whether the web *needs* the full node canvas vs a lighter "pipeline view" is an **owner call** the Phase-69 epic (HS-69-09/10/11) should confirm before the heavy lift. Sequenced last for exactly this reason. |

---

## 2. The ordered delivery backlog — Phase 69 (web delivery)

Sequenced **cheapest-high-impact first**, honoring the catalog's port-priority: the
egress-badge-into-cockpit and the shared depth card primitive first (both reuse existing
assets), the Queue HUD next, the node canvas heaviest and last. Each item names its surfaces,
the catalog pattern(s), priority, dependencies, and the proof required.

All proofs follow the standing owner bar: **show it** (browser screenshots of the real
cockpit, not just a class in the bundle — the Astro-scoped-CSS-on-JS-DOM lesson means a class
shipping ≠ it applying), and where a feature is LLM-shaped, prove it on real metal, not a
no-LLM plumbing pass.

| # | HS-69 id | Title | Surface(s) | Catalog pattern(s) | Priority | Depends on | Proof required |
|---|---|---|---|---|---|---|---|
| 1 | **HS-69-01** | Egress badge → the cockpit | history/meeting/intel cards across `/`, `/history` | §6 egress badge | **HIGH** (cheapest, POSITIONING obligation) | none | Screenshot of cockpit cards carrying the structured `{scope,label}` badge (local / local+cloud / cloud+target); a test/lock asserting cockpit cards render the badge, not prose. |
| 2 | **HS-69-02** | The shared Signal card primitive | app-wide (the substrate) | §1 depth, §8 motion (hairline) | **HIGH** (lifts everything at once) | none | One `.signal-card` utility (surface + gradient hairline + elevation + `.glyph-chip`); before/after screenshots of ≥3 surfaces; the gradient hairline visibly directional, not flat `inset white .04`. |
| 3 | **HS-69-03** | Gradient + hairline tokens | `web/src/styles/tokens.css` | §1, table drift rows | **HIGH** (unblocks 02/04) | none | `--accent-gradient` + `--bg-gradient` added with the iPad values (`MeetingCaptureApp.swift:410-418`); hero surfaces render the wash. (Small; can fold into HS-69-02.) |
| 4 | **HS-69-04** | Materialize + stagger motion | intel results, history rows, queue jobs | §8 motion | **MED→HIGH** (cheap, broad) | HS-69-02 | An `hs-materialize` keyframe (glow + insert/scale) + a stagger helper; screen recording or stepped screenshots of cards arriving with the glow; reduce-motion verified off. |
| 5 | **HS-69-05** | Premium sheets / modals uplift | `ConfirmDialog.astro`, `Panel.astro`, drawers | §5 sheets | **MED** (touches every modal) | HS-69-02 | Grab handle + glyph-chip header + accent "Done" + tinted glow background applied; screenshots of ≥2 dialogs uplifted. |
| 6 | **HS-69-06** | Qlippy dock into the cockpit | the main browser cockpit (off `/presence`) | §6, §9 (Qlippy reuse) | **MED** | HS-69-01 (shared egress component), HS-69-02 | Qlippy dock + cards rendering in the main cockpit (not just `/presence`); cards carry the egress badge; the existing sprite pipeline reused. |
| 7 | **HS-69-07** | The Queue HUD (shell + store) | app-wide (root) | §3 Queue HUD | **HIGH** (glanceable always-on) | HS-69-02 | A shared run-queue store (web has none today, state is per-page) + the collapse/expand floating pill + per-job ledger rows; screenshots of collapsed pill and expanded panel with live jobs; `backdrop-filter` material on `--surface-2`. |
| 8 | **HS-69-08** | Reactive mic waveform | `/dictation`, capture surfaces | §7 waveform | **MED** | none (independent) | Web Audio `AnalyserNode` → rAF canvas bars; recording of the envelope leaping on speech, flat on silence; accent peak glow. |
| 9 | **HS-69-09** | Generation theater (orb + constellation) | intel-streaming surfaces | §4 theater, §9 (orb asset) | **MED** (high wow, lower frequency) | HS-69-02; a web `theaterorb` PixelLab export | The orb breathing/rotating + the type constellation lighting per artifact, driven by live intel WS; proven on real metal (real intel run), not a no-LLM stub. |
| 10 | **HS-69-10** | Node canvas — foundation | a new web builder surface | §2 Workbench | **HIGH (heavy)** | HS-68-03 technical design; owner confirm (§1c) | Pannable/zoomable dot-grid canvas + draggable Signal node cards; screenshots of nodes placed/dragged. (First of the §2 epic.) |
| 11 | **HS-69-11** | Node canvas — wiring + inspector | the builder surface | §2 Workbench, §5 sheets | **HIGH (heavy)** | HS-69-10, HS-69-05 | Type-colored bezier cables with port-compatibility validation + the node palette + the inspector sheet; screenshots of a wired graph; port colors honor the web status palette (signal=`--info`, text=`--accent`, findings=`--ok`). |

**Sequencing rationale.** 01–03 are pure reuse/placement (the badge already exists; the card
primitive is composing tokens already present) — they cash the catalog's "cheapest
high-impact first" immediately and unblock the rest. 04–06 are broad-but-cheap polish that
ride on the card primitive. 07 (Queue HUD) is the first net-new *shell* and the highest
always-on craft, so it leads the heavier work. 08–09 are net-new capabilities gated on
plumbing (Web Audio / a web orb asset + live streaming). 10–11 are the node-canvas epic,
sequenced last because they're the heaviest build and carry an open owner question (§1c) that
HS-68-03's technical design and an owner confirm should close before the lift.

**Folding note.** HS-69-03 is small enough to fold into HS-69-02 if the team prefers fewer
stories; kept separate here so the token-only change is independently reviewable.

---

## 3. iPad-gains-breadth — the short list for the MOBILE roadmap (out of Phase 69 scope)

Recorded so the parity is honestly two-way. These are *not* Phase 69 stories; they go on the
mobile roadmap. The iPad already does the underlying work on-device — each item is a
desktop-class **management surface** it lacks.

1. **Full config cockpit** on the iPad (today `SettingsView` is inference-target only,
   `MeetingCaptureApp.swift:1589`). The biggest breadth gap.
2. **Faceted archive search** on the iPad (the meeting list has no facets;
   `MeetingListView:2764`).
3. **The visible learning loop as a surface** — journal + replay + correction memory + the
   learning digest (the iPad captures corrections in-moment via `VoiceCorrectionSheet:4305`
   but has no journal/digest/replay screen).
4. **Activity / routing rules** surface.
5. **Voice Commands board.**
6. **The onboarding funnel** (welcome wizard + guided setup).
7. **Status-palette re-tune** — adopt the canonical web `ok/warn/danger/local` values (the
   web-wins decision, `current-phase-status.md:86-92`). Small, already tracked in
   MASTER-EXECUTION.
8. **Egress badge structure** — the iPad adopts the web's `{scope,label}` badge to replace its
   pre-badge prose idiom (`MeetingCaptureApp.swift:1570-1571, 4934-4941`), the reverse of
   HS-69-01.

---

## 4. Open / ambiguous (owner calls, surfaced not guessed)

1. **Companion portal direction** (§1c) — peers in different roles, not a gap. Whether
   `/companion` adopts iPad CompanionBoard craft or stays a control panel is unresolved.
2. **Node canvas on the web at all** (§1c) — the heaviest port; whether the web needs the full
   node graph vs a lighter pipeline view is an owner call HS-69-10 should confirm before the
   lift. This is why it sits last.
3. Anything requiring the apps to be *run* to judge (e.g. exact felt-motion timing parity)
   cannot be settled from source alone; the Phase-69 proofs (screenshots / real-metal runs)
   are where that gets confirmed, per the standing "show it" bar.
