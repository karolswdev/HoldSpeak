# HS-174-07 — The third connector

- **Project:** holdspeak
- **Phase:** 174
- **Status:** in-progress
- **Depends on:** HS-174-06
- **Unblocks:** HS-174-08
- **Owner:** unassigned

## Problem

Once the owner decides on a third connector (story 06), the
implementation follows the same grammar as GitHub and Jira: a
WatchSource adapter, provider routes, Watch templates, the Door card,
and the Connections face row. The census priced a new CLI-backed
provider at approximately 730 lines (THE-TUESDAY-ARC.md:195) across
the adapter, WatchSource, templates, Door card, and provider routes.

## Scope

- In:
  - The WatchSource adapter for the chosen tool (the same shape as
    GitHubWatchSource at watch_sources.py:58-171 and JiraWatchSource at
    watch_sources.py:294-431): snapshot, entities, baseline/evaluate
    path.
  - Provider routes on the hub (`/api/providers/<tool>/...`) for
    connection status, discovery, and search.
  - Watch templates (`watch.<tool>.*`) for the common entity patterns
    (the templates chosen from the tool's entity types).
  - The Door card: the source row in DoorCore.tsx with the provider's
    default Watches (the same grammar as GITHUB_WATCH_DEFS and
    JIRA_WATCH_DEFS at DoorCore.tsx:28-37).
  - The Connections face row in Settings (one state, one verb; the
    switch-and-verify law from Phase 166).
  - MCP twins for the provider routes.
- Out:
  - Write effects through the connector (reads only in V0).
  - More than one new connector in this story.
  - A connector that requires REST/token (Article III).

## Acceptance criteria

- [ ] The WatchSource adapter passes the same test/baseline/evaluate
      path as GitHub and Jira (watch_sources.py gate).
- [ ] The Door card shows the source row with default Watches and the
      provider chip.
- [ ] The Connections face in Settings shows the tool with its
      connection state and one verb.
- [ ] Watch templates for the tool produce entities on a connected
      account.
- [ ] MCP twins for the provider routes pass parity tests (MCP-001).
- [ ] The switch-and-verify law holds: connection is verified before
      trusting (Article III; Phase 166's precedent).

## Test plan

- Unit: the WatchSource adapter snapshot returns entities for a seeded
  CLI response (the same pattern as the GitHub and Jira adapter tests).
- Unit: the Watch templates evaluate with expected entity shapes.
- Integration: the Door card renders with the provider's defaults; the
  Connections face shows the connection state.
- Manual: connect the tool on the owner's desk; create a Watch; verify
  entities appear in SOURCES.

## Notes / open questions

- If the chosen connector is `acli confluence`, the entity types are
  likely: pages (with last-modified, author, space, labels), spaces,
  and possibly blog posts. The WatchSource maps these to the same
  entity shape (id, title, url, updated_at, author, labels) that
  GitHub PRs and Jira issues use.
