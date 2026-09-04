# HS-168-01 - The audit + the settled design: Connections and the Sources step on the library

- **Project:** holdspeak
- **Phase:** 168
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-168-02, HS-168-03, HS-168-04
- **Owner:** unassigned

## Problem

The owner got confused configuring connectors on his own walk. The
law (2026-09-03): no face is built before he has ratified its design
on the library. This story measures today's path honestly, then
designs the flow — zero product code.

## Scope

- **In:** (a) the stopwatch audit, assets/audit-today.md: a fresh
  HOME (nothing connected) on the branch build; New Project driven
  THROUGH THE FACE by Playwright at 1440 and 393 from "New Project"
  to a tested GitHub Watch and a tested Jira Watch; every click,
  every second, every dead end, every sentence on screen counted;
  before-shots of the WINDOW at each step (assets/before/); the same
  path on the owner's real desk read-only (his gh + acli connected)
  for the connected-state shots. Facts, not adjectives. (b) the
  settled design, assets/settled-design-connections.md, in the 167
  form: D0 the spine (reuse 167's — identity band, ledger grammar,
  chip vocabulary, ScrollHint, footer; name only what differs); D1
  the Connections face — Settings → Connections (or the module the
  design names; the census of `openSurfaceWindow("configure-
  settings", …)` callers attached): ONE ChoiceCard per tool (GitHub
  · Jira · Calendar; model hosts as a LINK card to the 156 front
  door), one StateChip, one next verb, the ProvenanceChip naming the
  real host, the sign-in fold with the exact command in a mono well
  + COPY + Recheck, Jira's Add account as the 166 fold, the calendar
  card routing to the 146 flow; the CREDENTIALS and MESH groups keep
  their home; absent/degraded states drawn. D2 the Sources step
  redone — every suggestion card wears its provider's connection
  StateChip read from the wire; a disconnected provider renders ONE
  connect card ("Connect GitHub") that opens D1 in place and returns
  to the same session; a connected provider's card opens the wizard
  that asks SCOPE ONLY (repo / project + population) — never auth; a
  known-scope card offers the repo/project chosen for an earlier
  same-provider Watch (offered, never applied); the exit verbs
  unambiguous (`Use this Watch` / `Back`); D3 the GitHub wizard
  settled to the wire (pull requests + base branch; the 167
  ITEMS/LABELS sheet retired from the design with the reason
  written; a conflict row as 167 drew it); D4 the Jira wizard
  unchanged except the auth section moving to D1; the phone
  artboards for every face. Zero sentences; the egress chip names
  the host at the point of egress. (c) counsel (opus-worker, read-
  only) reads the design against the barrel, contract.md, the 167
  settled design and the current faces BEFORE the owner; findings
  paid in the design. (d) the mockups: a `design` canvas with every
  face at 1440 and 393, real token values, sources committed under
  assets/mockups/; the orchestrator reads every PNG at true size.
  (e) the owner's verdict recorded verbatim here and in the record;
  a bounce = redesign, not a build.
- **Out:** any change under web/src or holdspeak/.

## Acceptance criteria

- [ ] The audit records clicks, seconds, dead ends and on-screen sentences for today's path at both widths, with window shots — the baseline the 05 stopwatch is measured against.
- [ ] The settled design covers D1-D4 with the species named from the barrel, the callers census for any module rename, and the D3 wire ruling; counsel's findings paid in the design.
- [ ] Mockups at both widths published, sources committed, token values real; the owner's word recorded verbatim; PASS before 02/03/04 start.

## Test plan

- **Audit:** the Playwright audit script under assets/ (real build, fresh HOME, both widths) — its output IS the audit.
- **Design:** the token validator over the mockup sources; `.githooks/dw check holdspeak` green on phase-168.
