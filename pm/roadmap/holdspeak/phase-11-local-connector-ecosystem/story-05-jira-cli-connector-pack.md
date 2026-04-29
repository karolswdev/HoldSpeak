# HS-11-05 - Jira CLI connector pack

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-9-05, HS-11-01
- **Unblocks:** reusable Jira enrichment connector
- **Owner:** unassigned

## Problem

Jira CLI enrichment should be packaged as a reusable connector with
read-only command boundaries, fixture coverage, and explicit permission
metadata.

## Scope

- **In:**
  - Jira CLI connector manifest.
  - `jira` command policy allowlist.
  - Fixture parser for JSON/plain issue output.
  - Annotation output mapping.
  - Timeout and output-size default settings.
- **Out:**
  - Jira writes or transitions.
  - Token management.
  - Hidden network execution.

## Acceptance Criteria

- [ ] Connector manifest marks the connector as network-capable through local CLI.
- [ ] Only read-only `jira` commands are allowed.
- [ ] Fixture tests produce deterministic annotations.
- [ ] Command failures surface as connector run errors.
