# HS-132-10 — One meetings placement dial

- **Project:** holdspeak
- **Phase:** 132
- **Status:** backlog
- **Depends on:** HS-132-09
- **Unblocks:** HS-132-14
- **Owner:** unassigned

## Problem

Issue #450 defect 4's UI half survives. The backend has one placement
authority with explicit precedence and provenance
(`resolve_meeting_placement`, `holdspeak/intel/providers.py:653-713`, with
`placement_source`/`placement_reason`/`PLACEMENT_PROVIDER_OVERRIDDEN` at
:606-608,697), but the web still renders two independent dials: a Provider
cycle over `['meeting','intel_provider']` (`SettingsCore.tsx:636`,
options local/cloud) and a separate "Runs on > Meetings" destination pointer
over `['meeting','intel_profile_id']` (`settingsModels.tsx:414,269-289`).
No web consumer of `placement_source`/`placement_reason` exists. A user sets
Provider = LOCAL and it silently does nothing because an adopted destination
set in a different module wins; the control lies about what decides
placement.

## Scope

### In

- One user-facing meetings placement control. The Provider cycle is retired
  as an independent dial (demoted under the Runs-on pointer or disabled with
  the override named when a destination is adopted — settled at design).
- The settings API surfaces `placement_source` and `placement_reason`; the
  UI shows the effective placement and, when provider intent is overridden,
  a visible "PROVIDER SELECTION IGNORED — <reason>" signal at the control.
- The precedence rule rendered where the user sets it: what wins, and why,
  in one line (no prose paragraphs — label grammar).

### Out

- Backend precedence changes (correct already); the global default
  precedence chain UI beyond meetings; #450 Wave 1's one-target-spec API.

## Acceptance criteria

- [ ] Exactly one control decides meetings placement in the UI, or the
  subordinate control visibly names its override state.
- [ ] `placement_source`/`placement_reason` reach the client and render at
  the control; no silent no-op interaction remains.
- [ ] Changing the control changes where meetings actually run (round-trip
  test against the resolver).

## Test plan

- vitest: control rendering per placement state (local, cloud, adopted
  destination, overridden intent).
- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_meeting_placement_policy.py --tb=short` plus a settings-API test for the surfaced provenance.
- Both-widths rendering rides HS-132-14.
