# HS-166-06 - The docs: the acli transport canon edit, Jira honesty

- **Project:** holdspeak
- **Phase:** 166
- **Status:** backlog
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

- [ ] Canon says acli; no doc claims a capability the code lacks (the drift guard green, read).
- [ ] Every excerpt in MCP_SIDECAR/the Project Rooms doc is from a real run (05's transcript) — cited by path.

## Test plan

- **Docs:** `uv run pytest -q tests/ -k "docs or drift or vocabulary"` (the guards), the mermaid-docs renderer if touched.
