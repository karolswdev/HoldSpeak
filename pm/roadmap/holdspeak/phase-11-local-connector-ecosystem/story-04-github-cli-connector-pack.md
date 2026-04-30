# HS-11-04 - GitHub CLI connector pack

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-9-04, HS-11-01
- **Unblocks:** reusable GitHub enrichment connector
- **Owner:** unassigned

## Problem

GitHub CLI enrichment should be packaged as a reusable connector with
clear read-only command policy, fixture coverage, and visible permission
metadata.

## Scope

- **In:**
  - GitHub CLI connector manifest.
  - `gh` command policy allowlist.
  - Fixture parser for `gh pr view` and `gh issue view` JSON.
  - Annotation output mapping.
  - Timeout and output-size default settings.
- **Out:**
  - GitHub writes.
  - Token management.
  - Hidden network execution.

## Acceptance Criteria

- [x] Connector manifest marks the connector as network-capable through local CLI.
- [x] Only read-only `gh` commands are allowed.
- [x] Fixture tests produce deterministic annotations.
- [x] Command failures surface as connector run errors.
