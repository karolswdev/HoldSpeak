# Phase 166 settled design — the Jira face (story 04, round 2)

Drafted by the orchestrator 2026-09-03 after the owner's round-1
verdict on the first build, verbatim: "I absolutely hate the UX of
this thing ... Walls of text..., complete disregard to our component
and our motto of 'delighting our end-user'." The mockups the owner
judges BEFORE the rebuild: the Jira Watch Setup canvas
(https://claude.ai/code/artifact/85d15031-1c9c-407d-934f-6c36b0ac84e3).
Status: RATIFIED by the owner 2026-09-03, verbatim: "HECK YES, a BIG YES to this." Builders implement.

## The one sentence

The Jira face is composed ONLY from the surface library the 156
council ratified — every account and project is a ChoiceCard object,
every state a StateChip, every egress a ProvenanceChip naming the
site, the population a gadget sheet, the test a ProgressPlan that
lights up, the matches a ledger — and it never speaks a sentence.

## D1 — accounts are objects (ChoiceCardGroup, layout=row)

- One ChoiceCard per (site, email): emblem = the site's initial,
  label = the site, summary = the email, facts = StateChip
  (Connected · success / Sign in · warning / acli missing ·
  unreachable) + auth-type chip + ProvenanceChip `acli · <site>`.
- The selected card carries the accent presence; Recheck is a quiet
  verb on the card, never a sentence.
- A `Sign in` card opens its fold in place: the exact login command
  in a well with a COPY key, and ONE primary verb: Recheck. No hint
  prose ("Authenticate with your Atlassian API token..." is gone).
- Accounts acli already knows (the registry) appear as cool-tier
  cards with `Known to acli` and one verb: Use this account.
- The ghost `+ Add account` card holds two StringGadgets (site,
  email — mic in the well) and a quiet Add. No strip, no modal.
- Footer: a lamp chip `1 of 2 connected` + Back + the primary
  `Choose project`.

## D2 — scope is a project card + a gadget sheet

- Projects: ChoiceCards (emblem = key, label = name, facts = type ·
  style · issue count · ProvenanceChip). Selected = accent.
- Population: ONE gadget sheet — TYPES (enumerated; etched toggles),
  STATUS (observed; toggles + a `2 of 3 categories seen` chip — never
  dressed as enumerated), DUE (Within 7 days · Overdue toggles; the
  landing row highlighted), JQL (optional; mono StringGadget with
  mic).
- Preview: the display step `2 issues · 3 calls · 0.9s` + ledger
  rows (key · summary · StateChip · DUE token) + the compiled JQL as
  a token under the ProvenanceChip. A typed `query_invalid` renders
  as an ActionNotice under the JQL row — in flow, never overlapping.

## D3 — the test is a ProgressPlan that lights up

- Steps: Switch to <site> · Read back account · Search <project> ·
  Enrich N issues · Baseline ready — each with its rate/count and a
  done bar; footer = Receipt `Test passed · HH:MM:SS` +
  ProvenanceChip. The plan IS the honesty: the switch-and-verify
  law and the N+1 calls are visible, not narrated.
- Matches: the display step `2 of 3 issues · 3 calls` + ledger rows.
- Will notice: chips — the template's conditions (accent) and the
  transitions the source emits (quiet); cadence and action chips.
- Footer: lamp `Tested` + Test again + primary `Review and activate`.

## D4 — laws

- No sentences anywhere on the face (no-prose law). Labels are
  tokens; states are chips; commands are wells with COPY.
- Egress exactly where egress happens: the ProvenanceChip names the
  selected site on the account card, the project card, Preview, and
  the test footer. Never "github.com" on a Jira control.
- The wizard OWNS the window body while open: the suggestion column
  collapses (the GitHub wizard's own behavior), no bleed-through.
- 393: cards stack, ledger drops the DUE cell, nothing ellipsizes an
  identity (site and email wrap).
- MicButton in every text well (site, email, JQL, project search).
- Every component imports through `desk/surface` (the ratchet
  fence); feature CSS may lay out, never restyle library species.

## D5 — the rebuild

Replace JiraConnectionList / JiraScopePicker / JiraTestDisplay /
JiraWizardFlow and the `.jira-*` CSS in setup.css (lines ~1117-1610)
with compositions of ChoiceCardGroup/ChoiceCard, StateChip,
ProvenanceChip, Receipt, ActionNotice, GadgetGroup/GadgetRow/
StringGadget/CheckGadget, ProgressPlan, SurfaceLedgerRow, Disclosure.
Keep model.ts / api.ts / useSetupController.ts (clean). Replace the
five Jira component test files; keep the decoder + controller tests.
The glass rig re-shoots all ten steps at 1440 + 393; the orchestrator
reads every PNG; the owner sees the shots before merge.
