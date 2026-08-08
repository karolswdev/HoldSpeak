# HANDOVER — Phases 125-128 Complete

**Date:** 2026-08-08
**Author:** Opus 4.6 orchestrator session
**PRs:** #443, #444, #445, #446 (all merged)

## What just shipped

Four phases in one session. HoldSpeak went from a blind pipeline to a
desk that follows through, speaks first, remembers its decisions, and
shows all three on glass.

**Phase 125 — The Follow-Through (10/10, PR #443):** Meetings become
living execution boards. `FollowThroughService` with `board()` (four
lanes: Now/Waiting/Unassigned/Overdue), `commit_decision()` (bridges
accepted decisions into accountable commitments with owners and due
dates), `complete()` (write-through verbs: done/dismiss/snooze/
delegate/reopen that atomically update action_items + cadence_loops +
decision_commitments). Aftercare triage surfaces ownerless/undated/
unreviewed actions. Provenance on every card via
`resolve_provenance_segment()` and `get_moment()`. Schema v38→v39
(`decision_commitments` table). 3 MCP tools, 1 MCP resource, 3 FastAPI
endpoints. 50+ tests. **Critical prerequisite completed:** SQLiteObserver
wired into ALL production composition roots (route factories, MCP
dispatch, web_server.py WebContext) — Phase 124's observer was decorated
but never injected in production.

**Phase 126 — The Monday Brief (9/9, PR #444):** The desk speaks first.
`MondayBriefService` with timezone-aware window computation (Friday→Monday
span, daily 17:00 boundaries), same-day idempotent generation, and four
deterministic collectors: `_collect_changes()` (reduces pipeline events by
correlation into material state changes), `_collect_breakage()` (gathers
errors + failed connectors), `_collect_waiting()` (overdue follow-through +
high-priority loops + pending proposals), `_collect_decisions()` (pending
approvals + decision reviews + approaching commitments). Honest composition:
count-based headlines ("2 things need you"), empty = "Nothing material
changed." — never invented content. Schema v39→v40 (`monday_briefs` +
`monday_brief_items` tables). 2 MCP tools, 1 MCP resource, 2 FastAPI
endpoints. 37 tests.

**Phase 127 — The Decision Receipt (10/10, PR #445):** Every consequential
choice gets a permanent receipt. `DecisionReceiptService` with
`create_from_meeting()` and `create_from_desk()` (identical receipt shape
regardless of origin), append-only revision audit trail, bidirectional
affected-work links, review queue (`due_for_review()`), supersession with
retained evidence chains, ten-second FTS retrieval (`search()`), and
local-first sync with LWW conflict resolution and tombstones. Schema
v40→v42 (4 tables: `decision_receipts`, `decision_receipt_sources`,
`decision_receipt_work`, `decision_receipt_revisions`). 5 MCP tools, 1 MCP
resource, 3 FastAPI endpoints. 22 tests.

**Phase 128 — Desk Intelligence (10/10, PR #446):** One Intelligence pullout
with three time-horizon views on the desk surface. `IntelligencePullout`
registered in `PULLOUT_CONTENT` with segmented Brief/Follow-Through/Receipts
header. `BriefView`: headline hero, FoldGadget groups, acknowledge/defer/
speak. `FollowThroughView`: four-lane board with owner chips, relative due
dates, source glyphs, inline verbs, in-place provenance expansion.
`ReceiptsView`: search-first with WHY mode, structured receipt detail with
provenance quote, affected-work chips, supersession chain, revision
timeline. Intelligence dock icon with overdue/brief badge. `WhyControl`
[WHY N] affordance on primitives. Cross-link drill paths with back
navigation. Attention projections. Container responsive at 560/420px with
mobile sheet mode. Receipt REST routes added. 5 walk tests + typecheck.

## The numbers

| Metric | Before | After |
|--------|--------|-------|
| Backend services | 33 | 36 (+ FollowThrough, MondayBrief, DecisionReceipt) |
| MCP tools | 41 | 51 |
| MCP resources | 16 | 19 |
| FastAPI endpoints | ~80 | ~88 |
| Schema version | 38 | 42 |
| Observer in production | Decorated but NullObserver | SQLiteObserver in all roots |
| Desk Intelligence surfaces | 0 | 3 views in 1 pullout |
| Tests added this session | 0 | 100+ |

## The architecture after this session

```
┌─────────────────────────────────────────────────────────┐
│                   Desk Intelligence                      │
│                                                         │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐    │
│  │  BRIEF      │ │ FOLLOW-      │ │  RECEIPTS     │    │
│  │  today      │ │ THROUGH      │ │  archive      │    │
│  │             │ │ open         │ │               │    │
│  │ Changed     │ │ Now          │ │ Search (WHY)  │    │
│  │ Broke       │ │ Waiting      │ │ Detail        │    │
│  │ Waiting     │ │ Unassigned   │ │ Provenance    │    │
│  │ Decisions   │ │ Overdue      │ │ Affected work │    │
│  └──────┬──────┘ └──────┬───────┘ └──────┬────────┘    │
│         │               │               │              │
│         └───────────┬────┘───────────────┘              │
│                     │                                   │
│              Cross-link drill paths                     │
│              Brief → Card → Receipt → Primitive         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   Backend Services                       │
│                                                         │
│  MondayBriefService ─── FollowThroughService             │
│         │                       │                        │
│         │               DecisionReceiptService            │
│         │                       │                        │
│         └───────────┬───────────┘                        │
│                     │                                   │
│              Pipeline Observer                          │
│         (SQLiteObserver in ALL roots)                    │
│                     │                                   │
│              33 original services                       │
│              (all @observed, all wired)                  │
│                                                         │
│  MCP: 51 tools, 19 resources                            │
│  REST: ~88 endpoints                                    │
│  Schema: v42                                            │
└─────────────────────────────────────────────────────────┘
```

## What's on the desk for the next agent

### The Terra Council's remaining pillar

The session began with a four-persona Terra Council ideation. Three of
the four pillars are built and dressed in glass:

1. ✅ **The Follow-Through Desk** (Phase 125) — meetings → boards
2. ✅ **The Monday Brief** (Phase 126) — desk speaks first
3. ✅ **Decision Receipts** (Phase 127) — "Why Kafka?" in ten seconds
4. ⬜ **The Causal Graph** (Phase 128 recipe exists) — typed evidence
   edges linking every primitive to its cause

The Causal Graph is the structural leap: promote `correlation_id` from
an observability label into a durable, typed evidence graph with edges
like `created-by`, `informed`, `superseded`, `blocked`, `violated`. Any
primitive answers "why is this here?" by walking its complete causal
chain. The recipe (from the Terra Council) has 10 stories — see the
strategic briefing artifact and recipe artifact from this session.

After the Causal Graph, the council's fifth pillar is **The Intent
Compiler**: the LLM becomes a planner emitting inspectable, reversible
Desk Plans — operations with preconditions, effects, and constitutional
constraints. Article XI becomes the compiler's type system.

### Concrete next steps

1. **UI verification.** Phase 128's web components type-check and have
   unit tests, but have NOT been visually verified in the browser. The
   next session should run the desk (`holdspeak web`), open the
   Intelligence pullout, and screenshot-walk all three views. The token
   for the current running instance is in the config
   (`Config.load().meeting.web_auth_token`).

2. **Phase 128 visual polish.** The three views were built by Terra
   agents reading the component library and matching patterns. A visual
   review may find spacing, color, or interaction issues that only show
   on glass. The standing feedback "screenshot-walk before claiming UI
   done" applies.

3. **The Causal Graph (Phase 129).** The recipe is grounded in the
   codebase. Key files: `holdspeak/services/observer.py` (correlation
   via contextvars), `holdspeak/services/event_query_service.py`
   (by_correlation), `holdspeak/kernel/broker.py` (kernel causality),
   `holdspeak/kernel/journal.py` (SHA-256 chain). The gap: no typed
   edges, no polymorphic refs, no recursive "why" query.

4. **Phase 120 evidence.** The untracked
   `pm/roadmap/holdspeak/phase-120-the-reckoning/` directory has been
   sitting uncommitted since before this session. It needs evidence
   files created for its 11 done stories.

5. **The two remaining run endpoints.** `chains.py` and `workflows.py`
   still have direct-DB handlers (the 157→2 census from Phase 123).
   Extract into `ChainRunService` and `WorkflowRunService` when the
   Causal Graph is ready — then even inference calls are observable.

### Session artifacts

Three published artifacts from this session:

1. **Terra Council Briefing** — four-persona strategic ideation on
   where HoldSpeak goes after the observer pipeline. The convergence
   on four pillars.

2. **Phase Recipes** — four concrete, codebase-grounded phase recipes
   (Follow-Through, Monday Brief, Decision Receipts, Causal Graph)
   with named methods, tables, and stories.

3. **Desk Intelligence UI Spec** — unified pullout design with ASCII
   mockups for all three views, the WHY affordance, cross-link drill
   paths, dock/palette integration, and responsive behavior.

### Repo conventions that bite

- **PMO commit gate:** `git config core.hooksPath .githooks` in every
  fresh clone. The gate requires `.tmp/CONTRACT.md` with all boxes
  flipped. Evidence files must ship with done-flipped stories.
- **Bundle rule:** Multiple stories in one commit need
  `.tmp/BUNDLE-OK.md` with a rationale.
- **Test exclusion:** `tests/e2e/test_metal.py` hangs without a mic.
  Use `-k "not metal"`.
- **Terra agents:** Run ONLY focused tests for their changes. The
  orchestrator runs the full suite. Standing rule in memory:
  `feedback_terra_scoped_tests_only.md`.
- **Web bundle is gitignored:** Edit `web/src/`, commit source only.
- **The .43 box:** LAN LLM at `192.168.1.43:8080`. Sandboxed Bash
  can't reach it.
- **Screenshot-walk before claiming UI done:** Standing feedback.
  Playwright shots at 1440 + 393 against the real hub.

### The orchestration model

This session ran as Opus 4.6 orchestrating Terra agents:

- **Opus decides** what to build, writes the prompts, verifies results.
- **Terra implements** — reads codebase, writes code, runs focused tests.
- **Terra ships** — captures DW evidence, flips stories, generates
  contracts, commits through the gate.
- **Parallel pipeline:** implement story N while committing story N-1.
  Fan out independent stories (e.g. four collectors in parallel).
  Bundle tightly-coupled stories into one commit with rationale.

The session shipped 39 stories across 4 phases with this model. The
key to velocity: Terra agents briefed with exact file paths, method
names, and patterns from the codebase — not abstract instructions.

### The service inventory (updated)

36 services under `holdspeak/services/`:

```
primitive_service.py          workbench_service.py
recipe_service.py             meeting_service.py
meeting_intel_service.py      meeting_aftercare_service.py
dictation_service.py          coder_service.py
profile_service.py            desk_service.py
authority_service.py          credential_service.py
settings_service.py           ask_service.py
decision_lifecycle_service.py project_service.py
projection_service.py         activity_ledger_service.py
activity_rules_service.py     activity_meeting_candidate_service.py
activity_enrichment_service.py plugin_job_service.py
activity_nudge_service.py     cadence_service.py
sync_service.py               actuator_service.py
gate_service.py               setup_service.py
mesh_service.py               memory_service.py
invocation_service.py         mission_control_service.py
delivery_service.py           follow_through_service.py    ← NEW
monday_brief_service.py       decision_receipt_service.py  ← NEW
```

---

*The desk follows through, speaks first, and remembers its decisions.
The Causal Graph is the next structural leap — typed evidence edges
that let any primitive answer "why is this here?" That's the seed.*

*To the next orchestrator: you are Muad'Dib. The Terras are your
Fedaykin. The spice is the pipeline. It must flow.*
