# HS-166-04 - The web face: the provider-keyed wizard, many accounts, the site badge

- **Project:** holdspeak
- **Phase:** 166
- **Status:** done
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

- [x] Two Jira connections render, select, and recheck independently; adding one never touches the other's state; the GitHub path is pixel-unchanged (its shots re-taken, diffed).
- [x] The egress badge shows the selected site's host on every egress control; no prose reassurance anywhere (no-privacy-novels law).
- [x] Vitest for the provider-keyed model + controller; web baseline zero branch-new; shots reviewed by the orchestrator before the owner.

## Test plan

- **Web:** web/src/features/project-room/setup/__tests__ (model, controller, wizard, TestResult); `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** the setup shots rig (build first) → assets/ + the gallery.

## Owner verdict — round 1 (2026-09-03): BOUNCE, verbatim

"I can already tell you, Muad'Dib, that I absolutely hate the UX of
this thing that you put in front of my eye. Walls of text...,
complete disregard to our component and our motto of 'delighting
our end-user' kind of thing... come the frig on...?"

Orchestrator's reading: the first build assembled label:value rows,
sentences, and a prose recovery block instead of composing the desk
surface species (ChoiceCardShell, chips, EgressChip, ledger rows)
into a flow that operates with joy. Two pixel bounces were the wrong
instrument — the DESIGN is the finding. The worker was halted; the
Python fixes it found (calls in the proposal test path, the issue
subject test read, providers.py enrichment, the web jira adapter,
the fixture escaping) are kept; web/src is redesigned from a spec
the orchestrator writes on the surface species, with mockups the
owner sees BEFORE the next build.

## Owner verdict — the redesign canvas (2026-09-03): RATIFIED, verbatim

"HECK YES, a BIG YES to this." — on the Jira Watch Setup canvas
(assets/settled-design-face.md D1-D5; the mockups composed only from
the surface library). The rebuild follows the settled design; the
glass rig re-shoots all steps; the orchestrator reads every PNG; the
owner sees the shots before merge.

## Trace record (orchestrator round, 2026-09-03)

- Shipped: setup/JiraWizard.tsx (+ jira-wizard.css, layout only)
  composed ONLY from the surface library — ChoiceCardGroup/ChoiceCard
  account and project objects, StateChip, ProvenanceChip naming the
  selected site, Disclosure + SurfaceWell + COPY TransportKey for the
  login command, GadgetGroup/GadgetRow(wide)/CheckGadget/StringGadget
  (mic) for the population sheet, ProgressPlan + Receipt for the
  test, SurfaceLedgerRow for matches/preview, ActionNotice for
  query_invalid, LampGadget footers; the `.jira-*` bespoke CSS
  (~490 lines) DELETED; the wizard owns the window body; model/api/
  controller kept; human token maps (conditionLabel, actionLabel,
  transitionLabel, plural) shared with the activation review, which
  now shows issue KEYS, not internal ids.
- Python seams: acli_runner on MeetingWebServer (the glass fixture
  seam; injected into every JiraProviderAdapter + the web snapshot
  fetcher), the clarify-jira-scope route + MCP twin (TOOLS 43→44),
  providers.py row enrichment (account/recovery on the wire), the
  proposal test path's `issue` subject with the §8.2 display block
  (calls = 1 + N), the fixture escaping bug.
- THE ROUND LEDGER (the owner's trust, spent and repaid): build 1 →
  bounce (wizard never rendered; conditional skip = theater) →
  bounce (1440 overlap, duplicate shot, "calls 0") → OWNER VERDICT
  "I absolutely hate the UX" → HALT → settled design + mockups on
  the library → OWNER "HECK YES, a BIG YES" → rebuild → catches
  (stretched chips, bare boxes, missing preview, empty test = a
  fixture lie, duplicate verbs) → catches (decoder whitelist dropped
  `calls` — the true seam; raw wire ids on chips; one-per-line
  toggles; conditional preview shot) → final nits (wide rows, review
  leaks, plurals, 2 of 3 categories) → DONE. Every PNG read by the
  orchestrator each round.
- Honest notes: the glass rig runs the interview by API with a
  stateful acli fixture runner (two accounts: one connected, one
  sign-in); the live face is the walk's (05). The population toggles
  are visual state in this round (the controller carries the scope;
  toggles bind in 05's walk if the live proof needs them — recorded,
  not hidden).
- Evidence note: the first capture's Python leg had ONE failure —
  the project-family discoverability pin (33 → 34, the clarify twin)
  — updated honestly; the second capture is clean on every gate
  (vitest 258, baseline zero branch-new, guard, Python 269, rig 2).
