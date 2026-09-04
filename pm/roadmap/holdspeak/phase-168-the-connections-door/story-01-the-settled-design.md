# HS-168-01 - The audit + the settled design: Connections and the Sources step on the library

- **Project:** holdspeak
- **Phase:** 168
- **Status:** in-progress
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

## The audit (2026-09-04)

Face-driven Playwright on an isolated hub (tmp DB + config, real
HOME; gh karolswdev + acli karolsaneapple.atlassian.net authenticated;
the cold condition = GH_CONFIG_DIR empty): assets/audit-today.md,
assets/audit/audit_today.py + transcript.json, 46 window shots under
assets/before/. Connected: New Project → a tested GitHub Watch = 9
clicks · 12.4 s (1440) / 9 · 11.3 s (393); two sentences; exit verb
`Done`; a second GitHub suggestion repicks the repo. Cold: 6 clicks ·
7.7 s to a SILENT dead end — three native cards, nothing about GitHub
or Jira anywhere (the worst finding). Settings names neither tool.
The audit's first pass saw no Jira cards even when connected; the
orchestrator's wire probe on the same boot (add → recheck → suggest)
returned github AND jira proposals, so the audit was sent back — and
its second pass found the real cause, a PRODUCT defect: suggest cuts
the list at `_MAX_PROPOSALS = 8` after appending native → GitHub →
Jira (project_setup_service.py:74, :333-336), so a desk with three
native facts never sees a Jira card. Jira measured through the face
with a one-fact desk: 15 clicks · 28.2 s to the wizard's exit, `Test
this Watch` disabled until Preview, the exit verb `Back` (GitHub's
is `Done`). 52 window shots.

## Counsel round (2026-09-04)

Counsel (opus-worker, read-only) read the design against the barrel,
contract.md, the 167 spine and the wire: **RATIFY-WITH-CONDITIONS** —
3 M (the wire has FIVE connection states, the design mapped four and
would have rendered a network timeout as "gh missing"; BASE BRANCH
drawn as a gadget the wire cannot write — clarify-scope writes only
repositories; the connect round trip's re-read had no mechanism — the
desk has no window focus/close event for cores), 4 S (tiers `warm`/
`cool` are not palette keys — light/balanced/full; two recovery-hint
shapes across providers; the proposal `connection` field must be a
computed projection; the "Integrations" label also lives in
applications.ts:386 and its alias scope never resolved the tile), 8 N
(suggest confirmed deterministic; validate_repo carries no
default_branch; ITEMS/LABELS never landed and 167 never ledgered it;
the normalized entity matches the matches ledger; calendar_configured
lives in door_service; the connect-once premise holds; the 393
forward path is visible; the module id is safe). ALL PAID in the
design (D1 gains the `degraded` → `Unreachable` state; D3 BASE is a
fact; D2 names the windowsById subscription + the tools-row Recheck;
D6 carries the five-state mapping and one recovery_hint; D7 the
second label and the alias scar). The audit then added F6 (the cold
dead end) → D2's TOOLS row lists every connector-pack provider from
the wire, not only those in proposals, and re-suggests after a
connect; and D7b (four face defects the shots exposed, for 04).

## The mockups (2026-09-04)

Canvas: https://claude.ai/code/artifact/e3a6776b-151f-4d4c-991a-ef8952a596f6 — twelve
artboards (six faces × 640 window + 393 glass): Connections connected
· Connections cold · the Sources step · the GitHub wizard (repository)
· the GitHub wizard (tested) · the Jira wizard (project). Two Fedaykin
authors composing from the 167 atlas and the settled design; the
orchestrator read every PNG at true size — three bounce rounds paid
(the Room wings on the New Project window; a clipped host in the Jira
footer; a selected repo beside a disabled primary; two verbs with one
label; native template names on Jira cards; a 2×2 grid that voided
the GitHub card and stacked Jira's chips → one column of full-width
tool rows; overprinting SecretRows at 393; a ghost Jira card with no
identity; an empty cold footer → `local · Not checked`; abbreviated
tile labels). Sources committed: assets/mockups/*.dc.html +
canvas.json; shots: assets/story-01-shots/. **THE OWNER'S WORD:**
pending.

## Test plan

- **Audit:** the Playwright audit script under assets/ (real build, fresh HOME, both widths) — its output IS the audit.
- **Design:** the token validator over the mockup sources; `.githooks/dw check holdspeak` green on phase-168.
