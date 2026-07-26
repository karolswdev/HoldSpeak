# HS-104-04 - PR receipts — paying the candidate-Y deferral

- **Project:** holdspeak
- **Phase:** 104
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-104-06, HS-104-07
- **Owner:** unassigned

## Provenance (the bar)

Owner-mandated ("I do want it in"), and — the council found — not new
scope at all: Phase 94's final summary explicitly parks "real GitHub
PR/CI receipt rows" as candidate-Y ("scheduled, not claimed"), and
Phase 86's belt already renders `gh` conclusions as read-only
station lights. This story pays that recorded deferral at its
minimal honest scope. AgentGlass's full PR cockpit (faceted filters,
threads, line comments, merge) is the named trap the council warned
against; none of it ships here.

## Problem

Steered agents produce PRs; the desk cannot see them where the work
lives. The delivery read model (`holdspeak/delivery/read_model.py`)
carries attempts and receipts but no PR rows, so the owner leaves
the glass for the browser exactly at the moment the work becomes
reviewable — and worse, nothing on the desk states *whether* a PR
belongs to a given attempt or merely resembles it.

## Recipe

1. **Configured sources only.** PR rows exist solely for repos
   registered in the delivery source registry
   (`holdspeak/delivery/registry.py`). No machine-wide discovery, no
   forge abstraction — GitHub via `gh`, the Phase-86 precedent.
2. **Collect into the read model.** Extend the single-flight
   collector (`holdspeak/delivery/collector.py`) with a PR pass: one
   batched `gh` call per source (the AgentGlass lesson: one GraphQL
   query, never a subprocess per PR) yielding rows of exactly:
   repo, number, title, head SHA, base SHA, state
   (draft/open/merged/closed), CI rollup (the conclusion, not the
   logs), author, observed-at, and a freshness/error field that
   renders honestly when the last poll failed (never a silently
   stale row).
3. **Attribution wears its epistemics.** Correlate each PR to Work
   attempts (`holdspeak/delivery/attempts.py`): head-SHA or exact
   branch match → `exact`; anything looser (branch-name heuristics)
   → `heuristic`, labeled on the row. A PR with neither shows
   unattributed. The council's riskiest-assumption warning verbatim:
   a PR matching a branch was not necessarily *produced by* that
   agent — the row must never claim more than the match proves.
4. **Poll economy, honest egress.** Refresh is manual (a verb on the
   surface) or by an explicitly enabled cadence in the source
   registry entry — never ambient. The surface wears the one
   `local+cloud` badge (no privacy novels).
5. **Render where delivery already lives.** Rows join the existing
   delivery surfaces (`web/src/desk/delivery.ts`,
   `DeliveryListSection.tsx`), needs-you-first ordering like the
   Phase-102 Outcomes treatment: open-with-failing-CI above
   open-green above draft above merged/closed (quiet treatment).
6. **"Review" means look, honestly.** Two verbs only: **See diff** —
   a read-only local diff in desk glass, computed from the mapped
   worktree the runtime already tracks (base...head; if the local
   checkout lacks the SHAs, say so and offer fetch as an explicit
   act, since fetch is egress); and **Open on GitHub** — the
   external URL. No comments, no review submission, no merge, no
   webhooks, no CI logs.

## Out of scope

- The merge actuator (parked in the charter; it arrives on the
  executor spine with stale-head refusal when it arrives).
- Any GitHub write. This story is read-only to its bones.
- Non-GitHub forges.

## Acceptance

- A real PR on a registered source renders with all fields, correct
  state, CI rollup, and its attribution label; a heuristic match and
  an unattributed PR are visibly distinct from an exact one.
- A dead-network poll yields a row honestly marked stale, not a
  silent freeze; a manual refresh recovers it.
- See-diff renders the real diff for locally present SHAs and the
  honest absence + explicit fetch offer otherwise.
- Egress census: the only network touch is the batched `gh` call in
  the collector pass; grep-pinned.

## Test plan

- **Unit:** row mapping from a captured `gh` payload fixture;
  attribution matrix (exact/heuristic/none); ordering.
- **Integration:** collector single-flight behavior with the PR pass
  added; the stale/error path with a failing `gh` stub.
- **Live (evidence):** a real PR of this repo on the staged desk,
  both viewports, screenshots read; the diff verb against real
  local SHAs.

## Chef's notes

- Reuse the Phase-86 `gh` conclusion plumbing before writing any new
  GitHub client code; the belt already learned the auth and
  rate-limit lessons.
- The freshness field is the difference between a receipt and a
  dashboard. A receipt says *when it observed*; a dashboard implies
  *now*. Print observed-at, always.
- Resist filters. Needs-you-first ordering replaces the entire
  AgentGlass facet bar for a single-owner desk.
