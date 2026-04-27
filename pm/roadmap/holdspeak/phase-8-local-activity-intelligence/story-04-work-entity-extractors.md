# HS-8-04 - Work entity extractors

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
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

- [ ] Known work URLs map to stable entity types/ids.
- [ ] Jira keys are extracted from URLs and titles where safe.
- [ ] Unknown URLs retain useful generic domain records.
- [ ] Extractors are deterministic and tested.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-8-02.
