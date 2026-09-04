# Phase 168 settled design — the Connections Door on the surface library

Drafted by the orchestrator 2026-09-04 after the owner's bounce on
his own walk (verbatim in current-phase-status.md) and a read of the
faces he hit, the wire they read, and the 167 settled design (the
spine, D0, is inherited whole — this document names only what
differs). The mockups the owner judges BEFORE any build: the
Connections Door canvas
(https://claude.ai/code/artifact/e3a6776b-151f-4d4c-991a-ef8952a596f6 —
twelve artboards; sources under assets/mockups/, shots under
assets/story-01-shots/).
Status: counsel read 2026-09-04 (opus-worker, read-only) —
RATIFY-WITH-CONDITIONS, 3 M · 4 S · 8 N; ALL PAID below before the
owner sees it (M-1 the five wire states mapped; M-2 BASE a fact, not
a gadget; M-3 the re-read mechanism named; S-1 tiers from the real
palette; S-2 one recovery_hint; S-3 `connection` injected at suggest
time; S-4 the applications.ts label + the alias scar in the census).

## The one sentence

A tool is connected ONCE, in one place the desk names, with one
state and one verb per tool; the interview then only ever asks
"which repo, which project" — so a cold desk reaches its first
tested Watch through the face alone, and nothing on the way is a
sentence the user did not write.

## Today (what the audit measures; recon 2026-09-04)

- The connector has no face. Step 3 "Sources" lists Watch
  suggestions (deterministic, INT-010 — no model call); GitHub and
  Jira are reachable only through a suggestion card whose SOURCE
  chip names them (SuggestionCards.tsx:138). The click selects the
  Watch AND opens a wizard headed "Configure: <watch name>"
  (SetupRoot.tsx:157-283; ProviderWizardStep.tsx:560-562).
- Auth, scope and population share that wizard; scope is per
  proposal (`clarifyProposalScope(id, repo)`; SetupRoot.tsx:176);
  nothing carries to the next same-provider proposal.
- Recovery is a terminal command in a card (ProviderWizardStep.tsx:
  79-96); Jira's add-account fold takes site + email and still needs
  `acli` in a shell (JiraWizard.tsx:189-201).
- The exit verb changes label: "Back to suggestions" / "Done"
  (ProviderWizardStep.tsx:660-668).
- Settings has no Connections: Integrations = CREDENTIALS + MESH
  (SettingsCore.tsx:1043-1110); calendar sources live under Meetings
  (SettingsCore.tsx:803); the Door's "Connect calendar" is the only
  connect verb on the desk (DoorBoardLane.tsx:477-482).
- The readiness data exists with no face: GET /api/providers,
  /github/connection, /jira/connections (providers.py:90-297);
  `watch_provider_connections` (schema.py:3698); no MCP twin.
- **The stopwatch (assets/audit-today.md, face-driven, isolated hub,
  real HOME, 2026-09-04):** connected desk, New Project → a tested
  GitHub Watch = 9 clicks · 12.4 s at 1440 (9 · 11.3 s at 393);
  the exit verb reads `Done`; a second GitHub suggestion re-shows
  the discovery list (scope never carries, +2 clicks). Two
  sentences on the way ("GitHub is ready. Choose a repository to
  watch." · "Repository scoped. Ready to test."). At 393 the first
  GitHub card sits FOURTH, below three native cards, below the fold
  (F10). **Cold desk (gh logged out): 6 clicks · 7.7 s to a SILENT
  dead end (F6)** — the Sources step shows three native cards and
  NOTHING about GitHub or Jira: no card, no chip, no hint
  (project_setup_service.py:316-323 gates provider candidates on a
  connected connection). A cold user cannot learn from the face
  that GitHub exists. Settings → Integrations and Settings →
  Meetings mention neither tool. The 05 walk is measured against
  these numbers. Second pass (Jira measured through the face): New
  Project → the Jira wizard's exit = 15 clicks · 28.2 s — `Test this
  Watch` stays DISABLED after picking a project until Preview runs;
  the Jira exit verb is `Back` while GitHub's is `Done` (two
  grammars). **F7, a PRODUCT defect (project_setup_service.py:74 +
  :333-336):** suggest appends native → GitHub → Jira and cuts the
  list at `_MAX_PROPOSALS = 8`, so on any desk with three native
  facts (3 + 5 GitHub = 8) EVERY Jira suggestion is dropped silently
  — the product generates 13 candidates and persists 8. The audit's
  first pass saw zero Jira cards for this reason, not auth. 02 pays
  it (below).

## D0 — the spine (inherited from 167; what differs here)

Everything in 167 D0 holds: the window chrome, the ledger grammar
(`lead` · `primary` · `time=` always · `cells` · `trailing`), the
chip vocabulary (StateChip · ProvenanceChip · EgressChip · count
chips · quiet tokens), ProgressPlan for anything that runs,
ScrollHint on every scrolling well, SurfaceFooter (egress · receipt
· verbs), the absent/loading/degraded states, MicButton in every
text well, no prose, 393 = one column, the mold.

What this phase adds to the vocabulary — compositions, not species:

- **The tool card**: ChoiceCard (emblem = the tool's mark: `GH`,
  `J`, `◷` calendar, `M` models) · label = the tool (`GitHub` /
  `Jira` / `Calendar` / `Models`) · summary = the account the wire
  reports (`karolswdev` / `karolsaneapple.atlassian.net ·
  karol@…` / `2 sources` / `3 assigned`) · an inline chip row:
  StateChip (the ONE state) · ProvenanceChip (`gh · github.com`,
  `acli · <site>`, `local`) · the ONE verb · a `fold` that opens
  only when the state needs the user (the sign-in command well
  with COPY + Recheck; the add-account gadgets). One card, one
  state, one verb — never two verbs on a tool card.
- **The connect card**: the same tool card rendered where the
  interview needs a tool that is not connected — its verb is
  `Connect GitHub` and it opens D1 in place (below). It replaces the
  wizard for that provider until the tool is connected.
- **The known-scope card**: ChoiceCardShell tier `balanced` (the
  real palette is light/balanced/full — choice-card.css:70-78;
  unknown keys fall back neutral, S-1), label the
  scope (`karolswdev/HoldSpeak` / `KAN`), summary `chosen for <the
  earlier Watch's name>`, one verb `Use this repo` / `Use this
  project`. OFFERED at the top of the scope step; never pre-applied.

## D1 — the Connections face (Settings → Connections)

- **The module.** Settings tile id `integrations` KEEPS its id (the
  census in D7: no caller passes "integrations" by name — DeskToolShelf
  iterates module ids; the Door deep-links "meetings" only; zero deep
  links break). Its LABEL becomes `Connections`, its glyph stays
  (`secret`) until the icon palette gains a plug — a rider, not a
  blocker. The tile's body, top to bottom:
  1. **CONNECTIONS** — GadgetGroup holding a ChoiceCardGroup
     (layout `row` at 640+, stacked at 393) of tool cards:
     - **GitHub**: state from `GET /api/connections` → `connected`
       (StateChip success `Connected`, summary the login, verb
       `Recheck` quiet) · `owner_action_required` (StateChip warning
       `Sign in`; the fold OPEN: SurfaceWell with the exact
       `recovery_hint` — today `gh auth login` — in mono + TransportKey
       COPY; primary verb `Recheck`) · `unavailable` (StateChip
       failure `gh missing`; fold: the install line the wire names +
       COPY + `Recheck`) · `not_configured` (the GitHub provider is
       off in config — StateChip idle `Off`; verb `Recheck`; no
       fold) · `degraded` (the CLI is present, the probe timed out or
       the network failed — StateChip `unreachable` `Unreachable`,
       the wire's `error_detail` as the chip title, verb `Recheck`;
       NEVER rendered as `gh missing` — M-1). ProvenanceChip `gh ·
       github.com`. EgressChip
       `github.com` on Recheck (the check leaves the machine).
     - **Jira**: ONE card per (site, email) connection as the 166
       accounts step draws them (JiraWizard.tsx:123-166 — the
       reference), plus the `Known to acli` cards with `Use this
       account`, plus the ghost `Add account` card (site · email
       StringGadgets with mic · `Add`). With ZERO connections the
       Jira card is the ghost card itself, StateChip idle `Not set
       up`. ProvenanceChip `acli · <site>`; EgressChip `<site>` on
       Recheck.
     - **Calendar**: state from the Door projection's
       `calendar_configured` → `Connected` with summary `N sources`
       or idle `Not set up`; the ONE verb `Set up` / `Sources` opens
       Settings → Meetings' Calendar group (the 146 flow is canon —
       nothing re-implemented; the tile switch is a module change
       inside the same window). ProvenanceChip `local`.
     - **Models**: a LINK card only — summary from the 156 front
       door's assignment summary (`N of 7 assigned`), verb `Open
       Models` → the `models` tile. Never a second models flow.
  2. **CREDENTIALS** — unchanged (SecretRow ×n, the egress line
     `values stay on this hub`).
  3. **MESH** — unchanged (the RAW fold with the device group).
- **The receipt**: the module footer (the settings pane's existing
  foot) carries Receipt `Checked 13:28:04` after any Recheck and the
  EgressChip of the host just contacted; local stdio/none otherwise.
- **Absent/degraded**: the hub unreachable → SurfaceState `error`
  with Retry (as every settings tile); a provider whose recheck
  throws → its card StateChip failure with the wire's
  `last_error_code` as the chip title, never a sentence.
- **393**: cards stack; folds keep the well full-width; COPY stays
  on the well's right edge (the 166 phone precedent).

## D2 — the Sources step (SetupRoot + SuggestionCards)

- **ProgressPlan** `Outcome · Notice · Sources · Review` unchanged
  (the step name `Sources` stays — it is the step where sources are
  chosen; the tools row below makes it legible).
- **TOOLS** — a SurfaceSection above the suggestions, count chip =
  the connector-pack providers the hub knows (`TOOLS 2`): one
  compact tool card per provider from `GET /api/connections`
  (GitHub · Jira; `native` needs none and shows none) — NOT only the
  providers present in the proposals: on a cold desk the suggest
  step yields ZERO provider proposals (the F6 dead end), so the
  tools row is the only place a cold user learns GitHub and Jira
  exist. State read from the wire (02 — the face never derives):
  `Connected` (no verb) or `Sign in` with the verb `Connect GitHub`
  → opens D1 IN PLACE
  (openSurfaceWindow("configure-settings", "integrations") — the
  setup window stays open beneath; the session is server-side and
  resumes — WEB-CR-009; the two windows have distinct ids and
  coexist: compositorSlice.ts:234-256). The re-read mechanism (M-3 —
  the desk has NO window focus/close event for cores): 04 subscribes
  the setup core to the desk store's `windowsById` (a Zustand
  selector on the settings window's id) and re-reads `GET
  /api/connections` when that window LEAVES the map; the TOOLS row's
  connect card also carries `Recheck` as its quiet second action
  while the Connections window is open, so a user who signs in and
  comes back without closing Settings has a named way forward. No
  polling. After the re-read, when a provider went from not
  connected to connected, the step RE-SUGGESTS (POST /suggest is
  idempotent on the session — 02 verifies and pins it; existing
  selections and scopes survive) so that provider's Watch cards
  appear without leaving the interview. No second auth surface
  anywhere in the interview.
- **The cap (02):** suggest keeps a cap PER PROVIDER (native · GitHub
  · Jira, e.g. 4 each, the connected providers never starved) and
  the face groups the cards by provider with the native section LAST
  (the F10 fold fix); the count chip is the persisted count. A
  provider that is connected always has at least its top cards.
- **SUGGESTIONS** — ChoiceCardGroup as 167 D2 drew it (emblem =
  provider, label = the watch, facts = cadence token · action chip ·
  ProvenanceChip) with ONE addition to the facts: the provider's
  StateChip (`Connected` / `Sign in`). A card whose provider is not
  connected renders with NO tier (the neutral fallback — the chip
  carries the state, S-1) and its click does NOT open a
  wizard — it lights the TOOLS row's connect card (scrolls it into
  view) — so the only way forward is the one the face names.
- **The wizard** (a connected provider's card, in place, owns the
  body while open — 167 law): asks SCOPE and POPULATION only. Its
  heading is the ledger row of the Watch (`◉ PR review queue · every
  15 min · observe`), never a sentence. Steps as a ProgressPlan
  `Repository · Population · Test` (GitHub) / `Account · Project ·
  Population · Test` (Jira — `Account` skipped automatically when
  exactly one connection exists; shown when more than one).
- **Known scope**: the scope step opens with the known-scope card
  (above) when an earlier same-provider proposal in this session
  recorded a scope; `Use this repo` applies it to THIS Watch and
  advances; the discovery list follows beneath it. Nothing applied
  until the verb.
- **The verbs** (SurfaceFooter, both wizards): EgressChip of the
  host · receipt (the test's Receipt once run) · `Back` quiet ·
  primary `Test this Watch` until a test passes, then primary `Use
  this Watch`. `Back` leaves the Watch as it was before the wizard
  opened (unselected if it was unselected) and the card shows it. A
  passed test flips the card's chip to `Tested · 12 matches`
  (success). No "Done", no "Back to suggestions".
- **THE BRIEF** (the right column) gains a `TOOLS` fact row
  (`GitHub · Connected`, `Jira · Sign in`) so the brief IS the
  record of what the project will read.

## D3 — the GitHub wizard settled to the wire

- **Repository** step: the known-scope card (when any) → a search
  StringGadget with mic → ChoiceCards from `GET /api/providers/
  github/discover`, HONEST to its wire (github_provider.py:369-375:
  `id`, `name`, `visibility`): emblem = owner initial, label
  `owner/repo`, summary `visibility`, ProvenanceChip `gh ·
  github.com`. The 167 mockup's `BRANCH main · ISSUES 24 · PRS 3`
  facts are RETIRED — the discovery wire does not carry them and a
  chip the wire lacks is fabricated (the 167 D0 law). If 02 adds
  `default_branch` from validate_repo it appears as one token on the
  selected card only; the design draws the card without it. The
  typed `owner/repo` well stays beneath (`Or type a repository path`
  becomes the well's placeholder `owner/repo`, the label retired —
  the 167 counsel N).
- **Population** step: ONE gadget sheet honest to github_templates.py:
  194-246 — SUBJECT fact row `pull requests` (a token, not a choice —
  the wire has one subject), BASE BRANCH as a read-only fact token
  (the template's `base` default — clarify-scope writes only
  `scope.repositories`, project_setup_service.py:893-960, and
  clarify_proposal patches cadence/action/scope, never `query.base`;
  a gadget here would lie — M-2; a query-patch route is a V1 rider),
  and the query in plain words as a SurfaceFacts row
  (`queryPlainWords`, web model.ts:591). The 167 ITEMS
  (issues · pull requests · releases) and LABELS gadgets are RETIRED
  from the design with the reason: the GitHub wire watches pull
  requests only; issues/releases/labels are a V1 rider on the wire,
  never a face that lies. (Counsel confirmed: the base filter is NOT
  settable through clarify-scope — BASE is a fact.)
- **Test** step: ProgressPlan `Auth · Read owner/repo · Fetch N ·
  Baseline ready` + Receipt; the matches ledger (`#412 · title ·
  StateChip open/merged · time` — the normalized entity carries id,
  title, state, updated_at: reaction_service._normalize_entity);
  `0 current matches` = StateChip success `0 matches` with the
  chip title carrying the ACT-002 meaning, the sentence retired.
  Errors = StateChip failure with `error.type` and the message in a
  well (PROV-009 codes rendered honestly).
- The conflict row (`Conflicting sources · 2` with two
  ProvenanceChips and a Disclosure) as 167 D3 drew it.

## D4 — the Jira wizard (the auth section moves out)

- The 166 composition holds (D8 of 167). The ACCOUNT step's add /
  sign-in folds MOVE to D1; inside the interview the step is a pick
  among connected accounts (skipped when exactly one). A Jira
  suggestion with zero connections is a `cool` card whose click
  lights the TOOLS connect card, as D2 says.
- Known-scope card for `KAN` at the top of the Project step.
- Verbs as D2 (`Back` · `Test this Watch` → `Use this Watch`).

## D5 — the phone (393)

Every face above at 393: one column; tool cards stacked; the TOOLS
row before the suggestions; wizards own the body; the ProgressPlan
compact; ledgers drop the time cell; folds full-width with COPY on
the right edge; the footer's verbs never collide (167's two-footer
scar); ScrollHint on the suggestions well.

## D6 — the wire the faces read (what 02 returns; the faces never derive)

| Route / field | Shape | Read by |
| --- | --- | --- |
| `GET /api/connections` | `{tools: [{provider_id, state: connected·owner_action_required·unavailable·degraded·not_configured — MAPPED from the five wire constants (github_provider.py:64-68, shared by jira_provider.py:54-57): `connected`→connected; `disconnected` AND `owner_action_required`→owner_action_required (both carry a recovery hint; the fold opens); `unavailable`→unavailable; `degraded`→degraded; the route's 404 `provider_not_configured`→not_configured (synthesized, M-1), account: {login}·{site,email}·{sources}·{assigned,total}, next_action: {kind: recheck·sign_in·install·add_account·open_module, label}, recovery_hint (ONE string — normalized by 02 from GitHub's `display.recovery_hint`, github_provider.py:231, and Jira's `recovery.command`, providers.py:213-216 — S-2), error_detail, last_checked_at, egress_host, connections?: [...]}]}` — Jira's entry lists its (site,email) connections; the calendar's reads the Door projection flag; models reads the assignment summary | D1, D2's TOOLS row |
| `POST /api/connections/{provider}/recheck` | the same tool entry, rechecked (delegates to the existing rechecks) | D1 |
| proposal `connection` | `{state, account}` on every proposal — INJECTED at suggest/resume time from the connections service (a computed projection, never a `setup_proposals` column — stays fresh, no schema change; S-3) | D2 cards |
| session `known_scopes` | `{github: [{repository, for_proposal_id}], jira: [{project_key, site, for_proposal_id}]}` recorded on clarify-scope | D2/D3/D4 known-scope card |
| MCP `connection_list` / `connection_recheck` | the twins, same shapes, classified | the sidecar |

## D7 — the census (before any module change)

`openSurfaceWindow("configure-settings", <module>)` and
`openSurfaceOr("configure-settings", "/settings", <module>)` callers
(grep 2026-09-04): routes.tsx:59,72 (no module); applications.ts:130;
verbRegistry.ts:298 ("desk"); DoorBoardLane.tsx:479 ("meetings");
DeskToolShelf.tsx:317 (module.id — iterates); TrustWindow.tsx:139;
SurfaceWindows.tsx:173; CommandsCore.tsx:133 ("voice-typing");
PeopleCore.tsx:157 ("people-security"); dictation/Readiness.tsx:89
("voice-typing"). NONE passes "integrations" — the id stays, the
label changes, zero deep links break. The label "Integrations" lives
in TWO places and both change together: settingsPrefs.tsx:43 and the
DESK_APPLICATIONS entry `configure-integrations` at
applications.ts:386 (S-4). A pre-existing scar to ledger, not to lean
on: that application's alias passes scope `integration:destinations`
(applications.ts:141), which SettingsCore.tsx:200-209 accepts but
does not resolve to the tile — the shelf path (module.id) is the
one that works; 03 must not rely on the alias. No test pins the
label "Integrations" (grep 2026-09-04). The 01 audit re-runs this
census and attaches it.

## D7b — face defects the audit shots exposed (04 pays them)

- The footer's receipt line reads `OF 4` in every audit shot (the
  step number is clipped or absent — SetupRoot.tsx:76-83 builds
  `${stepIndex} of 4`); 04 renders the count as a token that is
  visible at 640 and 393.
- THE BRIEF prints `PROPOSED 3` twice (a section label and a
  heading — SetupBrief.tsx) — one label.
- The suggestion card's verdict sentence (`1 recent meetings --
  Meetings: Sprint Planning`, `GitHub connected as karolswdev --
  Surface…`) is prose under the card; it becomes a facts row or a
  Disclosure, never a sentence.
- The Jira wizard's `Test this Watch` stays disabled after a project
  is picked until Preview runs (the audit's second pass, 15 clicks to
  the exit); 04's verbs: a picked scope enables Test — Preview is a
  quiet verb, never a gate.
- At 393 the provider cards sit below three native cards; the TOOLS
  row above the suggestions is the fix, and provider cards for
  connected tools sort before native ones (the wire's order stays;
  the face groups by provider with the native section last).

## D8 — laws and counsel's hunts

- One readiness derivation: the hub's connections service; a face
  that computes "connected" is a finding.
- Connect once: no auth section inside the interview after this
  phase; the connect card is the only path and it returns to the
  same session.
- Offered, never applied: a known scope reaches a Watch only through
  that Watch's own verb.
- A chip the wire lacks is retired from the design, not built (the
  167 D3 facts and sheet).
- No credential ever crosses the face: the command is named, copied
  and rechecked; gh and acli hold the tokens (Article III).
- Egress exactly where egress happens: every Recheck and Test names
  its host; the calendar and models cards are `local`.
- The walk drives the face and shoots the window.
- Counsel hunts: a second derivation; a connect round trip that
  loses the session; a silently applied scope; a fabricated chip; a
  broken deep link; a wizard that still shows auth; a verb label
  that changes with state.
