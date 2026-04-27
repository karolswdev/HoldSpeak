# HS-8-07 - Project activity mapping rules

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-04, HS-8-05, HS-8-06
- **Unblocks:** project-aware activity context for plugins and handoffs
- **Owner:** unassigned

## Problem

The Local Attention Ledger can identify recent work objects, but users
need a simple way to teach HoldSpeak which activity belongs to which
project. This should be explicit, inspectable, and deterministic: "URLs
or entities matching this pattern belong to this Project KB."

Without this rule layer, plugin context is mostly global and downstream
features cannot reliably answer "what have I been doing for this
project?"

## Design

Add first-class project activity mapping rules. Each rule maps activity
records to a HoldSpeak project with a deterministic matcher and priority.

### Rule Fields

- `id`
- `project_id`
- `name`
- `enabled`
- `priority`
- `match_type`
- `pattern`
- `entity_type`
- `created_at`
- `updated_at`

### Match Types

- `domain`
  - Example: `jira.example.com` -> project `holdspeak`
  - Exact domain and subdomain match.
- `url_contains`
  - Example: `/browse/HS-` -> project `holdspeak`
  - Case-insensitive substring match against normalized URL.
- `title_contains`
  - Example: `HoldSpeak` -> project `holdspeak`
  - Case-insensitive substring match against title.
- `entity_type`
  - Example: `github_pull_request` -> project `platform`
  - Useful for broad project-wide routing.
- `entity_id_prefix`
  - Example: `jira_ticket` + `HS-` -> project `holdspeak`
  - Strong fit for Jira/Linear ticket prefixes.
- `github_repo`
  - Example: `openai/codex` -> project `codex`
  - Match against `entity_id` values shaped like `owner/repo#number`.
- `source_browser`
  - Example: `safari` -> project `research`
  - Low-priority fallback, disabled by default in UI unless user asks.

### Matching Semantics

- Rules are evaluated by descending `priority`, then oldest `created_at`.
- Disabled rules are ignored.
- The first matching rule assigns `project_id`.
- A preview endpoint shows matching activity records before applying.
- An apply endpoint backfills `activity_records.project_id`.
- Future imports run mapping during import after entity extraction.

### UI

Extend `/activity` with a "Project Rules" panel:

- project selector
- match type selector
- pattern input
- optional entity type selector
- priority input
- enabled toggle
- preview matches button
- apply/backfill button
- edit/delete rule actions

Keep the UI plain and operational. Users should be able to make rules
without writing YAML or regex.

## Scope

- **In:**
  - Local DB table for mapping rules.
  - Rule CRUD API.
  - Rule preview API.
  - Apply/backfill API.
  - Import-time project assignment.
  - `/activity` rule editor.
  - Tests for deterministic matching and precedence.
- **Out:**
  - Fuzzy/LLM project classification.
  - Automatic Project KB mutation.
  - External API calls.
  - Regex support in the first version.

## Acceptance Criteria

- [ ] User can create, edit, disable, and delete project activity rules.
- [ ] User can preview which records a rule will match before applying it.
- [ ] Activity records can be backfilled to projects.
- [ ] Future imports apply enabled mapping rules.
- [ ] Rules are deterministic and priority-ordered.
- [ ] Focused and full tests pass.

## Test Plan

- Unit tests for each match type.
- Unit tests for priority and disabled-rule behavior.
- Integration tests for rule CRUD/preview/apply APIs.
- Focused activity-intelligence sweep.
- Full non-Metal regression.
