# HANDOVER — executing the Project Rooms SRS (PR #519)

Written 2026-08-31 by the orchestrator that vetted this suite, for the
agent who will implement it. Read this whole file before chartering
anything. The suite you are holding was vetted by three independent
reviews (canon / codebase truth / internal consistency — all
RATIFY-W-C, 20 findings fixed in `442c85e2`); its baseline claims are
trustworthy at file:line. Your job is to turn it into shipped phases
without burning that trust.

## 0. Read first, in this order

1. `docs/internal/project-rooms/README.md` — precedence, priorities,
   verification codes, **slice naming map**, baseline truth.
2. `SRS_SYSTEM.md` — the closed loop, AD-PRJ-001…010, SYS/NFR tables,
   the V0 acceptance scenario (§10) — this is the definition of done.
3. `SRS_PROJECT_INTERVIEW_WATCHES.md` — the front door of the product
   (interview → tested Watch); `WatchSpec@1` §7/§9.3 is normative here.
4. `SRS_DOMAIN_DRIVER.md` — schema, services, Delta, Steward, MCP.
5. `SRS_WEB_EXPERIENCE.md`, `SRS_PRODUCT_VALIDATION.md`.
6. GitHub issue #514 (vision), `docs/internal/CONSTITUTION.md`
   (supreme canon — the vetting added NFR-009/WEB-VIS-005/DOM-014/
   WEB-A11Y-009 citing Articles XI, III.2, V.2, IV.1; honor them in code,
   not just prose).

Precedence when docs conflict: SRS_SYSTEM decisions > the more
specific council SRS > #514 > existing behavior. A discovery that
invalidates a requirement updates the suite BEFORE or WITH the code.

## 1. Ground truth — verified anchors (do not re-derive, do not trust blindly either)

Every "existing X" below was verified during vetting. If main has
moved, re-verify the anchor before building on it.

| Existing thing | Where |
|---|---|
| `ProjectRepository`, `projects` table | `holdspeak/db/projects.py:22`, `holdspeak/db/schema.py:537` |
| `ProjectService` (CRUD/archive/meeting/resource) | `holdspeak/services/project_service.py:16` |
| `/api/projects` routes (+ since-last-meeting, summary) | `holdspeak/web/routes/projects.py:32-209` |
| `ProjectMemoryCore` (Timeline/Decisions/Search/Ask wings) | `web/src/pages/cores/ProjectMemoryCore.tsx` |
| Desk application registration (`open-project-memory`) | `web/src/desk/applications.ts:274` |
| `connector_watches` (NO cadence/freshness columns — cadence lives in `query_json.refresh_interval_minutes`; freshness inferred from `last_success_at`) | `holdspeak/db/schema.py:2220` |
| `ReactionService` (preview/baseline/refresh_due/events) | `holdspeak/services/reaction_service.py:167,308` |
| Live GitHub snapshot (`gh pr list`) | `holdspeak/services/watch_sources.py:43-98` |
| Semantic GitHub/Jira diffs | `holdspeak/services/reaction_service.py:118-166` |
| Watch MCP tools live in the **reactions** family (~94 tools/~20 families total, no `project.*`) | `holdspeak/mcp/families/reactions.py` |
| `ServiceEventLedger` | `holdspeak/services/service_event_ledger.py:22` |
| YOLO default posture | `holdspeak/operation_policy.py:35` |
| Conductor + Cadence + Workbench seams | `holdspeak/workbench_conductor.py:468`, `holdspeak/cadence/service.py:33`, `holdspeak/services/workbench_service.py:41` |

**Not yet existing (proposed, marked so in the SRS):**
`ProjectStewardService`, `WatchSpec@1` columns, setup sessions, review
cursors, the `project.*` MCP family, `GET /room`.

## 2. The chartering play (how slices become phases)

The suite defines domain slices **P0–P7** (SRS_DOMAIN_DRIVER §14, each
with entry/exit conditions) and product slices **V0-A…V0-E**
(SRS_PROJECT_INTERVIEW_WATCHES §15). V0-A/B/C land within P1–P4,
before Gate A. Recommended phase cut (one DW phase per line, stories
from the slice bullets, every exit condition becomes an acceptance
criterion with evidence):

1. **Phase: The Contract (P0)** — freeze qualified-ref/result/error
   contracts; characterization tests over today's Project
   service/routes/Web/MCP registration. Small, unglamorous,
   non-negotiable: it protects the graduation promise (AD-PRJ-004).
2. **Phase: The Room (P1)** — revisioned aggregate, `GET /room`,
   command idempotency; legacy Projects intact (DOM-011/012 are laws).
3. **Phase: The Interview (P1a / V0-A)** — durable setup session,
   native Watch suggestions, `connector_watches` → `WatchSpec@1`
   graduation (ADDITIVE columns; NFR-007), Blank escape hatch.
4. **Phase: The Delta (P2)** — sources/observations/reviews, the
   frozen review algorithm, honest degraded coverage (SYS-025).
5. **Phase: The GitHub Watch (P2a / V0-B)** — the live vertical slice
   riding `watch_sources.py`; exit is a stopwatch bar (under five
   prepared-fixture minutes) — build the rig like HS-156-07's.
6. **Phase: The Update Factory (P3)**, **The Steward's Hand (P4 —
   manual run_once first)**, **The Unattended Desk (P5 → Gate A)**,
   **The MCP Family (P6)**, **Jira (P7/V0-D — only if selected;
   fixtures NEVER count as readiness)**.

Number phases only after `git fetch` + checking origin/main README
"Current phase" + `ls pm/roadmap/holdspeak | tail` (the renumbering
scar is real). Phase 155 The Crew is chartered and may land first —
do not collide.

## 3. Laws of this repo that WILL bite you here

- **PMO rails**: stage → `dw contract new` → honest flip → commit.
  Evidence ships only with its story's done-flip (orphan-evidence
  gate). Never `--no-verify`.
- **The effect-ledger tombstone**: `holdspeak/kernel/effect_ledger.json`
  is a ZERO-ROW tombstone under an owner-ratified sunset. NEVER
  register new sites in it. A new bounded read-only probe joins
  `_EXCLUDED_CALLS` in `tests/unit/test_kernel_effect_fence.py`
  ("setup/diagnostic network probe"); a real effect is MIGRATED
  through the kernel (admission + receipt — NFR-009 makes this
  Project Rooms law). The 156 close violated this and it cost a
  fix commit (`ca70d5f6`). Steward effects and provider writes
  (V0-E) go through the kernel, full stop.
- **Egress badge at the point of decision** (WEB-VIS-005/DOM-014):
  every provider call and model invocation shows local/local+cloud/
  cloud. Reuse the existing badge species; no privacy novels.
- **One Schema**: additive-only declarative reconcile; never a
  positional INSERT (all 33 INSERTs are named; a fence test blocks
  recurrence). Test against a COPY of a real DB for reconcile work.
- **Web**: React+Vite desk-first; everything is a DeskPrimitive; no
  modals (edit in-world — the Popover role="dialog" scar); no prose
  in the UI; voice mic on every input (WEB-A11Y-009); library-first —
  extend `web/src/desk/surface/` patterns (barrel imports only, the
  ratchet fence never grows; see `contract.md` incl. the HS-156-08
  ChoiceCard object slots).
- **Beauty pass**: after every functional pass; shot sheets at 1440 +
  393 on the real hub; THE OWNER SEES SHOTS BEFORE MERGE — his shot
  verdict closes UI stories. Budget it into every Web phase.
- **Proof**: real metal for LLM features (the .43 llama.cpp server at
  192.168.1.43:8080 — sandboxed Bash cannot reach LAN; use rigs);
  drive the REAL coordinator with a fake engine factory (the
  fake-adoption scar); never run pytest un-isolated (`HOME=$(mktemp
  -d)` via a scratch script — the harness blocks inline `HOME=`);
  `PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright`
  for glass; `npm --prefix web run check` +
  `scripts/check_web_baseline.py --run` in every close.
- **CI truth**: main is red with an inherited baseline. The honest
  gate is the NAME-DIFF vs main's latest run
  (`gh run view <id> --log-failed | grep -oE '(FAILED|ERROR)
  tests/[^ ]+'`, `comm -23`). Zero branch-new, or fix at root cause.
  Never chain `gh pr merge` after a watch — read the conclusion JSON
  in its own step, then merge (merge commits, not squash).
- **Delegation**: all subagents are the opus-worker
  (claude-opus-4-6[1m]); workers run scoped tests only; the
  orchestrator runs the full suite and the gates. Counsel close per
  phase; fix M-findings in-round.

## 4. Hazards found during vetting (pre-paid lessons)

- `person:` vs `people:` **ref-prefix drift already exists**
  (`holdspeak/services/thread_service.py:311` vs
  `holdspeak/services/people_service.py:799`). Qualified refs (P0)
  must pick one grammar and fence it, or Delta will silently miss
  links.
- `context_json` is explicitly BANNED as the operating-model dumping
  ground (AD-PRJ-008). Typed schemas with lifecycle, every time.
- The MCP Watch tools you're graduating live in the `reactions`
  family module — plan the `project.*` family as thin drivers over
  `ProjectService` (AD-PRJ-006), don't fork authority into MCP.
- Workbench/Cadence are collaborators, NOT the Steward engine
  (AD-PRJ-005). `ProjectStewardService.run_due()` and
  `WatchService.evaluate_due()` are independent conductor failure
  boundaries (P5).
- Jira readiness = live discovery/search or it doesn't exist. Pushed
  fixtures asserting readiness is the exact dishonesty the suite
  forbids twice.

## 5. Open items that precede the first commit

1. **Merge #519** (the owner's call). It carries the vetted suite,
   this handover, and one CANON edit awaiting his ratification: the
   POSITIONING "Watches (Project-scoped)" canonical-name row.
2. Ask the owner: is **EverDriven** delivery riding GitHub or Jira?
   (Decides whether P7/V0-D enters the proving V0.)
3. Re-verify §1 anchors against main at charter time; update this
   file with the same commit if anything moved.

## 6. Definition of masterful

The V0 acceptance scenario (SRS_SYSTEM §10) run end-to-end on the
owner's real desk with a real Project, stopwatch-measured against
VAL-INT-002 (outcome → active tested Watch ≤ 5 min), every claim in
the drafted update carrying source refs, the Steward's one real action
receipted through the kernel, zero branch-new CI names, shots the
owner wants to look at, and not one line of parallel authority. The
desk proposes; the owner disposes.
