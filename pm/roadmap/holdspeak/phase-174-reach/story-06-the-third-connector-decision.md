# HS-174-06 — The third connector decision

- **Project:** holdspeak
- **Phase:** 174
- **Status:** backlog
- **Depends on:** HS-174-01
- **Unblocks:** HS-174-07
- **Owner:** unassigned

## Problem

HoldSpeak has two connectors: GitHub (via `gh`) and Jira (via `acli`).
The Tuesday Arc names a third connector to bring another tool into
SOURCES. The connector must be CLI-backed (no REST API tokens, no
OAuth capture — Article III; the CLI holds the credentials, as `gh`
does for GitHub and `acli` does for Jira) and must follow the
switch-and-verify law from Jira parity (Phase 166: (site, email)
identity; verify the connection before trusting it).

This is a decision story: it evaluates the candidates, the owner
decides, and the implementation follows in story 07.

## Scope

- In:
  - Census of CLI-backed connector candidates on the owner's machine
    and the team's reality:
    - `acli confluence` — INSTALLED (`acli` at /opt/homebrew/bin/acli;
      the `confluence` subcommand is available; the owner's Atlassian
      account is already authenticated for Jira; Confluence Cloud
      commands are available).
    - `linear` — NOT INSTALLED; would require installing the Linear
      CLI; unknown whether the team uses Linear.
    - `glab` / `gitlab` — NOT INSTALLED; would require installing the
      GitLab CLI; unknown whether the team uses GitLab.
    - `az` (Azure DevOps) — NOT INSTALLED.
  - Evaluation criteria: (a) is the CLI installed? (b) does the team
    use this tool? (c) does the CLI support the switch-and-verify
    pattern (auth status, multiple accounts)? (d) what entities does
    the tool carry (pages, issues, boards) and which map to Watch
    entities?
  - The decision: the owner chooses ONE connector. The implementation
    story (07) follows.
- Out:
  - Implementation (story 07).
  - More than one new connector.
  - A connector that requires REST/token (Article III).

## Acceptance criteria

- [ ] The census of candidates is documented with installed/not, team
      usage, CLI capabilities, and entity mapping.
- [ ] The owner's decision is recorded with the rationale.
- [ ] The chosen connector meets the switch-and-verify law (the CLI
      has auth status + multi-account support or an honest fallback).

## Test plan

- Unit: n/a (decision story).
- Integration: n/a.
- Manual: the census is presented to the owner; his word.

## Notes / open questions

- The leading candidate is `acli confluence` because (a) the CLI is
  already installed, (b) the owner's Atlassian account is already
  authenticated, (c) `acli` already follows the switch-and-verify law
  for Jira (Phase 166), and (d) Confluence pages map naturally to Watch
  entities (pages with last-modified, author, space). The owner may
  prefer Linear if the team adopts it.
