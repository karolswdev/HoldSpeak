# HS-166-06 - The docs: the acli transport canon edit, Jira honesty

- **Project:** holdspeak
- **Phase:** 166
- **Status:** in-progress
- **Depends on:** HS-166-03
- **Unblocks:** HS-166-07
- **Owner:** unassigned

## Problem

SRS_PROJECT_INTERVIEW_WATCHES.md §8.2 still says "allowlisted `jira
issue list`" — the go-CLI, not acli — and "Jira MUST be labeled
partially usable/pushed-snapshot-only until a provider implements
discovery plus `jira.issue.search`". The owner ratified acli; canon
must say so, and the public docs must not promote (the 165 law).

## Scope

- **In:** the canon edit (RATIFIED transport): §8.2 names acli,
  the (site, email) connection identity, the switch-and-verify
  law, and the derived-types fallback; SETFLOW-005 stays and is
  marked MET-by-166 only after 05. Public docs: the Project Rooms
  doc's provider section (GitHub → GitHub + Jira: prerequisite
  `acli`, the login command, many accounts), MCP_SIDECAR's provider
  tools (the four jira tools with real excerpts from 05's
  transcript), README's install prerequisites line. Honesty notes
  stated: acli global account + the lock; derived vs enumerated
  types; read-only (no V0-E). POSITIONING vocabulary check (the
  canonical "Watches (Project-scoped)" row); the doc-drift guard and
  the roadmap-vocabulary guard RUN, output read.
- **Out:** code.

## Acceptance criteria

- [x] Canon says acli; no doc claims a capability the code lacks (the drift guard green, read).
- [x] Every excerpt in MCP_SIDECAR/the Project Rooms doc is from a real run (05's transcript) — cited by path.

## Test plan

- **Docs:** `uv run pytest -q tests/ -k "docs or drift or vocabulary"` (the guards), the mermaid-docs renderer if touched.

## Trace record (orchestrator round, 2026-09-03)

- Canon edit RATIFIED: SRS_PROJECT_INTERVIEW_WATCHES §8.2 now names
  acli, the (site, email) identity, the switch-and-verify law,
  enumerated types vs observed statuses, the search field cap
  (N+1 calls), read-only (V0-E), keeps "A fixture MUST NOT be used
  to claim readiness", and carries the dated ratification line; V0-D
  names the transport. SETFLOW-005 untouched (the walk proves it).
- Public docs: README "Prerequisites for Project Rooms" (gh + acli,
  the login command, the one-line egress fact naming
  `<site>.atlassian.net`); NEW docs/PROJECT_ROOMS.md (121 lines,
  canonical names, every sentence backed by shipped code);
  MCP_SIDECAR provider section (4 GitHub + 6 Jira tools, the "Jira
  over acli" honesty block from live-recorded shapes); API_SURFACE
  (six Jira routes); CONNECTOR_DEVELOPMENT (the acli_jira pack);
  docs/README link + counts.
- Guards run and READ by the orchestrator: 38 passed (doc drift incl.
  the tool-count and roadmap-vocabulary guards, web vocabulary,
  product language); the roadmap-vocabulary grep over the touched
  public files is empty.
- Sequencing law: the tool-count claims include the MCP twin the
  04 build adds, so this story ships AFTER 04's commit — a docs
  commit must never claim a count the tree does not hold.
- Ledgered for the close: MCP_SIDECAR's per-family counts are stale
  for families untouched here (people 14→16, the desk grouping) —
  unguarded, outside this story.
- Deferred by design: the walk's real excerpts (05) are cited in the
  final summary, not retrofitted into public docs.
