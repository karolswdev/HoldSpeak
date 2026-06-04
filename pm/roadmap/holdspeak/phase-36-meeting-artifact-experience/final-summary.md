# Phase 36 — Meeting Intelligence & Experience — Final Summary

**Status:** CLOSED ✅ — 6/6 stories shipped. **Closed:** 2026-06-04.

The phase that makes HoldSpeak's meeting intelligence deliver on **real, messy
meetings** end-to-end — on both halves of the problem. **Intelligence:** a brief,
clearly-stated intent buried in a digression used to be *silently lost* (the fixed-90s
rolling window + lexical-keyword scorer diluted it below the 0.6 activation threshold).
**Experience:** the artifacts that *did* survive rendered as flat chips + bare lists,
overflowed horizontally, and couldn't be lifted out. Both are fixed, and the same messy
meeting is the thread that proves it.

## The headline — same meeting, before vs. after

| | intents active | artifact types | rendered cards |
|---|---|---|---|
| **BEFORE** (fixed-window/keyword routing) | 2 — `architecture`, `product` | **7** | 23 |
| **AFTER** (segment-probe routing) | 5 — `+comms`, `+delivery`, `+incident` | **13** | 51 |

The meeting's plainly-spoken incident ("Prod fell over… checkout was down… we rolled it
back… a bad deploy that ate the connection pool") and comms ("I'll send a note to the
wider team announcing the changes") matched none of the lexical keywords and scored under
threshold — so in the BEFORE their chains never fired. The segment probe reads each
window by *meaning*, fishes them out, and their `incident_timeline` / `runbook_delta` /
`stakeholder_update` / `decision_announcement` artifacts appear. Captured on real `.43`
in the new cards: `evidence/dynamic_meeting_before.png` vs `_after.png`.

## What shipped

| Story | Target → result |
|---|---|
| **HS-36-01** | Elevated Signal **artifact cards** — type-colored accent edge + header (icon + title + type chip + meta + collapse toggle) + overflow-safe body; the generic `.segment` artifact chrome is gone. The **risk-table horizontal overflow** is fixed (`.table-scroll` + min-width + cell wrap). Asserted inner selectors preserved. |
| **HS-36-02** | **Copy-as-Markdown** — a per-card "Copy" button + a meeting "Copy all", serializing each artifact's `structured_json` to clean Markdown from the *data* (collapsed cards still copy), reusing the `CommandPreview` clipboard pattern. Pure per-type serializers (table with escaped `\|`, ordered timeline, sectioned headings, mermaid fence, fallback). |
| **HS-36-03** | **Per-type body polish** — root-caused the flatness (bodies referenced non-existent `--color-*`/`--font-weight-bold`/`--text-default` tokens → off-palette fallbacks; all migrated to real Signal status tokens) and designed each body: incident **timeline rail** (line + node dots), typed badges (requirements/risk/runbook/scope/signal), accent markers (decisions/stakeholder), left-accented sub-cards (action/adr/milestone/announcement), dependency node chips. CSS-only; selectors untouched. |
| **HS-36-04** | A third opt-in **dynamic/messy multi-topic spoken-e2e** through the **real** routing path — caught the weakness live (BEFORE = 7 types; incident/risk/comms dropped) and captured the BEFORE. |
| **HS-36-05** | **Segment-aware intent extraction** — an additive, gated per-segment LLM intent probe (`plugins/segment_probe.py`, merged element-wise `max` into `score_window`) that surfaces brief/paraphrased intents the lexical scorer drops; the lexical path stays as the deterministic fallback (probe off → byte-identical, routing tests unchanged). AFTER = 13 types. |
| **HS-36-06** | Closeout — re-ran the spoken-e2e on `.43` to re-capture the before/after **in the new cards**, this summary, README → done, HANDOVER refreshed. |

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **2,020 passed, 15 skipped** (spoken-e2e module skips cleanly without
  `HOLDSPEAK_SPOKEN_E2E=1`).
- **Spoken-e2e verified for real on `.43`** (Qwen3.5-9B-Q6): the dynamic before + after
  + incident-retro all passed (`3 passed in 245.99s`); selectors resolve inside the new
  `.artifact-card` body; before/after re-captured in the polished cards.
- **Routing invariants intact:** the default `segment_probe=None` path is byte-identical,
  so `test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing` are
  unchanged and green; the 13 new `test_segment_probe.py` tests cover the additive path
  (incl. the natural-language-incident regression).
- **Bundle:** `holdspeak/static/_built/` is a gitignored build product — rebuilt to
  verify, **0 files tracked**; only `web/src/**` source is committed.
- **Artifact data shapes unchanged** — the intelligence fix changes *which* plugins run
  and *what segment* they see, not the artifact schema; the experience track is
  presentation-only.
- **Branch:** `phase-36/hs-36-01-artifact-card-shell` (phase open + 6 story commits).

## Decisions of record

- **Direction = "Elevated cards"** (over tabbed workspace / notebook feed) — user pick.
- **Scope expanded** from presentation-only to also fix the intent-extraction weakness
  (HS-36-05) — user direction; the "no router changes" guard lifted, artifact data
  shapes kept.
- **Fix approach = segment-aware, LLM-assisted per-segment probing with a deterministic
  lexical fallback** — robust to paraphrase + dilution, consistent with the plugin
  egress posture, gated on the `llm` capability.
- **Numbering:** the UX phase took the Phase 36 slot; **Actuators → Phase 37**.

## Handoff → Phase 37 (Actuators)

The host's `actuator` plugin kind stays **blocked** (Phase 35 built its groundwork: the
authoring guide + pack manifest + discovery loader; `plugin_sdk.validate_manifest`
rejects `actuator` as deferred). Phase 37 adds the **preview → human approval → external
side effect** loop (RFC open question #5), intersecting the Phase-25 egress posture.
Scaffold a `phase-37-actuators/` folder + stories when starting.
