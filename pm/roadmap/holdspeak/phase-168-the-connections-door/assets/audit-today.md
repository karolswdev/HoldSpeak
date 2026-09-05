# HS-168-01 Stopwatch Audit: Today's Connector Path Through the Face

**Branch:** `feat/connections-door` off `ce629cc2`
**Date:** 2026-09-03 (re-run 2026-09-04 for Jira leg)
**Runner:** `assets/audit/audit_today.py` (env gate `HS168_AUDIT=1`)
**Build:** web bundle rebuilt fresh; hub booted isolated (tmp DB + config, real HOME)
**Auth conditions verified before run:**
- `gh auth status` exit 0: karolswdev (active), karoldriven (inactive) on github.com
- `acli jira auth status` exit 0: karolsaneapple.atlassian.net, karolsane+apple@gmail.com, oauth
**Suggest step:** DETERMINISTIC (project_setup_service.py:250 "Deterministic native suggestions from real desk facts"); zero model egress.

## Condition summary

| Condition | Auth | GitHub cards | Jira cards | Native cards | Total |
| --- | --- | --- | --- | --- | --- |
| connected | gh + acli on PATH, real HOME | 5 | 2 | 1 | 8 |
| cold | GH_CONFIG_DIR=empty, real HOME | 0 | 0 | 3 | 3 |

Connected condition seeded 1 native fact (meeting only). Full seeding
(3 native + 5 GitHub = 8) hits `_MAX_PROPOSALS = 8`
(project_setup_service.py:74) exactly, truncating Jira proposals
appended last -- see finding F7.

## Tables

### Connected condition, 1440 wide

| # | Step | Clicks (cum) | Seconds (cum) | Dead end? | Shot |
| --- | --- | --- | --- | --- | --- |
| 01 | Settings open | 1 | 3.0 | no | before/connected-1440-01-settings-open.png |
| 02 | Settings > Integrations | 2 | 4.0 | no | before/connected-1440-02-settings-integrations.png |
| 03 | Settings > Meetings | 3 | 6.4 | no | before/connected-1440-03-settings-meetings.png |
| 04 | New Project (interview) | 4 | 7.7 | no | before/connected-1440-04-interview-open.png |
| 05 | Outcome answered | 5 | 7.8 | no | before/connected-1440-05-outcome-answered.png |
| 06 | Signals answered | 6 | 7.8 | no | before/connected-1440-06-signals-answered.png |
| 07 | Suggestions (Sources) | 6 | 7.8 | no | before/connected-1440-07-suggestions.png |
| 08 | GitHub wizard | 7 | 7.8 | no | before/connected-1440-08-github-wizard.png |
| 09 | GitHub discovery | 7 | 7.9 | no | before/connected-1440-09-github-discovery.png |
| 10 | GitHub scoped | 8 | 9.9 | no | before/connected-1440-10-github-scoped.png |
| 11 | GitHub test passed | 9 | 10.5 | no | before/connected-1440-11-github-test.png |
| 12 | GitHub exit ("Done") | 10 | 12.1 | no | before/connected-1440-12-github-exit.png |
| 13 | Jira accounts | 11 | 14.1 | no | before/connected-1440-13-jira-accounts.png |
| 14 | Jira scope | 12 | 16.6 | no | before/connected-1440-14-jira-scope.png |
| 15 | Jira project selected | 13 | 16.7 | no | before/connected-1440-15-jira-project-selected.png |
| 16 | Jira test (disabled) | 14 | 26.7 | no | before/connected-1440-16-jira-test.png |
| 17 | Jira exit ("Back") | 15 | 28.2 | no | before/connected-1440-17-jira-exit.png |
| 18 | GitHub second (n/a) | - | - | - | - |

**GitHub wizard verbs:** step 08: `Use this repo`, `Back to suggestions`;
step 10 (scoped): `Test this Watch`, `Done`; step 12 (exit): `Done`.
**Jira wizard verbs:** step 13: `Recheck`, `Add`, `Back`, `Choose project`;
step 14 (scope): `Back`, `Test this Watch` (disabled); step 17 (exit): `Back`.

**Sentences on screen (GitHub wizard):**
- "GitHub is ready. Choose a repository to watch." (step 08)
- "Repository scoped. Ready to test." (step 10)

**Jira account card:** karolsaneapple.atlassian.net, karolsane+apple@gmail.com,
CONNECTED chip, ACLI egress chip.

### Connected condition, 393 wide

| # | Step | Clicks (cum) | Seconds (cum) | Dead end? | Shot |
| --- | --- | --- | --- | --- | --- |
| 01 | Settings open | 1 | 3.0 | no | before/connected-393-01-settings-open.png |
| 02 | Settings > Integrations | 2 | 4.0 | no | before/connected-393-02-settings-integrations.png |
| 03 | Settings > Meetings | 3 | 6.3 | no | before/connected-393-03-settings-meetings.png |
| 04 | Interview open | 4 | 7.7 | no | before/connected-393-04-interview-open.png |
| 05 | Outcome answered | 5 | 7.9 | no | before/connected-393-05-outcome-answered.png |
| 06 | Signals answered | 6 | 7.9 | no | before/connected-393-06-signals-answered.png |
| 07 | Suggestions | 6 | 7.9 | no | before/connected-393-07-suggestions.png |
| 08 | GitHub wizard | 7 | 7.9 | no | before/connected-393-08-github-wizard.png |
| 09 | GitHub discovery | 7 | 8.0 | no | before/connected-393-09-github-discovery.png |
| 10 | GitHub scoped | 8 | 10.0 | no | before/connected-393-10-github-scoped.png |
| 11 | GitHub test | 9 | 10.6 | no | before/connected-393-11-github-test.png |
| 12 | GitHub exit | 10 | 12.2 | no | before/connected-393-12-github-exit.png |
| 13 | Jira accounts | 11 | 14.2 | no | before/connected-393-13-jira-accounts.png |
| 14 | Jira scope | 12 | 16.7 | no | before/connected-393-14-jira-scope.png |
| 15 | Jira project selected | 13 | 16.7 | no | before/connected-393-15-jira-project-selected.png |
| 16 | Jira test (disabled) | 14 | 26.8 | no | before/connected-393-16-jira-test.png |
| 17 | Jira exit ("Back") | 15 | 28.3 | no | before/connected-393-17-jira-exit.png |
| 18 | GitHub second (n/a) | - | - | - | - |

### Cold condition, 1440 wide

| # | Step | Clicks (cum) | Seconds (cum) | Dead end? | Shot |
| --- | --- | --- | --- | --- | --- |
| 01 | Settings open | 1 | 3.0 | no | before/cold-1440-01-settings-open.png |
| 02 | Settings > Integrations | 2 | 4.0 | no | before/cold-1440-02-settings-integrations.png |
| 03 | Settings > Meetings | 3 | 6.3 | no | before/cold-1440-03-settings-meetings.png |
| 04 | Interview open | 4 | 7.6 | no | before/cold-1440-04-interview-open.png |
| 05 | Outcome answered | 5 | 7.7 | no | before/cold-1440-05-outcome-answered.png |
| 06 | Signals answered | 6 | 7.7 | no | before/cold-1440-06-signals-answered.png |
| 07 | Suggestions (3 native only) | 6 | 7.7 | no | before/cold-1440-07-suggestions.png |
| 08 | No GitHub cards | 6 | 7.7 | YES | before/cold-1440-08-no-github-cards.png |
| 09 | No Jira cards | - | - | YES | before/cold-1440-09-no-jira-cards.png |
| 10 | No second GitHub | - | - | - | - |

### Cold condition, 393 wide

| # | Step | Clicks (cum) | Seconds (cum) | Dead end? | Shot |
| --- | --- | --- | --- | --- | --- |
| 01-06 | (same as cold-1440) | 6 | 7.7 | no | before/cold-393-*.png |
| 07 | Suggestions (3 native only) | 6 | 7.7 | no | before/cold-393-07-suggestions.png |
| 08 | No GitHub cards | 6 | 7.7 | YES | before/cold-393-08-no-github-cards.png |
| 09 | No Jira cards | - | - | YES | before/cold-393-09-no-jira-cards.png |

## Totals

| Metric | Connected 1440 | Connected 393 | Cold 1440 | Cold 393 |
| --- | --- | --- | --- | --- |
| New Project to tested GitHub Watch | **9 clicks, 10.5s** | **9 clicks, 10.6s** | n/a (no cards) | n/a |
| New Project to Jira exit (test disabled) | **15 clicks, 28.2s** | **15 clicks, 28.3s** | n/a | n/a |
| New Project to dead end (cold) | - | - | **6 clicks, 7.7s (silent)** | **6 clicks, 7.7s** |
| Total steps recorded | 18 | 18 | 10 | 10 |

**The cold dead end is SILENT.** The user answers both questions, sees 3 native
cards with no GitHub or Jira option, and has no path forward to connect. No
error, no hint, no "Connect GitHub" card.

**The Jira test never ran.** The "Test this Watch" button in the Jira scope
step remained DISABLED after selecting a project. The Jira wizard requires
Preview before Test (the scope must be clarified via `onClarifyScope`),
making the Jira path longer and less obvious than GitHub's.

## Findings

### F1: No Connections face anywhere in Settings
**Anchor:** settingsPrefs.tsx:29-46
Settings has 8 modules: Voice, Sounds & Presence, Meetings, Rhythm, Models,
Assignments, Integrations, System. None is named "Connections". No module
mentions GitHub or Jira. The Integrations module (settingsPrefs.tsx:43,
SettingsCore.tsx:1043-1084) contains only credentials (web pairing token,
device audio key, Telegram bot token, Telegram pairing code, Slack webhook,
Custom webhook) + a RAW fold with 2 failure_webhook entries. Zero connection
status for any tool.

### F2: Three concerns share one wizard face
**Anchor:** ProviderWizardStep.tsx:508-672, SetupRoot.tsx:181-203
Clicking a GitHub suggestion card opens one wizard that handles:
(a) connection auth status check, (b) repo/scope discovery and selection,
(c) test/activation. All three are coupled to one proposal ID. The heading
reads "Configure: PR review queue" (the Watch name, not "Connect GitHub").

### F3: Scope does not carry between suggestions
**Anchor:** project_setup_service.py:395-431 (clarify_proposal per proposal)
Each proposal carries its own `spec.subject.scope` and
`clarifyProposalScope(id, repo)` scopes one proposal. Two GitHub Watches
on the same repo require two identical repo picks. (Confirmed by the first
audit run: second GitHub card showed discovery list again.)

### F4: The exit verb label changes meaning
**Anchor:** ProviderWizardStep.tsx:660-668
Before scope: the button reads "Back to suggestions".
After scope: the button reads "Done".
Neither says what happens to the Watch. The Jira wizard exit verb is
"Back" at all steps (a different verb from the GitHub wizard's "Done").

### F5: Auth recovery is a terminal command
**Anchor:** ProviderWizardStep.tsx:79-96
When `status.state === "owner_action_required"`, the wizard shows:
> To connect, run in your terminal:
> `gh auth login`
> Then press Recheck below.
This is the ONLY recovery path. No in-app auth flow exists.

### F6: The cold condition is a silent dead end
**Anchor:** project_setup_service.py:316-323 (GitHub candidates gated on
`status.get("state") != STATE_CONNECTED`), project_setup_service.py:1000-1006
(Jira candidates gated on connected connections)
When gh is not authenticated and no Jira connections are registered, the
suggest step returns only native proposals. The user sees 3 cards with
SOURCE=native. No card says "Connect GitHub" or "Connect Jira". No error,
no empty state, no call to action. The path to connecting is invisible.

### F7: The 8-proposal cap silently truncates Jira
**Anchor:** project_setup_service.py:74 (`_MAX_PROPOSALS = 8`), :333-335
(`proposals[:_MAX_PROPOSALS]`)
Generation order: native proposals (meetings, decisions, door) -> GitHub
templates (5) -> Jira templates (5). With a typical desk (3 native + 5
GitHub = 8), the Jira templates at indices 8-12 are truncated by the cap.
The product DOES generate Jira candidates when connected (confirmed by
direct `_jira_candidates` call returning 5), but the persist loop drops
them. The initial harness observation of "zero Jira cards" was caused
by this cap, not by a priming or adapter failure.

### F8: The Settings > Meetings calendar section has no "Connect" verb
**Anchor:** SettingsCore.tsx:801-849
The Meetings module shows Calendar > Sources (an ICS URL table with
ADD SOURCE / IMPORT SCREENSHOT). The Door's "Connect calendar"
(DoorBoardLane.tsx:479) is the only "connect" verb on the desk surface, and
it connects a calendar source (ICS URL), not a tool.

### F9: The GitHub wizard heading names the Watch, not the tool
**Anchor:** ProviderWizardStep.tsx:581-583
The heading reads `Configure: {proposal.spec.name}` -- e.g. "Configure: PR
review queue". A user who wants to connect GitHub sees a heading about a
Watch they did not ask for. The connection is subordinate to the Watch.

### F10: First GitHub card is not visible without scrolling at 393
**Anchor:** transcript.json connected-393 suggestions step
At 393 wide, the first GitHub card sits at index 1 (with minimal seeding).
With full seeding (3 native cards first), the first GitHub card sits at
index 3 and is below the fold at 852px viewport height.

## Census: every caller of `openSurfaceWindow("configure-settings", ...)` and deep links

### Production callers (excluding tests)

| Caller | File:Line | Target module | Context |
| --- | --- | --- | --- |
| Door "Connect calendar" | DoorBoardLane.tsx:479 | meetings | The ONLY "connect" verb on the desk |
| Settings verb (menu/hotkey) | verbRegistry.ts:298 | desk (-> system alias) | Opens Settings tile grid |
| Trust window fallback | TrustWindow.tsx:139 | (none) | Opens Settings tile grid |
| Commands > voice typing | CommandsCore.tsx:133 | voice-typing (-> voice alias) | Link from commands |
| People > security | PeopleCore.tsx:157 | people-security | Unresolved module id (no alias) |
| Dictation > readiness | Readiness.tsx:89 | voice-typing (-> voice alias) | Link from readiness |
| DeskToolShelf (all modules) | DeskToolShelf.tsx:317 | `module.id` (each tile) | Settings palette entries |

### Module aliases (settingsPrefs.tsx:50-61)

| Alias | Resolves to |
| --- | --- |
| appearance | sounds |
| hotkey | voice |
| transcription | voice |
| voice-typing | voice |
| wake-word | voice |
| presence | sounds |
| cadence | rhythm |
| devices | system |
| delivery | models |
| desk | system |

**No alias resolves to "connections"** -- the module does not exist. Any future
`openSurfaceWindow("configure-settings", "connections")` call would need a new
PREF_MODULES entry and a new alias if the old id changes.

### `configure-runs-on` (Model Library front door, separate surface)

| Caller | File:Line |
| --- | --- |
| ThoughtWorkspaceWindow | ThoughtWorkspaceWindow.tsx:351 |
| CapabilitySection | CapabilitySection.tsx:191 |
| DeskToolInspector | DeskToolInspector.tsx:341 |
| SetupCore | SetupCore.tsx:160 |
| DictationSections | DictationSections.tsx:36 |

## Shot verification

All shots read at true size. Key observations:
- connected-1440-01: Settings tile grid. 8 tiles, no "Connections" tile.
- connected-1440-02: Integrations module. Credentials only (web pairing token,
  device audio key, Telegram, Slack webhook, Custom webhook). No tool status.
- connected-1440-07: Suggestions with 8 cards. 1 native (Meeting activity),
  5 GitHub (PR review queue, CI health, Merge flow, Delivery drift, Release
  readiness), 2 Jira (Jira blockers, Jira delivery flow).
- connected-1440-08/09: DUPLICATE hashes (wizard shot taken before discovery
  loads; discovery loads synchronously from the connected adapter).
- connected-1440-10: Scoped state. "Repository scoped. Ready to test." with
  ProgressPlan (Auth, Read karolswdev/HoldSpeak, Baseline ready).
- connected-1440-11: Test passed. TESTED chip on the card in the right column.
- connected-1440-13: Jira accounts step. One account card: karolsaneapple,
  CONNECTED chip, Recheck button, Add ghost card.
- connected-1440-14: Jira scope step. KAN and SAM1 projects visible.
- connected-1440-16: Jira test step. Test button DISABLED.
- connected-393-07: At phone width, only the first card (Meeting activity)
  is fully visible. GitHub and Jira cards are below the fold.
- cold-1440-07: 3 native cards only. PROPOSED 3. No GitHub, no Jira, no
  "connect" verb, no empty state text.
