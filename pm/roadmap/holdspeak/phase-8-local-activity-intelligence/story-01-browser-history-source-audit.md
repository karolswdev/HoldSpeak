# HS-8-01 - Browser history source audit

- **Project:** holdspeak
- **Phase:** 8
- **Status:** done
- **Depends on:** HS-7-05
- **Unblocks:** safe browser-history ingestion
- **Owner:** unassigned

## Problem

Safari and Firefox browser history can provide valuable work context, but
reading browser databases is sensitive. Before implementing ingestion we
need a precise, local-first audit of source paths, schemas, lock behavior,
permissions, and privacy boundaries.

## Scope

- **In:**
  - Identify Safari history database locations and relevant tables/fields.
  - Identify Firefox profile discovery and `places.sqlite` tables/fields.
  - Define a safe read-only copy strategy for locked SQLite databases.
  - Document macOS permission expectations and Linux Firefox behavior.
  - Define the minimum data contract for history metadata ingestion.
  - Define default-enabled behavior and startup visibility requirements.
  - Produce evidence that confirms what can be inspected without page
    content scraping.
- **Out:**
  - Persistent ingestion tables.
  - UI controls.
  - Entity extraction beyond sample URL/title probes.
  - Reading cookies, cache, page content, or credentials.

## Acceptance Criteria

- [x] Safari source path/schema expectations are documented.
- [x] Firefox source path/profile/schema expectations are documented.
- [x] Safe copy/read strategy is documented.
- [x] Privacy boundaries are explicit.
- [x] Default-enabled startup behavior is explicit and visible.
- [x] HS-8-02 and HS-8-03 scopes are confirmed or adjusted from findings.

## Test Plan

- Docs/audit validation.
- Focused command evidence from local schema inspection where safe.
- `git diff --check`

## Evidence

- [evidence-story-01.md](./evidence-story-01.md)
