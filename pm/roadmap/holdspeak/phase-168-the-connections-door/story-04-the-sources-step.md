# HS-168-04 - The Sources step connect-once

- **Project:** holdspeak
- **Phase:** 168
- **Status:** backlog
- **Depends on:** HS-168-01, HS-168-02, HS-168-03
- **Unblocks:** HS-168-05
- **Owner:** unassigned

## Problem

Step 3 of the interview asks the user to find a Watch card whose
small SOURCE chip says github, click it, and then authenticate,
scope and populate on one face headed by the Watch's name — per
proposal, with an exit verb that changes its label. This is the
face the owner bounced.

## Scope

- **In:** SuggestionCards / SetupRoot / ProviderWizardStep /
  JiraWizard recomposed to D2-D4: every suggestion card wears its
  provider's connection StateChip from the wire (02); a
  disconnected provider renders ONE connect card that opens the
  Connections face in place and returns to the SAME setup session
  (project_setup_resume — the answers survive, asserted); a
  connected provider's card opens a wizard that asks scope +
  population only (the auth section gone from both wizards); the
  known-scope card offers an earlier same-provider scope (offered,
  never applied); the verbs `Use this Watch` / `Back` with the Watch
  state legible after either; D3 settled to the wire (pull requests
  + base branch; the ITEMS/LABELS sheet retired with the reason in
  the story; no chip the wire lacks); the ProgressPlan step label
  from `Sources` to what the design names. Tests that pin dead DOM
  get SELECTOR edits (the 167 law); the 159/161/166/167 rigs green
  on the recomposed faces; shots at both widths.
- **Out:** the controllers' wire decoders beyond the 02 fields; new
  templates.

## Acceptance criteria

- [ ] A disconnected provider never opens a wizard; the connect card round-trips to Connections and back with the session intact (glass-asserted).
- [ ] A connected provider's wizard shows no auth section; scope chosen once is offered to the next same-provider proposal and applied only on that card's verb.
- [ ] Both exit verbs leave the Watch in a state the card shows; the 159/161/166/167 rigs green (selector edits only); shots read at true size.

## Test plan

- **Vitest:** the setup suite (SetupRoot/SuggestionCards/ProviderWizardStep/JiraWizard) + the controller's known-scope handling.
- **Glass:** tests/e2e/test_hs168_sources_glass.py (the connect round trip; the connected wizard; the known-scope offer) + the 159/161/166/167 rigs.
- **Baseline:** zero branch-new.
