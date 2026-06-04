# Phase 36 — Meeting Intelligence & Experience

> **Note:** the folder slug (`phase-36-meeting-artifact-experience`) predates a scope
> expansion. Opened 2026-06-04 as an artifact-presentation phase; the same day the user
> expanded it to also **fix the intent-extraction weakness** the messy-meeting e2e
> surfaces. Title broadened to "Meeting Intelligence & Experience"; slug kept to avoid
> link churn.

**Status:** in-progress (opened 2026-06-04). 4/6 stories shipped.

**Last updated:** 2026-06-04 (**HS-36-02 shipped — copy-as-Markdown.** Each elevated
card now has a **"Copy"** button (in the HS-36-01 header slot) and the Artifacts section
has a **"Copy all"** control. Both serialize the artifact `structured_json` to clean
Markdown from the *data* (so a collapsed card still copies) and write to the clipboard
reusing the `CommandPreview` pattern (copied-state + graceful `Press ⌘C` fallback).
Per-type serializers (`artifactMarkdown` / `allArtifactsMarkdown` in `history-app.js`):
tabular → Markdown table with `|` escaped + empty cells `—`; timeline → ordered list;
sectioned types → `###` headings; diagram → ```` ```mermaid ```` fence; fallback →
`body_markdown`. Verified by a Node serializer harness over the real module (output in
evidence), bundle rebuilt + helper present in `_built` (gitignored, not committed),
selectors untouched, suite 2020/15. Next: HS-36-03 (per-type body polish) → HS-36-06
closeout. Earlier: **HS-36-01 shipped — elevated artifact cards.** The flat
`.segment` artifact rendering is replaced by Signal **artifact cards** (type-colored
accent edge + icon + title + type chip + meta + collapse toggle + overflow-safe body),
and the **risk-table overflow is fixed** (`.table-scroll`). Source committed; bundle
rebuilt locally (it's a gitignored build product, not committed); selectors preserved
(incident e2e green); suite 2020/15; new-look screenshot
`evidence/artifact_cards_new_look.png`. Next: HS-36-02 (copy-as-Markdown) → HS-36-03
(per-type polish) → HS-36-06 (closeout, re-captures the before/after in the new cards).
Earlier: **HS-36-05** — the intelligence fix + before/after. A gated, additive
**per-segment LLM intent probe**
(`plugins/segment_probe.py`, merged max into `score_window`) fishes out
brief/paraphrased intents the lexical scorer drops. On the *same* messy meeting via the
*same* real routing path: **BEFORE** = `['architecture','product']` / 7 artifact types,
incident+comms lost; **AFTER** = `['architecture','comms','delivery','incident','product']`
/ **13** types, with incident_timeline / runbook_delta / stakeholder_update /
decision_announcement fished out. Default path byte-identical (routing tests unchanged);
suite 2020/15; both screenshots in `evidence/`. Next: HS-36-01 (UI cards) + HS-36-06
closeout).

## Goal

Make HoldSpeak's meeting intelligence actually deliver on **real, messy meetings** —
end to end. Two halves:

1. **Extraction (intelligence).** Today a long, digression-heavy meeting can *silently
   lose* a real intent: the pipeline scores fixed 90s rolling windows with lexical
   keyword matching, so a brief-but-clear signal (a risk mentioned once in a 20s aside
   amid chatter) is diluted below the 0.6 activation threshold — the intent never
   fires and its plugin never runs. Fix it by **segmenting the conversation and probing
   each segment for intent** ("fishing out" the intent per segment), so a clearly-incident
   segment activates the incident chain regardless of surrounding noise.
2. **Experience (presentation).** The fourteen artifact types render as basic chips +
   flat lists/tables inside a generic card (missed by the Phase-30 "Signal" pass), wide
   content (the risk table) overflows horizontally, and there's no way to lift content
   out as Markdown. Fix all three — Signal **artifact cards**, **copy-as-Markdown**,
   **overflow-safe** rendering.

The messy-meeting spoken-e2e (HS-36-04) is the thread that ties them together: it
reproduces the extraction weakness *and* produces the dense, varied artifact set that
showcases the new presentation.

## Scope

### In

- **Elevated artifact-card shell + overflow-safe layout (HS-36-01).** Replace the
  generic `.segment` artifact container with a Signal "artifact card": a type-colored
  accent edge, a header row (type icon + title + type chip + collapse toggle), and a
  body region that contains overflow. Fix the **risk-table horizontal overflow** (and
  any other wide artifact) via an overflow-safe scroll container + sensible cell
  wrapping. Card chrome is shared across all artifact types.
- **Copy-as-Markdown per artifact (HS-36-02).** A per-artifact "Copy" button that
  serializes that artifact's `structured_json` to clean Markdown (headings, tables,
  lists per type) and writes it to the clipboard, reusing the `CommandPreview`
  clipboard pattern (copied-state feedback, graceful fallback). Plus a "copy all
  artifacts" affordance for the meeting.
- **Per-artifact-type body polish (HS-36-03).** Apply the Signal treatment to each
  renderer's *body* (timeline, runbook delta, risk register, stakeholder update,
  decision announcement, decisions/open-questions, requirements, ADR, milestone plan,
  dependency map, scope review, customer signals, action items, mermaid) — typed
  status colors, iconography, spacing, density — so each reads as a designed block,
  not a flat dump.
- **Dynamic, digression-heavy multi-topic spoken-e2e (HS-36-04).** A third spoken-e2e
  scenario: one long, messy, human-sounding meeting (small talk, tangents,
  interruptions, callbacks) spanning several intents, so several plugin chains fire and
  a dense/varied artifact set results. Dual purpose — stress-tests pipeline signal
  extraction against noise, *and* is the rich showcase fixture for the new cards.
  Structural, noise-tolerant assertions (≥3 distinct artifact types; no exact-type/wording
  pins). Opt-in like the others.
- **Segment-aware intent extraction — the routing fix (HS-36-05).** Replace/augment
  the fixed-90s-window + lexical-keyword scoring with **per-segment intent probing**:
  segment the meeting into topic-coherent chunks and probe each for the intents it
  exhibits, **LLM-assisted** (consistent with the plugin egress posture; the `.43`
  endpoint), with the **existing lexical scorer kept as a deterministic fallback** when
  the `llm` capability is unavailable. Aggregate the per-segment intents (union) so a
  brief-but-clear intent isn't diluted away, and dispatch each plugin with its relevant
  segment(s) as local context. Behind a config gate; deterministic path stays unit-tested;
  the messy-meeting e2e (HS-36-04) proves the brief-intent-now-surfaces behavior on real
  `.43`.
- **Closeout (HS-36-06).** Rebuild the bundle; verify/update the spoken-e2e selectors
  in lockstep; capture before/after screenshots (the dynamic meeting is the headline
  showcase); `final-summary.md`.

### Out

- **New artifact *types* / renderers** for types that don't exist yet, or changes to a
  plugin's *output* `structured_json` shape (the extraction fix changes *which* plugins
  run + *what segment* they see, not the artifact schema).
- **Export-to-file / download** beyond clipboard Markdown (a later idea; clipboard is
  the asked-for facility).
- **A non-dark / light theme** for artifacts — Signal is dark-first.
- **Reworking the lexical scorer's keyword lists** as the primary fix — the segment
  probe supersedes keyword-threshold dilution; keywords stay only as the deterministic
  fallback.

> **Scope note (changed 2026-06-04):** the original "presentation only — no router /
> plugin-dispatch changes" boundary is **lifted**. HS-36-05 deliberately changes how the
> meeting is segmented and how intents are detected + dispatched. The *artifact data
> shapes* are still unchanged.

## Exit criteria (evidence required)

- [ ] Artifacts render as elevated Signal cards (accent edge + header + contained
      body); the generic `.segment` chrome is gone for artifacts. (HS-36-01)
- [ ] The risk table (and every wide artifact) no longer overflows the modal — content
      scrolls within its card; verified at a narrow viewport. (HS-36-01)
- [ ] Each artifact has a working "Copy as Markdown" button (clipboard write +
      copied-state); the produced Markdown is well-formed per type. (HS-36-02)
- [ ] Every artifact type's body got the Signal polish pass. (HS-36-03)
- [ ] A third spoken-e2e (dynamic, digression-heavy, multi-topic) exists, is opt-in,
      and verified once for real against `.43`; structural/noise-tolerant assertions
      (≥3 distinct artifact types, no exact-type/wording pins). (HS-36-04)
- [ ] Segment-aware intent extraction: a meeting is segmented + each segment probed for
      intent; a brief-but-clear intent that the old fixed-window/keyword path diluted
      below threshold now activates its chain and produces its artifact — proven by a
      regression test (deterministic path) + the messy-meeting e2e on real `.43`. The
      deterministic lexical fallback still works with the `llm` capability off. (HS-36-05)
- [ ] `cd web && npm run build` succeeds and the source change reaches the rebuilt
      bundle (the bundle is a **gitignored build product** — not committed; built at
      install/package time); `tests/e2e/test_spoken_meeting_e2e.py` selectors pass
      (preserved or updated in lockstep). (all)
- [ ] **Before/after comparison captured:** two screenshots of the *same* messy meeting
      — `evidence/dynamic_meeting_before.png` (old routing, intents diluted away, sparse)
      and `_after.png` (segment-probe routing, the present intents fished out, rich cards)
      — with a quantified delta in `final-summary.md`. (HS-36-04 captures before; HS-36-05
      after; HS-36-06 presents.)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout; the routing
      unit/integration tests updated in lockstep (not silenced); the dynamic-meeting
      spoken-e2e re-run for real shows the new extraction + the new look. (HS-36-06)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-36-01 | Elevated artifact-card shell + overflow-safe layout | done | [story-01-artifact-card-shell.md](./story-01-artifact-card-shell.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-36-02 | Copy-as-Markdown per artifact | done | [story-02-copy-as-markdown.md](./story-02-copy-as-markdown.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-36-03 | Per-artifact-type body polish | not-started | [story-03-per-type-body-polish.md](./story-03-per-type-body-polish.md) | — |
| HS-36-04 | Dynamic, digression-heavy multi-topic spoken-e2e | done | [story-04-dynamic-meeting-e2e.md](./story-04-dynamic-meeting-e2e.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-36-05 | Segment-aware intent extraction (fish out intent per segment) | done | [story-05-segment-intent-extraction.md](./story-05-segment-intent-extraction.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-36-06 | Phase closeout + final-summary | not-started | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

Opened 2026-06-04 immediately after Phase 35 closed (merged via PR #11; the config
hardening follow-up is PR #12). Phase 35 made the plugin system extensible; this phase
makes its *output* look the part. The recon is done: artifacts render in
`web/src/pages/history.astro` (~856–1136) via Astro + Alpine, the Signal tokens live in
`web/src/styles/tokens.css`, a reusable clipboard pattern exists in
`CommandPreview.astro`, the risk-table overflow is a missing `overflow-x` container +
unbounded cells, and the spoken-e2e pins several artifact selectors. Direction chosen
by the user: **Elevated cards**. Numbering: this took the Phase 36 slot; **Actuators
moved to Phase 37**. The user then asked to add a **dynamic, digression-heavy
multi-topic spoken-e2e** (HS-36-04) — a messy, human-sounding meeting — *and* to have
the phase **fix the routing weakness that meeting exposes**, not just test it. A second
recon mapped MIR-01: fixed 90s rolling windows (`intent_timeline.build_intent_windows`)
+ lexical keyword scoring (`plugins/signals.extract_intent_signals`) + a 0.6 threshold
(`plugins/router.select_active_intents`); plugins already get window-local context
(`plugins/dispatch.dispatch_window`). The weakness: a brief signal-dense aside is
diluted across its 90s window below threshold → the intent never activates → its plugin
never runs (silent loss); keyword-only scoring also misses paraphrase. The fix
(HS-36-05): **segment + probe each segment for intent** (LLM-assisted, lexical
fallback) + aggregate the union. Closeout bumped to HS-36-06. Two tracks now —
intelligence (04→05) and experience (01–03) — joined at the closeout. HS-36-01 (card
shell + overflow fix) first as the most visible win; HS-36-04+05 are the intelligence
core.

## Pickup order

1. HS-36-01 — elevated card shell + overflow-safe layout ✅ **done** (cards + overflow
   fix shipped; selectors preserved).
2. HS-36-02 — copy-as-Markdown ✅ **done** (per-card Copy + Copy-all; pure per-type
   serializers; clipboard reuse of the `CommandPreview` pattern).
3. HS-36-03 — per-type body polish (fills in each artifact body within the new shell). **◀ next**
4. HS-36-04 — dynamic/messy multi-topic spoken-e2e ✅ **done** (BEFORE captured; the
   routing drops incident/risk/comms).
5. HS-36-05 — segment-aware intent extraction ✅ **done** (probe fishes the dropped
   intents out; AFTER captured — 7 → 13 artifact types).
6. HS-36-06 — closeout + final-summary.

Intelligence track (04 → 05) is **complete**; on the experience track, **HS-36-01
(elevated cards + overflow fix) and HS-36-02 (copy-as-Markdown) are done**. **◀ next:
HS-36-03** (per-type body polish) → HS-36-06 closeout (which re-captures the before/after
in the new cards).

The two tracks are parallel: **experience** (01 → 02 → 03) and **intelligence**
(04 → 05). Either can go first; the closeout (06) needs both. HS-36-01 leads since it's
the most visible win and unblocks the UI track.

**Headline deliverable (user-requested):** a **before/after** of the *same* messy
meeting — HS-36-04 captures `evidence/dynamic_meeting_before.png` on the current routing
(intents diluted away → sparse), HS-36-05 captures `_after.png` on the new segment-probe
routing (the genuinely-present intents fished out → rich cards). The diff is the phase's
money shot; the closeout (HS-36-06) presents it with a quantified delta.

**HS-36-04 shipped (2026-06-04).** The messy meeting runs through the real
`process_meeting_state` routing on `.43` and **caught the weakness exactly as
predicted**: across 5 windows it activated only `['architecture', 'product']` and
silently dropped the meeting's clear **incident** (described as "fell over… rolled it
back… bad deploy ate the connection pool" — none of which match the `incident`/`rollback`
keywords), **risk**, and **comms** ("announcing…" scored ≈0.22, under 0.6). BEFORE =
7 artifact types (action_items, adr, customer_signals, decisions, diagram, requirements,
scope_review) with **no** incident_timeline / risk_register / runbook_delta /
stakeholder_update / decision_announcement. `dynamic_meeting_before.png` captured;
reproduced across two runs (deterministic baseline). The AFTER (HS-36-05) is now the
clear target: fish those intents out per segment so the missing five types appear.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Renaming artifact CSS classes breaks the spoken-e2e selectors | High (if careless) | Preserve the asserted class names (`.risk-table tbody tr`, `.incident-timeline li`, …) or update the e2e in the same commit; keep them as inner elements within the new card | An e2e `wait_for_selector` times out |
| Forgetting to rebuild the bundle → source edits don't show | Medium | `cd web && npm run build` before verifying/screenshotting (the bundle is gitignored + built at install from `web/src`, so it won't auto-refresh); never commit `_built` | The served app / e2e looks unchanged after an edit |
| Collapsible cards hide content from the e2e / from copy | Medium | Default artifact cards to expanded; copy reads from data, not the DOM | e2e can't see a collapsed body |
| Scope creep into export-to-file / new artifact types | Medium | Clipboard Markdown only; no new artifact *types* / no artifact-schema changes | A PR adding a new artifact type or changing a plugin's output shape |
| Routing fix (HS-36-05) regresses the existing chains / tests | High (expected churn) | Update `test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing` in lockstep — don't silence; keep the deterministic lexical path green; the segment path is additive + gated | A `-k`-filtered green hiding a real routing diff |
| LLM segment-probe adds latency / nondeterminism / is unavailable | Medium | LLM path is gated on the `llm` capability with the lexical scorer as fallback; assertions on the LLM path are structural (like the spoken-e2e); it runs at meeting finalization, not realtime | The probe blocks finalization or flakes the suite |
| Segment probe sends transcript to the LLM (egress) | Low | Same egress posture as the existing plugins (already send transcript to the configured endpoint); honors the Phase-25 provider gate; off when `llm` capability is off | A probe egressing where plugins wouldn't |

## Decisions made (this phase)

- 2026-06-04 — **Direction = "Elevated cards"** (vs tabbed workspace / notebook feed) —
  user pick from previewed options.
- 2026-06-04 — **Numbering: UI overhaul = Phase 36, Actuators → Phase 37** — user pick;
  the "teed-up Phase 36 — Actuators" references in HANDOVER/README updated accordingly.
- 2026-06-04 — **Scope expanded from presentation-only to also fix the intent-extraction
  weakness** (HS-36-05) — user direction ("the phase should also fix that weakness …
  divide the meeting into segments and probe them for intent"). The "no router changes"
  guard is lifted; artifact *data shapes* stay unchanged.
- 2026-06-04 — **Fix approach = segment-aware, LLM-assisted per-segment intent probing
  with a deterministic lexical fallback** (agent design; user delegated "you know best
  how to best address this"). Rationale: directly implements "fish out intent per
  segment", robust to paraphrase + dilution, consistent with the existing plugin egress
  posture; the lexical path stays for determinism/tests + offline.

## Decisions deferred

- Whether to add export-to-file (download .md / .json) in addition to clipboard —
  trigger: HS-36-02 — default: clipboard only this phase (the asked-for facility).
- Whether artifact cards should be collapsible by default vs always-expanded —
  trigger: HS-36-01 — default: always-expanded (keeps e2e + copy simple), add a
  collapse toggle that defaults open.
- Segmentation granularity + whether the LLM does segmentation *and* intent in one pass
  vs. fixed/finer windows + an LLM intent probe per window — trigger: HS-36-05 design
  spike — default: one LLM pass returning topic segments + their intents, with the
  fixed-window path as the deterministic fallback.
