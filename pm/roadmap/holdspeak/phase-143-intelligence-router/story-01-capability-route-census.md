# HSEGHS001HS104-143-01 - Capability and Route Census

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** none
- **Unblocks:** 143-02 through 143-14
- **Owner:** unassigned

## Problem

HoldSpeak currently resolves intelligence through Config pointers, ProfileRecord fields, Workbench/Recipe inheritance, MeetingIntelPlan, SpeechPlan, and several direct call sites. We need a generated, reviewable baseline before replacing any authority.

## Scope

### In

- Generate a complete capability, pointer, resolver, dispatch, fallback, sync, and owner-surface census.
- Map every physical generation path to InferenceRunner or name the bypass.
- Classify legacy workflow fallback labels that are not inference fallback.
- Publish migration ownership for every pointer family in assets/repository-census.md.

### Out

- No runtime behavior or schema change.
- No inferred capability compatibility.

## Acceptance criteria

- [x] Every production inference call site has one proposed capability ID and source owner.
- [x] Every mutable route pointer and resolver is listed with its migration story.
- [x] ProfileService transport-neutral authority bypass and profile sync path exposure are recorded.
- [x] One-path census proves current physical leaves and names every exception.
- [x] Counsel and owner audits are incorporated into the phase contracts.

## Test plan

- Exact AST/static inventories checked into three focused unit fixtures with
  synthetic fail-closed mutation cases.
- `uv run pytest -q tests/unit/test_phase143_*_census.py tests/unit/test_one_path_census.py tests/unit/test_api_surface.py`.
- `dw check holdspeak` and `git diff --check`.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.
