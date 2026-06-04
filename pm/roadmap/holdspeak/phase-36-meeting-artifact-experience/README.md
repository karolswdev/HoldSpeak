# Phase 36 — Meeting Intelligence & Experience

> Folder slug (`phase-36-meeting-artifact-experience`) predates a same-day scope
> expansion; title broadened, slug kept to avoid link churn.

**Status:** in-progress (opened 2026-06-04; runs after Phase 35).

The plugin system can now *produce* fourteen kinds of meeting artifacts (Phases
16→29) and others can *extend* it (Phase 35). But on **real, messy meetings** it falls
down at both ends, and this phase fixes both:

1. **Intelligence — the right intents don't always get extracted.** MIR-01 scores
   fixed 90s rolling windows with lexical keywords, so a brief-but-clear signal (a risk
   raised once in a 20s aside amid chatter) is diluted below the 0.6 activation
   threshold → the intent never fires → its plugin never runs → the signal is *silently
   lost*. The fix: **segment the conversation and probe each segment for intent**
   ("fish out" intent per segment), LLM-assisted with the existing lexical scorer as a
   deterministic fallback, aggregating the union so nothing is diluted away.
2. **Experience — the output looks basic.** The artifacts render as chips + flat
   lists/tables in a generic `.segment` card (missed by the Phase-30 "Signal" pass),
   wide content overflows (the risk table), and there's no copy facility. Direct user
   feedback (2026-06-04): *"the pills are so basic … the content often overflows
   horizontally … looks very basic and completely not what I like."* The fix: Signal
   **artifact cards**, **copy-as-Markdown**, **overflow-safe** rendering.

A **dynamic, digression-heavy spoken-e2e** (HS-36-04) ties the two together: it
reproduces the extraction weakness on the real routing path and yields the dense
artifact set that showcases the new presentation. The **headline deliverable** is a
**before/after** of that same meeting — old routing (sparse, intents lost) vs new
segment-probe routing (rich, intents surfaced) — rendered in the new cards.

Scope note: the original "frontend/UX only, no router changes" boundary was **lifted**
the same day at user direction. The intelligence track changes segmentation + intent
detection + dispatch; the artifact *data shapes* stay unchanged.

## Chosen direction (user, 2026-06-04)

**"Elevated cards."** Each artifact is a distinct elevated card: a type-colored
accent edge, a header row (type icon + title + type chip + copy button + collapse
toggle), and an overflow-safe body. Tables and other wide content scroll within the
card instead of blowing out the modal width.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `web/src/pages/history.astro` — the artifact renderers (~lines 856–1136) + their CSS
  (the `.segment`, `.risk-table`, `.incident-timeline`, `.runbook-list`,
  `.stakeholder-update`, `.announcement-artifact`, … blocks).
- `web/src/scripts/history-app.js` — the Alpine data layer (`openMeeting`, the
  `risksFor`/`hasStructuredRender` helpers).
- `web/src/styles/tokens.css` — the Signal token set (surfaces, accent `#FF6B35`,
  status colors, spacing/type/radius/elevation/motion scales).
- `web/src/components/CommandPreview.astro` — the canonical
  `navigator.clipboard` + `[data-*-copy]` delegator pattern to reuse for copy.
- `../phase-30-ui-ux-overhaul/` — the "Signal" design language this phase applies to
  artifacts.

### For the intelligence track (HS-36-04/05)

- `holdspeak/intent_timeline.py` — `build_intent_windows` (the fixed-90s windowing).
- `holdspeak/plugins/signals.py` — `extract_intent_signals` (lexical keyword scoring).
- `holdspeak/plugins/router.py` — `select_active_intents` (0.6 threshold + hysteresis),
  `build_plugin_chain`, `PROFILE_PLUGIN_BASE_CHAINS` / `_INTENT_PLUGIN_CHAIN`.
- `holdspeak/plugins/dispatch.py` — `dispatch_window` (per-window plugin context).
- `holdspeak/plugins/pipeline.py` / `holdspeak/meeting_session.py` — `process_meeting_state`
  + the MIR finalization wiring.
- `holdspeak/intel/` (`build_configured_meeting_intel`) — the LLM seam for the segment probe.

## Phase boundaries

**Two tracks: intelligence (extraction) + experience (presentation).** What stays
unchanged: each plugin's **output `structured_json` shape**, the set of artifact
*types*, and the API. What this phase *does* change: the meeting **segmentation**, how
**intents are detected** (segment probe), how plugins are **dispatched** (which run +
what segment they see), and the artifact **rendering**. (The "frontend-only / no router
changes" boundary the phase opened with was lifted the same day at user direction.)

The artifact CSS **selectors asserted by the spoken-e2e**
(`tests/e2e/test_spoken_meeting_e2e.py`: `.risk-table tbody tr`, `.incident-timeline li`,
`.runbook-list .runbook-change`, `.stakeholder-update`, `.announcement-artifact .announcement`,
…) must keep working — preserved or updated in lockstep (never silently broken). The
routing unit/integration tests (`test_intent_router` / `test_intent_dispatch` /
`test_multi_intent_routing`) are updated **in lockstep, not silenced**. The web bundle
(`holdspeak/static/_built/`) is **gitignored** (`.gitignore:55`) — a build product built
from `web/src/**` at install (`scripts/install.sh`) / packaged into the wheel, **not**
committed. Rebuild it (`cd web && npm run build`) before verifying/screenshotting so the
served app reflects the source; commit only the source. The `ui-ux-pro-max` design skill (vendored at
`.claude/skills/ui-ux-pro-max`) is the design aid, as in Phase 30.
