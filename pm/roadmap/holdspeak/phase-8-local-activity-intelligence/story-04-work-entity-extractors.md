# HS-8-04 - Work entity extractors

- **Project:** holdspeak
- **Phase:** 8
- **Status:** done
- **Depends on:** HS-8-02
- **Unblocks:** useful activity summaries from raw URLs
- **Owner:** unassigned

## Problem

Raw URLs are not enough. HoldSpeak needs deterministic extractors that
convert visited URL/title metadata into work objects such as Jira
tickets, Miro boards, GitHub PRs/issues, docs, and generic domains.

## Scope

- **In:**
  - Jira ticket extractor (`PROJ-123`, issue URLs, title fallbacks).
  - Miro board extractor.
  - GitHub PR/issue extractor.
  - Linear issue extractor.
  - Confluence/Atlassian page extractor.
  - Google Docs/Drive and Notion page extractors.
  - Generic domain fallback.
  - Unit tests for URL/title patterns.
- **Out:**
  - Network enrichment.
  - OAuth/API integrations.
  - LLM classification.

## Acceptance Criteria

- [x] Known work URLs map to stable entity types/ids.
- [x] Jira keys are extracted from URLs and titles where safe.
- [x] Unknown URLs retain useful generic domain records.
- [x] Extractors are deterministic and tested.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_db.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-04.md](./evidence-story-04.md)
