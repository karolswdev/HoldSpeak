# HS-166-04 - The web face: the provider-keyed wizard, many accounts, the site badge

- **Project:** holdspeak
- **Phase:** 166
- **Status:** backlog
- **Depends on:** HS-166-03
- **Unblocks:** HS-166-05
- **Owner:** unassigned

## Problem

The setup wizard is GitHub-shaped: ProviderWizardStep.tsx:111
hard-codes "contacts github.com", model.ts:610-705 types only the
github wire, useSetupController.ts:506 holds one providerConnection.
Jira needs a picker over MANY connections, and Article III demands
the badge name the real host at the point of egress.

## Scope

- **In:** the wizard generalized to provider-keyed state (github |
  jira) — never a second wizard. A Jira connection list: one row per
  (site, email) with its state chip; "Add account" shows the exact
  `acli jira auth login --site … --email … --token` in-world (the
  Door recovery-command species, ProviderWizardStep.tsx:74-84) then
  Recheck — never a credential field (PROV-004/005). Scope picker:
  project(s) then issue types / status categories (or `derived`
  labeled as such), then the constrained population (status/
  priority/assignee/labels/components/sprint/advanced JQL). The
  egress badge on Check/Discover/Test names `<site>.atlassian.net`
  for the selected connection (Article III §2; the 164 MODEL-chip
  lesson: badges exactly where egress happens). TestResult renders
  the jira population block (03). SETFLOW-005 states rendered
  honestly: unavailable / partial / connected. Beauty pass after the
  functional pass; the scroll-hint species on any scrolling well;
  shots at 1440 + 393 into the gallery (rig BUILDS FIRST).
- **Out:** live verdict (05), docs (06).

## Acceptance criteria

- [ ] Two Jira connections render, select, and recheck independently; adding one never touches the other's state; the GitHub path is pixel-unchanged (its shots re-taken, diffed).
- [ ] The egress badge shows the selected site's host on every egress control; no prose reassurance anywhere (no-privacy-novels law).
- [ ] Vitest for the provider-keyed model + controller; web baseline zero branch-new; shots reviewed by the orchestrator before the owner.

## Test plan

- **Web:** web/src/features/project-room/setup/__tests__ (model, controller, wizard, TestResult); `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** the setup shots rig (build first) → assets/ + the gallery.
