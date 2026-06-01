# Phase 27 — Ubiquitous plugins + spoken-meeting e2e

**Last updated:** 2026-06-01 (HS-27-04 shipped — `requirements_extractor` flipped from stub to a real LLM plugin: extracts + classifies requirements into functional / non-functional / constraint / acceptance, with a grouped-by-type structured `/history` render. No routing ripple (already in the balanced + architect base chains). The spoken e2e now exercises **all four** real plugins and screenshots them. Verified live on `.43` Q6. Phase **in-progress, 4/5**).

> Lineage note: Phase 16 (`first-real-plugin`) proved the LLM-backed plugin
> pattern end-to-end with `mermaid_architecture`. Its docs refer to "phase 17" as
> the follow-on that flips the remaining stubs — but phase 17 was already taken
> (`device-initiative`), so this follow-on is **Phase 27**. Read Phase 16's
> `final-summary.md` first; this phase is its direct continuation.

## Goal

Flip the highest-value `DeterministicPlugin` stubs to **real** LLM-backed plugins
— starting with the ones useful on *almost every* meeting, not niche ones — and
prove the whole stack with a **real spoken-meeting end-to-end harness**: a mock
meeting is synthesized with `say`, transcribed by Whisper, routed through MIR,
processed by the real plugins against the live `.43` LLM, persisted, and rendered
in the web UI — captured as screenshots.

The substrate is already proven (Phase 16); this phase is about **breadth**
(more real plugins) + **confidence** (a true e2e you can watch and screenshot).

## Scope

### In

- Real `run()` for ubiquitous stub plugins, re-using the Phase-16 pattern
  (LLM call via `resolve_intel_provider` → parse/validate → structured output →
  synthesis body → web render). Lead with the ones that fire on almost every
  meeting.
- A spoken-meeting e2e harness: `say` → wav → `Transcriber` → MIR → `PluginHost`
  → `synthesize_and_persist` → web → Playwright (Python) screenshots. Real endpoints
  (local Whisper + `.43` Q6 LLM), opt-in (slow), structural assertions.
- Web rendering for any new artifact *shapes* the new plugins introduce (text /
  checklist bodies render via the existing markdown path; only diagrams need the
  mermaid SVG path from HS-16-04).
- Phase exit: RFC reality-status table updated (flip the plugins shipped here),
  `final-summary.md`.

### Out

- Flipping **all** twelve remaining stubs in one phase — pick the ubiquitous
  few; the long tail (incident/runbook/stakeholder/customer-signal) is a later
  phase.
- `actuators` / external side effects (Jira/Slack/GitHub). Disabled by default
  per the RFC; out of scope.
- Live-meeting plugin hooks (running plugins during an active meeting). Saved /
  recorded meetings only, per Phase 16's carried-forward decision.
- Editing artifacts in the web UI. Read-only render.
- Cross-network / hardware work (Phase 15 / Phase 24).

## Exit criteria (evidence required)

- [x] At least the ubiquity champion (`action_owner_enforcer`) ships a real,
      non-stub `run()` meeting all four Appendix-A bars (real downstream,
      structured payload, synthesis-rendered, tests for success/failure/blocked).
      (HS-27-01 — `evidence-story-01.md`.)
- [x] A spoken-meeting e2e harness exists and runs against real endpoints: it
      synthesizes audio with `say`, transcribes it, runs the real plugin chain,
      persists artifacts, and captures at least one web screenshot showing a
      rendered artifact. Opt-in (skips cleanly when `say` / `.43` / Playwright
      absent). (HS-27-02 — `evidence-story-02.md`; screenshot in `evidence/`.)
- [ ] Every plugin flipped to real this phase is annotated ✅ in the RFC
      reality-status table; the rest stay ⚠️.
- [ ] No regressions: full sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green; the new e2e is excluded from the default sweep (own marker).
- [ ] `final-summary.md` records which plugins shipped, the e2e posture, and the
      handoff for the next plugin-rollout phase.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-27-01 | `action_owner_enforcer` — real run (ubiquity champion) | done | [story-01-action-owner-enforcer.md](./story-01-action-owner-enforcer.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-27-02 | Spoken-meeting e2e harness (`say` → pipeline → screenshots) | done | [story-02-spoken-meeting-e2e.md](./story-02-spoken-meeting-e2e.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-27-03 | `decision_capture` — decisions + open questions (net-new, ubiquitous) | done | [story-03-decision-capture.md](./story-03-decision-capture.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-27-04 | `requirements_extractor` — real run | done | [story-04-requirements-extractor.md](./story-04-requirements-extractor.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-27-05 | RFC reality-check refresh + phase exit | backlog | [story-05-phase-exit.md](./story-05-phase-exit.md) | — |

## Where we are

**In-progress, 4/5.** Scaffolded 2026-06-01; **HS-27-01 shipped same day** — the
real `action_owner_enforcer` plugin (the ubiquity champion) is live: LLM →
validated action items with owner/due **gap** flags → a checklist synthesis body,
verified live against `.43` Q6 (4 items extracted, gaps flagged). The Phase-16
pattern generalized cleanly to a non-diagram text artifact, and the registrar now
uses a `_REAL_PLUGINS` map (two real plugins, eleven stubs).

**HS-27-02 shipped:** the spoken e2e demonstrates `mermaid_architecture` +
`action_owner_enforcer` together on real endpoints (transcript + rendered SVG +
action-item checklist screenshot). It earned its keep immediately — it caught the
configured-provider wiring gap and the raw-markdown action-items rendering, both
now fixed.

**HS-27-03 shipped:** `decision_capture` is live on the balanced base chain with
a structured Decisions / Open-questions render; the spoken e2e now demonstrates
three real plugins together (diagram + action items + decisions).

**HS-27-04 shipped:** `requirements_extractor` flipped from stub to a real LLM
plugin — extracts requirements and classifies each as functional /
non-functional / constraint / acceptance, with a grouped-by-type structured
`/history` render. No routing ripple (it was already in the balanced + architect
base chains as a stub). Verified live on `.43` Q6 and via the spoken e2e, which
now demonstrates **four** real plugins together (diagram + action items +
decisions + requirements). **Four real plugins now, ten stubs.**

Pickup: **HS-27-05** (close the phase) — refresh the RFC reality-status table
(flip the four plugins shipped this phase to ✅) + write `final-summary.md`.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| LLM output quality varies per plugin (structured JSON vs free text) | medium | Strict prompt + post-hoc validation per plugin (reject malformed); reuse mermaid's parse-then-fallback shape. | Parse-failure > 40% on `.43` Q6 for a given plugin → demote to draft-only + document. |
| `say` TTS audio transcribes poorly / unrealistically | low | TTS is clean audio; Whisper handles it well. Use multiple `say` voices for multi-speaker realism. | If Whisper WER on `say` audio is too high to route intents, hand-author the transcript and feed it directly (skip TTS) for the assertion path; keep TTS for the demo screenshot. |
| The e2e is slow + non-deterministic → flaky in CI | high | Opt-in marker (excluded from default sweep, like `test_metal.py`); assert *structure* (artifact exists, valid block) not exact text; gate on endpoint/tool availability. | If it can't be made reliable even structurally, keep it as a `make demo` script rather than a pytest test. |
| Action-item plugin overlaps the existing action-item system | medium | Scope `action_owner_enforcer` as an *artifact* (ownership-gap report) over transcript content, not a mutation of the existing action-item review tables. | If it duplicates the existing extractor, pivot to enriching existing action items instead — separate decision. |

## Decisions made (this phase)

- 2026-06-01 — **Lead with ubiquity, not visual flash.** `action_owner_enforcer`
  (every meeting has action items) over `customer_signal_extractor` (niche). The
  visual demo is still carried by `mermaid_architecture` via the e2e. — author: Karol + agent.
- 2026-06-01 — **Real spoken e2e on real endpoints**, opt-in + structural
  assertions, doubling as a living demo (screenshots). — author: Karol + agent.
- 2026-06-01 — **Ship both plugins this phase:** `decision_capture` (HS-27-03)
  **and** `requirements_extractor` (HS-27-04). `decision_capture` first
  (ubiquity). — author: Karol.
- 2026-06-01 — **The e2e is a pytest test** (opt-in marker), not just a demo
  script. Script fallback only if it genuinely can't be made structurally
  reliable. — author: Karol.

## Decisions deferred

- (none open — see "Decisions made".)
