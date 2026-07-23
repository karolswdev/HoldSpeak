# Phase 103 - Foundations & Borrowed Fire

**Status:** IN PROGRESS (2/6, 2026-07-22). Chartered from a four-agent
research pass the owner commissioned directly: three independent Opus
4.8 analysts examining `ViuGiaLai/researchmind` from different angles
(architecture/engineering, product/UX, feasibility/risk/licensing) to
find anything worth carrying over, plus one wholly independent Opus
4.8 skeptical audit of HoldSpeak's own claim to be a "Streamlined
Operating System" (the Desk). The owner's framing: mix the four
reports' findings into the additional stories, with a healthy dose of
skepticism against blind adoption and realism about single-owner
delivery timelines.

**Last updated:** 2026-07-22 (HS-103-02 shipped: the dash-in-glass guard
found 33 offenders, not the 3 named — all fixed).

## Why this phase exists

Phase 102 ("The Refit") closed out the six named per-surface
recompositions; this phase is different in kind — not owner-eyeballed
screenshot convictions, but a deliberately adversarial research
process: four agents, three studying an unrelated external repo for
transferable ideas and one turning the same scrutiny on HoldSpeak
itself with no knowledge of the other three. The synthesis (recorded
verbatim in "Where we are" below) rejected most of what the research
surfaced — most of researchmind is academic-domain and either
duplicates HoldSpeak or doesn't fit its architecture — and kept only
what survived skepticism: one durability bug the independent audit
proved live with file:line evidence, one guard-coverage gap the same
audit caught, and two small carry-overs that two of the three
researchmind agents converged on independently or that closed a named
"quiet trust" gap.

## Goal

Fix the desk's one load-bearing durability gap (session restoration),
close a voice-guard coverage hole the project's own canon should have
caught, and land two small, skepticism-tested carry-overs from the
external research pass (per-claim grounding verification, endpoint
health) — plus the harness fix needed to make the flagship
agent-steering feature provable by anyone, not just archaeology.

## Scope

- In: the five build stories (session restoration + reset-layout fix,
  voice guard on rendered glass, grounding verification, endpoint
  health, a composed steering-demo UAT recipe) and their evidence.
- Out: any other researchmind idea not named in the debate synthesis
  (academic-domain features, governance-as-data — parked, not
  committed, see Decisions deferred); redesigning the steering feature
  itself; cross-device/cross-browser state sync (the audit found
  localStorage-only persistence defensible for a local-first posture).

## Exit criteria (evidence required)

- [ ] All five build stories (HS-103-01 through HS-103-05) shipped
      with evidence.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.
- [ ] `cd web && npx tsc --noEmit -p . && npx vitest run && npm run
      build && npm run tokens:gate` green.
- [ ] The interior-canon + vocabulary guards (including HS-103-02's
      new dash-in-glass rule) green.
- [ ] HS-103-06 closeout: the owner's sitting verdict recorded, per
      Article IX.4.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-103-01 | Session restoration — the desk remembers it was open | done | [story-01-session-restoration](./story-01-session-restoration.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-103-02 | The voice guard reads the glass, not just the docs | done | [story-02-voice-guard-on-glass](./story-02-voice-guard-on-glass.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-103-03 | Grounding verification — does the artifact say what the source says | backlog | [story-03-grounding-verification](./story-03-grounding-verification.md) | — |
| HS-103-04 | Endpoint health — honest fallback across Runs-on destinations | backlog | [story-04-endpoint-health](./story-04-endpoint-health.md) | — |
| HS-103-05 | A provable steering demo — the flagship feature, on demand | backlog | [story-05-steering-demo-recipe](./story-05-steering-demo-recipe.md) | — |
| HS-103-06 | Closeout | backlog | [story-06-closeout](./story-06-closeout.md) | — |

## Where we are

**2026-07-22 — the research debate, synthesized.** Four Opus 4.8
agents ran in parallel: three dissecting `ViuGiaLai/researchmind`
(MIT-licensed, ~5-week-old solo academic-research-assistant repo — a
private Zotero + RAG chat + literature-review generator, architecture
near-match to HoldSpeak's Python/FastAPI backend, product domain
almost entirely unrelated), one auditing HoldSpeak's own Desk
independently, headed-equivalent, against a real staged instance, with
no knowledge of the other three.

Real convergence: the architecture and feasibility agents,
independently, both named the same ~50-line file
(`backend/chat/provider_resilience.py`, a circuit breaker + rolling
health score) as the one genuinely portable engineering idea — two
blind analysts agreeing without seeing each other's work. The product
agent's own top pick — per-claim citation-entailment verification —
was assessed as the strongest *product* carry-over: on-brand for
HoldSpeak's "quiet trust" positioning, closes a real gap (a citation
today asserts provenance, never support). The architecture agent's own
favorite idea (a versioned JSON "governance" policy engine) was
weighed and REJECTED for this phase: it solves a combinatorial
multi-task prompt-assembly problem researchmind has and HoldSpeak's
one-plugin-one-prompt architecture doesn't — parked as a backlog idea,
not committed.

The independent HoldSpeak audit rated the Desk 7/10 "OS-ness,"
confirming most of the roadmap's own self-assessment held up under
independent, hands-on, live-driven scrutiny (window manager, click
grammar, physics persistence, OS reflexes, mobile bottom sheets all
verified real, not vaporware) — but named one load-bearing gap with
file:line evidence: `SurfaceWindows.tsx:199` has no persist
middleware, so the desk remembers window GEOMETRY but not that a
window was OPEN; every reload is a blank desk, directly contradicting
the Constitution's own "the user's arrangement is sacred and persists"
claim. It also caught a `resetLayout()` leak (`store.ts:871`) and
three instances of the Constitution's own banned em-dash/reassurance
prose shipped live in the glass — a hole neither of the two existing
guards (`test_web_vocabulary_guard.py`: terms, not dashes;
`test_doc_drift_guard.py`: dashes, but docs-only) was positioned to
catch.

Six stories drafted: the durability fix (HS-103-01), the guard-gap fix
(HS-103-02), the two surviving researchmind carry-overs
(HS-103-03/04), a harness fix so the steering feature — which the
audit could not verify live, through no fault of the code, just a gap
in the seeded-desk UAT recipe — becomes provable by composing two
UAT-recipe primitives that already exist but have never been combined
(HS-103-05), and closeout (HS-103-06).

**2026-07-22 — HS-103-01 shipped.** `useSurfaceWindows` (open windows)
now persists to its own `hs.desk.open-windows` localStorage slot,
manual load/save functions matching `store.ts`'s existing pattern (no
new `zustand/persist` dependency) — chosen over folding into the
already-multi-writer `hs.desk.panels` blob (see the story's evidence
for the full reasoning). Reset Layout's stale-geometry half of the
audit finding was investigated with a targeted regression test and
confirmed live on a staged hub (headed Playwright, 1440 + 393): it
does not reproduce on the current codebase — `resetLayout()` already
clears an open window's geometry reactively — so no production change
was needed there; the regression test now pins the correct behavior.

**2026-07-22 — HS-103-02 shipped.** Extended `test_web_vocabulary_guard.py`
with a dash-in-prose rule (reusing its existing regex-scan machinery,
no JSX parser) that exempts numeric ranges (`3–4`, `F1–F12`) and
template-literal interpolation (a nested `x || "—"` placeholder). Fixed
a pre-existing false-positive in the SHARED scan helper along the way
(a bare `/*` inside a string, e.g. `audio/*`, was mistaken for a JSDoc
comment open and swallowed real code up to the next unrelated `*/`).
Running the finished guard once, before any fixes, surfaced **33
offending lines**, not the 3 the audit named — every one composed
without a dash (period/comma/colon/semicolon/parentheses per context)
and without the "on paper" reassurance idiom the three named lines
also carried. Confirmed live on a staged hub. The full pytest run
showed 7 failures; verified via `git stash` that all 7 are pre-existing
and unrelated to this story (1 a build-vs-test race from a manual
rebuild during the run, 6 a stale generated API-surface manifest/ledger).
Next: HS-103-03.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Session-restoration fix (HS-103-01) touches two window-state stores that may have drifted apart; a naive fix could paper over a deeper store-shape inconsistency | medium | Read both `SurfaceWindows.tsx` and `store.ts`'s persisted blobs fully before choosing a fix shape; prefer folding into one store if it's not disruptive | The fix requires reconciling two genuinely incompatible state shapes rather than adding persistence to one |
| Grounding verification (HS-103-03) ships a lexical entailment checker that false-flags legitimate paraphrase often enough to erode trust instead of building it | medium | Frame as a soft, quiet signal from day one (never a hard verdict); test the ambiguous/paraphrase case explicitly, not just the clean-supported/clean-unsupported cases | Live testing shows the flag firing on a majority of well-grounded claims |
| Endpoint health (HS-103-04) is scoped too broadly and turns into a routing rewrite instead of an additive health layer | low | Story explicitly scopes to 2 call sites and excludes mesh-relay redesign; full existing intel/dictation suite must stay green as a hard gate | The change requires touching `mesh_relay.py`'s actual routing decisions, not just recording health |
| The two UAT recipes (HS-103-05) don't compose as cleanly as their YAML shapes suggest | medium | Investigate first (see the story's own Notes/open-questions); report what's actually found rather than forcing a clean story if the real answer is messier | `includes:` and `seeds:` can't coexist in one recipe without harness changes |

## Decisions made (this phase)

- 2026-07-22 — commissioned a four-agent research pass (3 external + 1
  independent internal, all Opus 4.8) rather than a single agent or
  the owner reading researchmind directly — owner's explicit
  instruction, framed as wanting a debate to mix into the resulting
  stories.
- 2026-07-22 — rejected wholesale code adoption from researchmind
  (MIT license is compatible, but this project's greenfield/no-vendoring
  posture favors precise from-scratch reimplementation of small ideas
  over importing code from a different stack) — all four candidate
  stories that reference researchmind (03, 04) explicitly scope to
  "adapt the pattern," never "port the file."
- 2026-07-22 — phase scaffolded via `dw phase create` /
  `dw story create`; the generated story-ID prefixes came out garbled
  (`HSEGHS001HS104-103-0N` instead of the canonical `HS-103-0N`) and
  were corrected by hand across all six story files — a `dw` tooling
  bug worth reporting upstream, not a roadmap content issue.

## Decisions deferred

- Governance-as-data (versioned JSON prompt/policy assembly, the
  architecture research agent's top pick) — trigger: if HoldSpeak's
  plugin system ever grows genuinely combinatorial multi-task prompt
  assembly (it doesn't today — one plugin, one prompt, one intent) —
  default if never revisited: stays out, current per-plugin prompt
  authoring is adequate for the one-prompt-per-intent shape.
- Extending grounding verification (HS-103-03) to its second candidate
  surface (meeting artifacts OR Ask-AI, whichever isn't chosen first)
  — trigger: HS-103-03 ships and the pattern proves out — default if
  not revisited: single-surface coverage is enough for now.
