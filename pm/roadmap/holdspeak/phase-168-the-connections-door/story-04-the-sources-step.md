# HS-168-04 - The Sources step connect-once

- **Project:** holdspeak
- **Phase:** 168
- **Status:** done
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

- [x] A disconnected provider never opens a wizard; the connect card round-trips to Connections and back with the session intact (glass-asserted).
- [x] A connected provider's wizard shows no auth section; scope chosen once is offered to the next same-provider proposal and applied only on that card's verb.
- [x] Both exit verbs leave the Watch in a state the card shows; the 159/161/166/167 rigs green (selector edits only); shots read at true size.

## Delivered (2026-09-04)

The Sources step connect-once: a TOOLS row (ToolsRow.tsx) above the
suggestions from `GET /api/connections` — every connector-pack
provider, `Connected` with no verb or `Sign in` with `Connect GitHub`
/ `Connect Jira` (opens Settings → Connections in place; the setup
window stays mounted; the controller subscribes to the desk store's
`windowsById` and re-reads + re-suggests when the settings window
leaves the map — no polling) and a quiet `Recheck`; suggestion cards
with the provider's StateChip, the rationale folded into a
Disclosure, a disconnected provider's card lighting the TOOLS card
instead of opening a wizard; the wizards asking scope + population
only (the GitHub connection card and the Jira auth folds GONE; the
Jira account step skipped with one connection), the heading a ledger
row of the Watch, ProgressPlan of steps, the known-scope card offered
first and applied only by its verb, `Back` · `Test this Watch`
(enabled by a picked scope) → `Use this Watch`; D3's honest facts
(SUBJECT · QUERY; BASE when the template carries it); THE BRIEF's
TOOLS row, one `PROPOSED N`, the native emblem honest; the footer's
step count visible. The seam it found: re-suggest was NOT idempotent
(`wprop_<uuid>` per call — a second suggest orphaned every
selection); paid in the setup service with a dedup key per (provider,
template) — existing rows returned unchanged, only new candidates
added — failing-then-passing in the integration suite. Four
orchestrator rounds: no glass rig + 67 vitest skips (theater) →
rebuilt; the shots' "washed-out column" diagnosed by the
orchestrator's Playwright probe as the RIG shooting mid
`surface-rise-in` (a settle-animations helper now in glass_infra);
the wizard footer outside the window; the heading without its
primary; the brief's emblem; `Test this Watch` enabled with no scope;
the Jira wizard shots skipped and called "acceptable" — required.
Shots (assets/story-04-shots/, 20): cold + connected Sources at both
widths, the connect round trip, the answered row, the GitHub wizard
(repository · known scope · tested), the Jira wizard (project ·
scoped).

## The owner's bounce on the live face (2026-09-04)

Verbatim: "dude. Why is the edit button such a generic HTML button,
but not a button of our design component library...? — and also,
why is the checkmark on one line and then the content on another..."
Paid in this story: every raw `<button>` under setup/** becomes the
library Button (the 167 counsel's ledgered "design-level call" —
ruled by the owner); the lead/primary split fixed at the species
(surface.css [data-wrap] narrow-container rule). Shots of the
answered row at both widths in assets/story-04-shots/.

## Test plan

- **Vitest:** the setup suite (SetupRoot/SuggestionCards/ProviderWizardStep/JiraWizard) + the controller's known-scope handling.
- **Glass:** tests/e2e/test_hs168_sources_glass.py (the connect round trip; the connected wizard; the known-scope offer) + the 159/161/166/167 rigs.
- **Baseline:** zero branch-new.
