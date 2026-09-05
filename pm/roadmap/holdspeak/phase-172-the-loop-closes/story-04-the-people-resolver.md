# HS-172-04 — The People resolver

- **Project:** holdspeak
- **Phase:** 172
- **Status:** in-progress
- **Depends on:** HS-172-01
- **Unblocks:** HS-172-05
- **Owner:** unassigned

## Problem

Watch entities carry `assignee` (Jira, watch_sources.py:368) and
`reviewRequests` (GitHub, watch_sources.py:108) as plain strings (GitHub
logins, Jira display names). The People ledger has 5 relationships with
display names and owner_aliases (people_service.py:637). But there is NO
resolver that takes a Watch entity's assignee/reviewer string and maps
it to a People relationship. The existing
`resolve_relationship_by_owner` (people_service.py:707) resolves by
owner_alias only and has never been called from the Watch/Room path.
The arc says: "the People-to-Watch resolver (display name / alias to
assignee / reviewer; local, never egressed)."

## Scope

- In:
  - A resolver method on PeopleService that takes a Watch entity's
    assignee or reviewer string and returns the matching relationship
    (if any), using display name and owner_aliases for the match.
  - The match is case-insensitive, in-memory (the encrypted payloads
    are decrypted in-process), and NEVER egressed or persisted as a
    comparison (Article III).
  - The resolver is called from the 1:1 brief (HS-172-05) and from
    the People card in the Room (HS-172-07), not from the Watch
    evaluation path (reads are free; Article V.5).
  - Owner aliases gain a new affordance: linking a GitHub login or
    Jira display name as an alias maps that person across all Watches.
- Out:
  - Automatic alias linking from Watch entities (the owner must link
    aliases manually; the resolver only reads them).
  - Persisting the match result outside the encrypted People boundary.
  - Modifying Watch entity data (read-only from People's perspective).

## Acceptance criteria

- [ ] `resolve_relationship_by_watch_identity(identity_string)` on
      PeopleService returns the matching relationship when an
      owner_alias or display_name matches; returns None when no match
      (Article VI: honest at zero).
- [ ] The match is case-insensitive and in-memory; no alias string
      appears in plaintext outside the People store (Article III).
- [ ] The existing `link_owner_alias` and `unlink_owner_alias` work
      for GitHub logins and Jira display names (e.g., "karolswdev" or
      "Karol Sane").
- [ ] The resolver is called only from read paths (1:1 brief, People
      card); it never writes (Article V.5).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k people_resolver`
  - A linked alias matches a Watch entity's assignee string.
  - A linked alias matches a Watch entity's reviewer login.
  - Case-insensitive match succeeds.
  - No match returns None.
  - Archived relationships are excluded.
- Integration: n/a (the encrypted store is tested in unit tests).
- Manual: n/a.

## Notes / open questions

- The match strategy: exact string match on owner_aliases is the first
  pass. Fuzzy matching (e.g., "Karol" matching "karolswdev") is
  explicitly out of scope; the owner links the exact strings.
- Should the resolver also check display_name against Watch assignee
  strings? The existing `resolve_relationship_by_owner` only checks
  aliases. Including display_name broadens the match without requiring
  explicit alias linking.
