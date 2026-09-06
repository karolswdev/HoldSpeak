# Phase 166 - The Jira Parity (P7): final summary

**Exit, verbatim:** Jira readiness is backed by live discovery/search
and the same no-duplicate Delta/action behavior, never pushed
fixtures alone. **MET, measured live** on the owner's real acli
(1.3.36, OAuth) and real site (project KAN), x2 at 1440 + 393 with
identical counts: a clean first tick after finalize; ONE declared
harness transition → 3 transitions → 2 effects → 1 steward run → ONE
door item; the Delta carrying the Jira evidence; an unchanged tick →
zero new anything; a second manual run at the same watermark created and
reconciled (the 163 law); Web and MCP reading the same revisions. THE OWNER'S VERDICTS:
the first face BOUNCED verbatim ("I absolutely hate the UX ... Walls
of text..."); the redesign on the library: "HECK YES, a BIG YES to
this."; the live walk gallery: his word given 2026-09-03 ("yes the PR is
fine, I gave my word..., you know?") — PR #532 MERGED, main `31c072f5`.

## The seven stories

1. **The connection ledger** - the acli pack (read verbs only) and
   JiraProviderAdapter; a connection is (site, email) — acli's own
   identity — under the switch-and-verify law (switch → command →
   auth-status read-back, one process lock); Jira in the provider
   list with honest readiness; acli's registry enumerated. Four
   catches paid, one found ONLY live (the URL-form identity split).
2. **Discovery + search** - projects paginated; issue types
   ENUMERATED; statuses OBSERVED and labeled so; JQL verbatim; the
   acli SEARCH FIELD CAP honored by bounded per-issue enrichment
   with calls reported; routes + MCP twins; `_with_account` the one
   helper. Proven live.
3. **The JiraWatchSource** - the single watch_sources gate
   graduated with ZERO evaluator fork (proven by a jira leg through
   the real WatchService and live); five watch.jira.* templates;
   candidates + clarify; the ONE matcher paid an inherited lie
   (older_than/newer_than never matched) with six honest
   snapshot-level comparisons; both 165 riders paid.
4. **The web face** - bounced by the owner, redesigned on the
   surface library (settled-design-face.md, mockups ratified),
   rebuilt through five orchestrator rounds (theater rig skips; a
   decoder whitelist dropping `calls`; raw wire ids on chips; an
   empty test that was a fixture lie). Sixteen shots read each round.
5. **The live walk** - the exit measured; FOUR inherited product
   defects paid with tests: the false baseline at finalize; the
   Delta service composed without project_service (create_item
   silently skipped); no risk rule for watch transitions; no
   watermark gate on the steward route. Plus three face defects
   only the real site could show (a day-early date, two label leaks).
6. **The docs** - canon says acli (§8.2 + V0-D); README
   prerequisites; the public Project Rooms guide; the Jira tools and
   routes documented; guards green.
7. **The close** - this document.

## Gates (real numbers)

- Full CI-style suite: **19 failed / 9201 passed / 61 skipped** (two halves, 12:53 + 8:03) -> sweep vs main's baseline
  at the branch base (23 names @ run 33697563134):
  8 baseline + 9 real paid in-round (the effect census, the thread
  tool gate census, the command pin, the connector set, the API
  surface regenerated, and the 163 steward glass ×2 — the walk's
  route-level watermark dedup broke §9.3's same-watermark law and
  was reverted; the walk now measures the 163 contract) + 1 proven
  flake + 2 honest skips (the live walk under an isolated HOME).
  Zero unexplained. On the settled tree: candidates 9 passed, the
  live walk 2 passed, the flake proof x2 green.
- Web: baseline **2358 passed, zero branch-new** (one vitest flake seen
  once between captures, clean on re-run).
- Counsel: **RATIFY-WITH-CONDITIONS** — ONE M + three S, all paid
  in-round: the palette pin (37 → 44, renamed honestly); the Workbench
  automation read model calling a working Jira adapter "unavailable"
  on both the route and its web twin (the graduated gate's leftover
  lie); the auth-status read-back filling a missing Site/Email from
  expectations (now an honest non-match). Seven N ledgered.

## Debts

- New, carried: the second-target proof (the owner holds ONE acli
  account; two sites/accounts were designed, tested with fixtures,
  never walked live); the population toggles are visual state on
  the face (the controller carries the scope; the toggles bind in a
  later pass); MCP_SIDECAR's per-family counts stale for untouched
  families (people 14→16, the desk grouping) — unguarded; the door
  title's transition choice (status_changed vs resolved) is
  first-match within one evaluation — human either way, not pinned;
  per-issue enrichment costs N+1 acli calls per evaluation (bounded
  by the watch limit, reported, not yet receipted per run); Jira
  Cloud search eventual consistency handled by the walk's polling,
  not by the evaluator; the two cadence-repair commits (dw's row
  flip gotcha, now in memory).
- Counsel's N: the acli lock is per-process (the MCP sidecar holds
  its own — a V1 file lock or one runner process); diff_snapshots'
  else-branch assumes jira for any non-gh connector (a third
  connector needs an elif + refusal); the enrichment `except
  Exception` is broad (best-effort by design; narrow it);
  find_run_by_watermark scans the last 100 runs (the unique
  active-run index is the real guard); the transcript's
  counts_match is asserted by the two independent runs, not
  computed across widths; the ActivationReview jira entity label
  has no dedicated unit test; MCP_SIDECAR's counts verified clean.
- Carried from before (re-listed): 165's eight counsel N (minus the
  two riders paid here) + per-watch cadence write wire + the
  scheduled-path trigger route; 164 N-1..N-5; 163 S-4/N-1/N-3; 160
  N-5/N-1/N-2; 158 S-1/N-1/N-3; 159 seeding walls; 161 N-1.

## The arc

P7 was the LAST §14 slice. With it the SRS arc's V0 is COMPLETE:
P0..P7 merged. Post-arc: Gate B partner feedback, MCP-008 remote
(deferred by design), the debt ledger, the parked backlog (155 The
Crew, the model-era collapse).
