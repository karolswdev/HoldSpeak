# HS-68-01 — The cross-platform design-pattern catalog

- **Project:** holdspeak
- **Phase:** 68
- **Status:** in-progress — the catalog is **authored 2026-06-22** at `design-pattern-catalog.md` (this phase dir); formal close pending its `evidence-story-01.md` (downgraded from `done` during the HSM-14-19 wholesale checkpoint, which has no per-story evidence). All nine
  patterns named, specified, traced to Swift `file:line`, mapped onto the existing web tokens with
  reuse-vs-new verdicts + port-priority, plus a reconciled shared-token table. Headline: the foundation
  is **byte-identical** (accent `#FF6B35`, the surface + text ramps) — convergence is apply-not-redesign.
  Open owner decision surfaced: the **status palette diverged** (iPad vs web greens/ambers/reds) — the
  catalog recommends web-wins (WCAG contrast), re-tune iPad.
- **Depends on:** none
- **Unblocks:** HS-68-02, HS-68-03
- **Owner:** unassigned

## Problem

The iPad Swift app's design patterns live only in code (`apple/App/MeetingCaptureApp.swift` +
`apple/Sources/`) and in the owner's head. There is no single specification that names them, defines
them platform-neutrally, and maps them onto the **existing** web "Signal" token system
(`web/src/styles/tokens.css`). Without that catalog, porting to the web is guesswork and the two
platforms keep diverging. (The Phase-30 web design-language doc
`phase-30-ui-ux-overhaul/evidence/design-language-signal.md` is the web-side anchor to extend.)

## Scope

- **In:** a written catalog — `docs/internal/DESIGN_LANGUAGE_SIGNAL.md` (or an agreed path) — that, for
  each iPad pattern, gives: the name, what it is, the rules (tokens/spacing/motion/states), a reference
  to the Swift source, the **equivalent web token(s)** that already exist, and a **reuse-vs-new** verdict
  (does the web token cover it, or is something new needed). The patterns to catalog (from the shipped
  iPad app):
  1. **Signal depth** — the elevated card (layered fill + top-lit hairline + soft shadow), the glyph
     chip (gradient rounded icon), pressable scale-on-press, gradient/glow tokens. *(Web has the tokens:
     `--surface-*`, `--elev-*` with inset hairline, `--accent`/`--glow-accent` — under-applied.)*
  2. **The node-graph Workbench** — typed draggable nodes, **type-colored bezier cables**
     (signal=cobalt / text=amber / findings=green), a pannable/zoomable **dot-grid canvas**, port
     wiring, tap-to-inspect, the palette, run-pulses. *(Web: none.)*
  3. **The Queue HUD** — a Dynamic-Island-style pill → an expandable job ledger; the status vocabulary
     (working / blocked / queued / done), progress bars, origin/target chips; app-wide above every
     screen. *(Web: none; web has per-surface WS state to feed it.)*
  4. **The generation theater** — the "model thinking" visualization (plasma orb + a constellation of
     target types lighting up as each is produced). *(Web: none; web has live intel streaming.)*
  5. **Premium sheets / modals** — custom presentation (no default chrome), a real grab handle, a
     designed header, depth. *(Web: drawers exist; modals are plainer.)*
  6. **The egress badge** — `egress:{scope,label}`, one badge (local / local+cloud / cloud→target).
     *(Web HAS it — but mostly on Qlippy/`/presence`; the catalog notes "pull into the cockpit".)*
  7. **The reactive mic waveform** — a voice-dominant level meter (gain + gamma + peak glow).
     *(Web: none; needs a Web Audio `AnalyserNode`.)*
  8. **Materialize / settle motion** — cards glow+insert on arrival, staggered entrances, the "Signal
     settle" ease. *(Web: tokens exist (`--ease-standard`, `hs-pulse`); applied conservatively.)*
  9. **PixelLab bespoke assets** — generated pixel-art (theaterorb, crystal, Qlippy sprites).
     *(Web: Qlippy sprites exist under `/_built/qlippy/`.)*
- **Out:** building any of it (HS-68-03 designs the build; Phase 69 builds). The two-way *feature*
  inventory (HS-68-02 owns that; this story is the *design-pattern* layer).

## Acceptance criteria

- [ ] A catalog doc exists covering all nine patterns, each with: definition, rules, Swift source ref,
      the existing web token(s) it maps to, and a reuse-vs-new verdict.
- [ ] The web "Signal" tokens are reconciled with the iPad's — a single shared token vocabulary table
      (accent, surfaces, elevation/hairline, motion, type), noting any drift to align.
- [ ] Each pattern is rated **port-priority** (high/med/low) by craft impact, as input to HS-68-02's
      ordering.
- [ ] Traced against real files on both platforms (Swift source + `web/src/styles` + components).

## Test plan

- Documentation story: the "test" is tracing — every cited token/file/pattern verified to exist (the
  voice/doc guards pass; no broken refs). Reviewed against the shipped iPad screenshots from Phase 14/15
  so the catalog matches what actually shipped, not an idealized version.
