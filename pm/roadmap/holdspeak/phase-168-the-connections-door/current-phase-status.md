# Phase 168 - The Connections Door

- **Project:** holdspeak
- **Status:** CHARTERED 0/7
- **Chartered:** 2026-09-04 off main `ce629cc2` (167 The Room in Use MERGED via PR #549 → `a47ae31f`; the handover PR #550 merged after it)
- **Canon:** docs/internal/CONSTITUTION.md (Article III honest egress — every connection check names its host; Article XI — the caller supplies neither principal nor authority); docs/internal/POSITIONING.md (the voice rules — zero sentences in the UI); web/src/desk/surface/contract.md (the library contract); docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §7 (providers) + §9.5 (the wizard); the owner's laws: face-design-before-build (2026-09-03), setup flows must be joyful (2026-08-17), the front-door law from Settings → Models (2026-08-31), "will you use this on a Tuesday?" (Phase 139)

## The charter

The owner walked the Room on his real desk after 167 merged and
bounced the connectors, verbatim (2026-09-04): **"I still..., get
pretty upset around how unintuitive it is to configure the
connectors, I feel like that itself deserves its own sort of... UX
wizard IMO ... our main idea was to delight the user with an
incredible, Workbench 2.0 on steroids inspired fashion, but not to
confuse them ... Even myself - I got confused. Not good, not good."**
His word to open this phase: "charter it".

What he hit (recon 2026-09-04, anchors verified):

1. **There is no connector step.** The interview's step 3 "Sources"
   is a list of AI-generated Watch suggestions (SuggestionCards.tsx).
   GitHub and Jira are reachable only by clicking a suggestion card
   whose SOURCE chip happens to read `github` or `jira`; the click
   both selects the Watch AND swaps the column for a wizard headed
   "Configure: <watch name>" (SetupRoot.tsx:157-283). The connector
   is subordinate to a Watch the user has not asked for yet.
2. **Three concerns on one face.** Account auth, repo/project scope
   and the Watch's population all live in that wizard
   (ProviderWizardStep.tsx:508-673; JiraWizard.tsx). Scope is per
   proposal (`clarifyProposalScope(id, repo)`), so two GitHub
   suggestions mean two wizards and two repo picks; nothing carries.
3. **Auth recovery is a terminal command** (ProviderWizardStep.tsx:
   79-96: "To connect, run in your terminal: gh auth login"); Jira's
   "Add account" takes site + email and still needs `acli` in a
   shell.
4. **No front door.** Settings has no Connections face: Settings →
   Integrations (settingsPrefs.tsx:43; SettingsCore.tsx:1043-1110)
   is credentials (web token, Telegram, webhooks) + mesh; calendar
   lives under Settings → Meetings (SettingsCore.tsx:803) and the
   Door's "Connect calendar" (DoorBoardLane.tsx:477-482) is the only
   "connect" verb on the whole desk. The readiness data exists —
   GET /api/providers, /github/connection, /jira/connections
   (providers.py:90-297), `watch_provider_connections` (schema.py:
   3698) — with no face of its own and no MCP twin.
5. **The exit verb is ambiguous**: the same button reads "Back to
   suggestions" before scope and "Done" after (ProviderWizardStep.
   tsx:660-668); neither says what happens to the Watch.
6. **The ratified D3 design did not fully land**: the 167 canvas
   shows ITEMS / LABELS / BRANCH gadgets; the built wizard still has
   the discovery list, the typed-repo box and "Repository scoped.
   Ready to test." The 167 records do not ledger the gap — and the
   GitHub wire (github_templates.py:194-246) carries pull requests +
   a base-branch filter only, so the ITEMS/LABELS sheet would have
   fabricated chips. This phase settles it honestly.
7. **A finding against the orchestrator**: the 167 real-desk walk
   drove setup through the WIRE. Its four setup shots (assets/
   story-06-walk/real-1440/01..04) are the desk with no window open;
   03 and 04 are byte-identical. Nobody walked New Project through
   the UI on his desk before he did. The law this phase adds: a
   setup walk drives the FACE and shoots the WINDOW.

This is the same defect class as Settings → Models (2026-08-31):
the architecture is right (adapters, discovery, test, activation)
and there is no front door. The fix is the same shape: one
first-class flow on top of the existing machinery, never a parallel
authority.

The exit, verbatim: **a cold desk with nothing connected reaches its
first GitHub Watch on a real repo and its first Jira Watch on a real
site through the FACE alone — every step shot at both widths — with
one terminal visit per tool at most, under the stopwatch, and the
owner's word is that configuring connectors no longer confuses
him.**

The chain: 01 the audit + the settled design (the stopwatch audit
of today's path THROUGH THE FACE; the Connections face + the Sources
step redone, designed on the library; mockups at 1440 + 393; OWNER
RATIFIES — zero code) -> 02 the connections service (one readiness
shape across providers on the hub; the suggest step annotated with
it; known scopes per setup session; MCP twins) || 03 the
Connections face (Settings → Connections; glass rig) -> 04 the
Sources step connect-once (connection state on the cards; the
connect card opens Connections in place and returns; the wizard asks
scope only; scope carries; honest verbs; D3 settled to the wire) ->
05 the Tuesday walk, face-driven (the owner's real desk; the window
shot at every step; the stopwatch; OWNER VERDICT) || 06 the docs ->
07 the close.

OUT: model hosts (the 156 front door owns them; the Connections
face may LINK to it, never re-implement it); a second calendar
setup (the 146 flow is canon; the Connections card routes to it);
new providers; MCP-008 remote (its own charter, prepared in the
handover); OAuth or token capture of any kind (gh and acli hold the
credentials — Article III; the face only names the command and
rechecks).

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-168-01 | The audit + the settled design (the stopwatch audit through the face; Connections + Sources on the library; mockups at 1440 + 393; OWNER RATIFIES) | backlog | [story-01-the-settled-design](./story-01-the-settled-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-168-02 | The connections service (one readiness shape; the suggest step annotated; known scopes; MCP twins) | backlog | [story-02-the-connections-service](./story-02-the-connections-service.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-168-03 | The Connections face (Settings → Connections; one state, one verb per tool; the sign-in fold; glass rig at both widths) | backlog | [story-03-the-connections-face](./story-03-the-connections-face.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-168-04 | The Sources step connect-once (state on the cards; connect in place and return; the wizard asks scope only; scope carries; honest verbs; D3 settled) | backlog | [story-04-the-sources-step](./story-04-the-sources-step.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-168-05 | The Tuesday walk, face-driven (the owner's real desk; the window shot at every step; the stopwatch — OWNER VERDICT) | backlog | [story-05-the-tuesday-walk](./story-05-the-tuesday-walk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-168-06 | The docs ("Connect your tools" in the guide; the Rooms guide re-shot; MCP_SIDECAR regenerated; README prerequisites) | backlog | [story-06-the-docs](./story-06-the-docs.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-168-07 | The close (gates, riders, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | [evidence-story-07](./evidence-story-07.md) |

## Where we are

**CHARTERED 0/7.** Branch `feat/connections-door` off main
`ce629cc2`. The owner's bounce on his own walk (2026-09-04) and his
word: "charter it". Recon (read-only, anchors verified): the
connector has no face of its own — it hides inside Watch suggestion
cards; auth, scope and population share one wizard; scope is per
proposal; recovery is a terminal command; Settings → Integrations is
credentials + mesh; the readiness routes and the connections table
exist with no front door and no MCP twin; the 167 GitHub wizard
mockup's ITEMS/LABELS sheet never landed and would have fabricated
chips the wire lacks; the 167 walk shot the desk, not the setup
window. Next: 01 — the stopwatch audit through the face on a fresh
HOME, before-shots at both widths, the settled design, the mockups,
counsel, then the owner's word.

## Active risks

- **A Connections face that computes state a second time.** The
  face and the interview must READ one readiness shape from the hub
  (02); if either derives "connected" on its own, the two will
  disagree on the day gh logs out. Counsel hunts a second
  derivation.
- **Opening Settings mid-interview must not lose the setup session.**
  The connect card opens the Connections face in place and returns
  to the same session (project_setup_resume exists — the 159 seam);
  a walk step asserts the answers survive the round trip.
- **"Connect once" must not become "scope once".** A repo or project
  chosen for one Watch is OFFERED for the next same-provider Watch
  (a known-scope card), never applied silently. A Watch never
  inherits a scope the user did not pick on its own face.
- **Renaming Settings → Integrations breaks deep links.**
  `openSurfaceWindow("configure-settings", "<module>")` ids are
  called from the Door and the Front Door; the design decides the
  module name and the census names every caller before it moves.
- **The credentials rows must survive.** Whatever the Connections
  face becomes, the web token / Telegram / webhook rows and the mesh
  group keep a home and their tests keep passing.
- **The wire decides the population sheet.** The GitHub wire is pull
  requests + a base-branch filter. The design draws what the wire
  carries; ITEMS/LABELS become a ledgered V1 rider unless 02 grows
  the wire honestly (it does not, in this charter).
- **The walk must drive the face.** A runner that calls the routes
  and shoots the desk is theater (the 167 scar). The 05 runner
  clicks the window, waits on the face, shoots the window; a step
  that cannot be asserted fails the walk.
