# Phase 166 - Project Rooms: The Jira Parity (P7)

- **Project:** holdspeak
- **Status:** COMPLETE 7/7
- **Chartered:** 2026-09-03 off main `493253d8` (165 The MCP Family MERGED via PR #531 — the TENTH Project Rooms phase merged; this is the LAST §14 slice)
- **Canon:** docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §14 P7; SRS_PROJECT_INTERVIEW_WATCHES.md §6 PROV-001..012, §8.2 Jira issue parity, §15 V0-D, SETFLOW-005; SRS_PRODUCT_VALIDATION.md (Jira only with a real adapter); CONSTITUTION.md Article III (honest egress)

## The charter

P7's exit, verbatim: **Jira readiness is backed by live
discovery/search and the same no-duplicate Delta/action behavior,
never pushed fixtures alone.** The owner's word, twice: "Yes, I will
want Jira parity." and, on the transport (2026-09-03): "`acli` is
basically a prerequisite, and that's it" — and the focus: "being
able to support multiple accounts, against multiple targets
(*.atlassian.net)". So: the Atlassian CLI is to Jira exactly what
`gh` is to GitHub. No REST client, no token in HoldSpeak's custody,
no credential sheet — `acli jira auth login` is the provider-owned
interaction (PROV-005), HoldSpeak only reads back `acli jira auth
status`. The connection identity is **(site, email)** — acli's own
identity for `auth switch --site --email` — and one owner may hold
MANY of them (two sites, two accounts on one site); every Jira
connection row, discovery call, WatchSpec and test names its
connection ref. acli keeps ONE current account globally, so every
HoldSpeak call is `switch → command → status read-back` under one
process lock (the switch-and-verify law): a read that lands on the
wrong site is a typed error, never a silent wrong answer.

What exists already (recon, re-verified): the GitHub adapter shape
(services/github_provider.py: manifest/connection_status/discover/
validate_repo, typed PROV-009 codes, the runner seam), the generic
`watch_provider_connections` table (provider_id + external ref —
no schema change expected), the graduated Watch machinery (161/164:
test/baseline/evaluate_core/evaluate_due, source_revision dedup,
effect idem keys), the Jira semantic diff COMPLETE in
reaction_service.py (assigned/status/priority/due/resolved) and
the single gate at services/watch_sources.py:102-108 that today
raises `connector_snapshot_adapter_unavailable` for every
connector but gh. Jira is INVISIBLE in the provider list today —
not partial (SETFLOW-005 unmet); story 01 makes it appear, honest.

The chain: 01 the acli pack + the multi-account connection ledger
-> 02 discovery + search (projects, types, statuses, JQL; routes +
MCP) -> 03 the JiraWatchSource + the five watch.jira.* templates +
the interview candidates + the fetcher-seam rider -> 04 the web
face (provider-keyed wizard, many accounts × many sites, the
`<site>.atlassian.net` egress badge; shots) -> 05 the live walk
(OWNER VERDICT: real acli, real site(s), SETFLOW-005's transition
-> one Delta + one action, no duplicate) || 06 the docs (canon edit:
the acli transport) -> 07 the close.

OUT: Jira write effects (V0-E), a REST/API-token transport, Jira
Server/Data Center (acli is Cloud), the legacy `jira` go-CLI
enrichment pack (connector_packs/jira_cli.py — PARKED, untouched,
never deleted), the per-watch cadence write wire (stays ledgered).

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-166-01 | The acli pack + the connection ledger (many accounts × many sites; switch-and-verify) | done | [story-01-the-connection-ledger](./story-01-the-connection-ledger.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-166-02 | Discovery + search (projects, issue types, statuses, JQL; routes + MCP) | done | [story-02-discovery-and-search](./story-02-discovery-and-search.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-166-03 | The JiraWatchSource + templates + candidates (the gate graduates; the fetcher-seam rider) | done | [story-03-the-watch-source](./story-03-the-watch-source.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-166-04 | The web face (provider-keyed wizard; the site egress badge; shots) | done | [story-04-the-web-face](./story-04-the-web-face.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-166-05 | The live walk (real acli, real site(s), SETFLOW-005 — OWNER VERDICT) | done | [story-05-the-walk](./story-05-the-walk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-166-06 | The docs (the acli transport canon edit; Jira honesty; the dedicated docs story) | done | [story-06-the-docs](./story-06-the-docs.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-166-07 | The close (gates, riders, debts, final summary) | done | [story-07-the-close](./story-07-the-close.md) | [evidence-story-07](./evidence-story-07.md) |

## Where we are

**COMPLETE 7/7 — the P7 exit MET live; the SRS arc's V0 slices P0..P7
are all built.** Full suite 19 failed / 9201 passed / 61 skipped →
sweep zero unexplained (8 baseline, 9 real paid in-round incl. the
163 same-watermark law restored, 1 proven flake, 2 honest skips);
web 2358 zero branch-new; counsel RATIFY-W-C (one M + three S paid,
seven N ledgered). The owner's verdicts so far: the first face
BOUNCED ("walls of text"), the redesign RATIFIED ("HECK YES"). PR #532
opened on the local gates and MERGED on his word (2026-09-03, "yes
the PR is fine, I gave my word..., you know?") → main `31c072f5`.
See final-summary.md. Next: Phase 167 The Room in Use (his pick). After P7: the SRS arc's V0 is
COMPLETE; post-arc = Gate B partner feedback, MCP-008, the debt
ledger, the parked backlog.

## Recorded truths (the orchestrator's own acli runs, 2026-09-03)

acli 1.3.36-stable at /opt/homebrew/bin/acli; the owner authenticated
ONE account by OAuth on a practice site (an "HR"-type team-managed
project, key `KAN`, types Epic/Subtask/Task, three issues). Raw
captures: the session scratchpad `acli-recorded/` (re-recordable
at any time with the same commands).

- `auth status` connected: exit 0, `✓ Authenticated / Site: <host>
  / Email: <email> / Authentication Type: oauth`. Unauthenticated:
  exit 1, `✗ Error: unauthorized: use 'acli jira auth login' to
  authenticate`.
- `auth switch --site S --email E`: exit 0 `✓ Switched to account:
  S [E]`; unknown pair: exit 1 `✗ Error: account with email 'E' and
  site 'S' not found, ...` — the "acli does not know this account"
  signature, distinct from a read-back mismatch.
- The account registry is `~/.config/acli/jira_config.yaml`
  (`current_profile: <cloud_id>:<account_id>`, `profiles: [{site,
  cloud_id, account_id, display_name, email, auth_type}]`) — tokens
  are NOT in it; it is the non-secret enumeration of accounts acli
  knows. Read-only for HoldSpeak.
- `project list --json` returns the REST project objects (id, key,
  name, projectTypeKey, style, lead...; `issueTypes: null` in the
  list). `project view --key K --json` ENUMERATES `issueTypes`
  (name, id) — types are enumerable, not derived. Statuses are NOT
  in project view; `status.statusCategory` rides every issue, and
  JQL filters `statusCategory != Done` / `due <= 30d` work
  server-side (`--count` proves it).
- **THE SEARCH FIELD CAP** (the phase's real surprise):
  `workitem search --fields` ALLOWS only issuetype, key, assignee,
  priority, status (with statusCategory), summary, labels,
  reporter, creator, description; it REFUSES duedate, resolution,
  updated, created, project, components, fixVersions, issuelinks,
  subtasks, parent, statusCategory, `*all`, `*navigable` (exit 1,
  `✗ Error: fields '...' are not allowed`). `workitem view KEY
  --fields ... --json` allows EVERYTHING (duedate, resolution,
  resolutiondate, updated, created, statuscategorychangedate,
  components, labels, ...). `--paginate` and `--limit` both work;
  `--count` returns `✓ Number of work items in the search: N`.
  RULING for 03: the JiraWatchSource fetches the population by ONE
  JQL search (conditions that can be JQL — blocked status,
  due-within, resolved — are pushed INTO the JQL), then enriches
  each entity with ONE bounded `view --fields
  duedate,resolution,updated,statuscategorychangedate` call, capped
  by the watch's limit (N+1 calls per evaluation, N ≤ limit; the
  test result reports the call count). The diff's due_at/resolution
  come from view; never invented, never null-dressed.
- Bad JQL: exit 1 `✗ Error: failed to parse JQL query: <Jira's
  message>` → `query_invalid` with the message verbatim.

## Active risks

- **acli's global current account** is the phase's honesty problem:
  two HoldSpeak callers (the conductor's evaluate_due, a web
  discover) interleaving `switch` calls would read the wrong site.
  The lock + status read-back is the cure; counsel hunts exactly
  this (a fetch without a read-back is the third door reborn).
- **Issue types + status categories** may not be enumerable from
  acli (`project view --json` shape unverified). The fallback is
  derived-from-population, LABELED derived (PROV-007: partial stays
  usable, never dressed as complete) — mirrors §8.1's typed
  owner/repo fallback. Decided in 02 on the real CLI, recorded.
- **Recorded shapes lie until re-recorded**: acli's JSON field names
  come from the docs' examples, not from a run. Every recorded
  fixture carries a `recorded_from` note; 05 fails on the first
  mismatch and the adapter is fixed, not the fixture.
- **The rule grammar**: §8.2's "due soon/overdue", "entered a
  configured blocked state", "no activity for a duration" need
  comparisons the GitHub templates never used. Extend
  watch_validation in ONE place, tests beside it — never a Jira
  fork of the evaluator.
- **INHERITED LIE found by the 03 recon (paid in 03):** the condition
  matcher's `older_than`/`newer_than` return False unconditionally
  (watch_condition_matcher.py:183-190), so `watch.github.
  delivery_drift` has NEVER matched. §8.2's due-soon/overdue/
  inactive conditions are the same snapshot-level species; all six
  land in the ONE matcher against the transition's current entity.
- **THE WALK'S FINDINGS (05, round 1, live on the owner's site):**
  (1) FALSE BASELINE — finalize writes baseline_state=established
  with NO snapshot, so the first unattended tick "discovers" every
  issue and fires effects + a steward run from nothing (provider-
  agnostic; 164's GitHub walk counted that discovery tick as a
  useful run). Paid in 05: finalize baselines for real. (2) ZERO
  DOOR ITEMS from a jira transition — the act chain breaks
  somewhere between the jira observation and a project item; traced
  and paid in 05. (3) REPLAY minted a new run — the walk passed no
  watermark; re-run with the run's watermark. (4) Jira Cloud search
  is eventually consistent (~3-6 s after a transition) — the walk
  polls. (5) acli cannot set due dates; the due window is widened
  through the product's own rules route, recorded.
- Debts carried in: 165's eight counsel N + the legacy-side watch
  guard + the sidecar fetcher seam (both PAID here, 03) + per-watch
  cadence write wire + the scheduled-path trigger route; 164
  N-1..N-5; 163 S-4/N-1/N-3; 160 N-5/N-1/N-2; 158 S-1/N-1/N-3; 159
  seeding walls; 161 N-1.
