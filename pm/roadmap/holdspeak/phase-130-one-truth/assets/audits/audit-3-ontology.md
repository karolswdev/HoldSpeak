# Audit 3 — Sync / ontology / constitution / roadmap-overlap (issue #450), verified 2026-08-08

**1. Workbench sync declared but incomplete — CONFIRMED (worse than stated)**
`holdspeak/services/sync_service.py:15-21` — `workbench` in SYNC_KINDS. :61-66 — `_MERGEABLE["workbenches"]` exists (name, recipe_id, profile_id, schedule, schedule_enabled, item_order). :69-81 — `_BUCKET_KIND` has no workbenches entry. `push()` computes `known_buckets = set(_BUCKET_KIND)` (:696), so a workbenches bucket is never validated or merged and cannot satisfy the "at least one known bucket" check (:698); the merge map is dead code. `pull()` (:552-687) returns 18 buckets, no workbenches. `resolver_profile_id` is a real column (db/schema.py:1163) absent from the merge map.

**2. mir_profile vs plugin_profile — CONFIRMED (nuance: recorded debt)**
Both at config/meeting.py:68 and :79, both default "balanced". Runtime reads `mir_profile`: web_runtime.py:182, intel_queue.py:272, meeting_session/session.py:116,185,721. Doctor reports only `plugin_profile`: commands/doctor.py:1098,1120,1125,1129,1138. Only other consumer of plugin_profile is its own validator (meeting.py:160-163). Settings UI exposes both as separate dials (SettingsCore.tsx:673,675). Nuance: the split was a deliberate recorded decision (phase-2-multi-intent-routing/story-09-config-flags.md:42,69 — "They could converge in a future cleanup") — acknowledged debt, but doctor validating a field the runtime ignores is true today.

**3. "Receipt" overloaded — CONFIRMED**
docs/product-language.json:125-129 defines Receipt as "A durable account of what ran, where, why, and with what outcome." kernel/journal.py:258-276 (`add_receipt`/`receipt`) follows exactly that: one immutable row per operation_id, insert-once. `DecisionReceiptService` stores mutable governing content — rationale/alternatives/owner/review_date in `_EDITABLE_FIELDS` (decision_receipt_service.py:14-16), `update_receipt()` with revision trail (:132-181), `supersede()` flipping lifecycle (:263-301), `due_for_review()` (:338). A Decision record with an audit log, not what-ran evidence. The sync layer compounds it with four decision_receipt* sync kinds.

**4. Two daily briefs — CONFIRMED, overlap narrower than claimed**
cadence/brief.py:36-46 (`build_brief`) reads ONE source — cadence loops — pure/in-memory, not persisted. monday_brief_service.py:82-141 reads four sources (pipeline_events :180,:241; FollowThroughService.board() :311-313; pending proposals/approvals :395-406), persists, idempotent per day. Real overlap: cadence loops reach both; output shape rhymes (both have a `BriefItem` dataclass of the same name). Monday Brief is a strict superset only on the loops lane.

**5. Two obligations surfaces — DRIFTED-BUT-REAL (strengthened)**
follow_through_service.py:59-149 merges both and de-duplicates (a cadence loop with source_type=="meeting_action" enriches the action card, :78-86,:118-120). CadenceCore.tsx:30-183 presents an independent list from /api/cadence/loops under a section labeled "Now" (:76) with snooze/close/kill. Drift: the other surface is not only CadenceCore — FollowThroughView.tsx:37-40 renders the four-lane board also with a "Now" lane. Two web surfaces both headed "Now" over an overlapping loop set.

**6. Delivery AgentProfile is not an Agent — CONFIRMED**
delivery/factory_launch.py:213-222: AgentProfileStore = argv templates ("a fixed executable from KNOWN_EXECUTABLES, fixed safe-token args, allow-listed option slots"). product-language.json:65-70 defines Agent as "Saved reusable behavior…"; :71-76 defines coder_session as "A live Claude or Codex process, never a saved agent." DeliveryBoard.tsx:211-213 labels the launch-template picker AGENT/Agent (also :90).

**7. Workbench hard-bound to recipes — CONFIRMED**
db/schema.py:1159-1171: workbenches has recipe_id/profile_id/resolver_profile_id — no capability_ref. Comment :1157: "one agent, one target, one schedule, N items." workbench_conductor.py:447-450 hard-fails without a recipe; run path is recipe-shaped (:475-486). Sequences and Workflows exist as first-class primitives (schema.py:970 chains, :980 workflows; sync kinds chain/workflow; product-language capability category) — a Workbench can host neither.

## Constitution check (docs/internal/CONSTITUTION.md)

Five of six cited articles support the mandate; Article IX does not — it constrains how the phase must PROVE, not why it should exist.

- Article I (:19-28) — supports the duplication claims: "Features do not own surfaces. The OS owns surfaces… and features plug into them."
- Article II (:30-38) — strongest single support: "New capability means a new primitive or a new affordance on one, never a new world."
- Article V (:56-65) — "Every attempt leaves a receipt: who, what, where, outcome" — the constitutional definition of Receipt matches the kernel journal, not DecisionReceiptService.
- Article VII (:81-88) — "Labels state what, in the fewest words" — supporting citation only.
- Article IX (:97-105) — "Nothing is done because its code merged. It is done when it ran." A bar on evidence, cited out of role as a mandate basis; applies to how any resulting phase closes.
- Article XI (:120-140) — "Every consequential operation… is admitted once through the kernel before it acts, and ends in a terminal receipt." Directly mandates the Ask/Workbench/chat admission fix and fixes "receipt" as kernel vocabulary — the sharpest constitutional argument in the issue.

## Roadmap overlap

- **Phase 112 "Enough" is CLOSED** (6/6 SHIPPED AND WALKED, 2026-08-02). Its one-dial story (story-01-one-dial.md:11-19) set "the InferenceTarget (the profiles table) is the ONLY place an endpoint or model lives" — precedent, not collision. Its survey already enumerated the three-pointer problem; `mir_profile`/`plugin_profile` are routing profiles, outside 112's closed scope. meeting.py:50-58 carries "DEAD legacy fallbacks (HS-112-01)" comments — 112's cleanup landed and stopped short of the routing dials.
- **Phases 125-129 all closed.** Claims 3/4/5 target code shipped in 125 (FollowThrough), 126 (Monday Brief), 127 (Decision Receipt) — three consecutive phases built in one session, never reconciled sideways. Likely root cause.
- **Candidate Z — The Inherited Ledger** (BACKLOG.md:64, :242-258), filed-but-unruled, owner ruling pending at the 129 sitting: 96 backend failures spanning decision records, live bus, sync/primitive contracts, guards. The ledger includes `tests/unit/test_primitive_contract.py::TestKindSetCannotDrift::test_schemas_cover_exactly_sync_kinds` and `tests/unit/test_web_routes_sync.py` pull/push tests — plausibly the same defect as the workbench-sync gap (claim 1). Candidate Z and #450 Wave 1 partly intersect.
- **Candidate AA — Workbench remainders** (BACKLOG.md:726-737) — desk-window/drag/icon items only; does not cover capability_ref generalization.
- **No BACKLOG entry for placement/settings consolidation** — nothing to collide with, but no prior owner ruling to lean on either.
