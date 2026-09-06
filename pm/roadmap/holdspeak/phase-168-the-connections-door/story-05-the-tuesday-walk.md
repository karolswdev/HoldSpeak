# HS-168-05 - The Tuesday walk, face-driven: the owner's real desk under the stopwatch

- **Project:** holdspeak
- **Phase:** 168
- **Status:** done
- **Depends on:** HS-168-03, HS-168-04
- **Unblocks:** HS-168-07
- **Owner:** unassigned

## Problem

The 167 walk drove setup through the wire and shot the desk; the
owner walked the face himself and got confused. This walk drives the
FACE, shoots the WINDOW at every step, and reads the stopwatch
against the 01 baseline.

## Scope

- **In:** assets/walk-script.md (the steps, what is asserted, both
  widths) and the runner tests/e2e/live168_walk.py (HS168_WALK=1;
  HS168_WALK_DB=isolated|real; real HOME; skip-guarded on gh + acli;
  build-first): from a cold state (the isolated leg: nothing
  connected; the real leg: his gh + acli) — open Settings →
  Connections, read the state, Recheck; New Project → the interview
  → Sources → the connect card round trip (isolated leg) → the
  GitHub wizard scope-only on `karolswdev/HoldSpeak` → Test → the
  Jira wizard on KAN → Test → the known-scope offer on a second
  same-provider suggestion → Review → Activate → the Room lands.
  Every step: click the window, wait on the face, shoot the window
  at 1440 and 393; clicks and seconds recorded to a transcript and
  compared with assets/audit-today.md. The real leg archives the
  project in a finally with unattended OFF BEFORE archive (the 167
  law) and reverts any KAN touch. Then the owner's attended walk and
  his verdict, verbatim, in this story and the record. Every defect
  found live gets a failing-then-passing test under tests/unit/
  test_hs168_walk_fixes.py or the owner's word that it is ledgered.
- **Out:** steward / update steps (167 proved them).

## Acceptance criteria

- [x] The runner drives the face and shoots the window; no step may be skipped; a step that cannot be asserted fails the walk (a hash-identical pair of step shots fails the walk).
- [x] The stopwatch: clicks and seconds for cold → two tested Watches, recorded beside the 01 baseline; one terminal visit per tool at most.
- [x] The owner's verdict recorded verbatim; his word on "no longer confuses me" is the exit.

## Delivered (2026-09-04)

The runner tests/e2e/live168_walk.py (HS168_WALK=1; HS168_WALK_DB=
isolated|real; real HOME; build-first; every shot settled; every step
asserted; consecutive shots hash-different) and assets/walk-script.md
+ assets/stopwatch.md. ISOLATED leg (real gh + acli, tmp DB): cold →
Settings → Connections `Sign in` / `Not set up` → New Project → the
TOOLS row with `Connect GitHub` / `Connect Jira` and zero provider
cards → the connect round trip (Connections opens over the setup
window; the session's answers survive) → re-boot connected → Settings
→ Connections `Connected` for both → Sources with Connected chips →
the GitHub wizard scope-only on karolswdev/HoldSpeak → Test → Use this
Watch → a second GitHub suggestion offers the known-scope card `chosen
for PR review queue` → Use this repo → Test → the Jira wizard on KAN
(account step skipped) → Test → Review (3 watches, both baselines
established) → Activate → the Room lands; 2 passed at 1440 + 393, 22
steps each. THE REAL LEG on the owner's desk (HS168_WALK_DB=real,
run by the orchestrator; DB backed up beside itself first): 2 passed
in 89 s; at 1440 the connected part ran 18 clicks · 38.3 s to the
Room (project_id=proj-4ed6be467d96; lifecycle=active); at 393 18 clicks · 35.5 s; both projects
ARCHIVED in the finally with every watch paused (the DB read back:
three archived projects, watches 2/2 · 3/3 · 3/3 paused; the 167
project untouched). The stopwatch (assets/stopwatch.md): BEFORE 9
clicks · 10.5 s to a tested GitHub Watch with two sentences and a
terminal command inside the wizard → AFTER 7 clicks · 11.7 s, zero
sentences, no terminal command in the interview; the second GitHub
Watch 4 clicks from the first (the known scope); Jira 15 clicks, Test
enabled by the pick; cold: from a SILENT dead end to `Connect GitHub`
on the face at 4 clicks. Two species bugs the real-desk shots exposed
and paid (b159bd71): the footer's egress slot clipped hosts at 156px
(every truncated host on the branch), and an empty egress slot shifted
the receipt into the narrow first column (`OF 4`). Runner scar paid:
the real leg overwrote the isolated leg's shots — legs now write
`real-` prefixed directories. Shots: assets/story-05-walk/{cold,
connected,real-connected}-{desktop,phone}/ + the four transcripts.

## THE OWNER'S ATTENDED WALK (2026-09-04) — BOUNCE, verbatim

On the hub built from the branch (http://127.0.0.1:53379, real desk):
"unacceptable UI work..., see how the TIMELINE, DECISIONS, SEARCH,
ASK are just completely off to the side of the window, as on this
screenshot... second to this..., I really don't understand why
everything's still so complicated. The tool suggestions are still not
obvious AT ALL, it's not obvious I have to click them to then scroll
within that same dialog to test them, validate them, and so on. I'm
telling you - this stuff is still not streamlined at all..." — then:
"so prepare another Muad'Dib."

Roots (found in this sitting, NOT yet paid):
1. **The wings escape the window** — a long project name in the Room's
   title bar pushes TIMELINE · DECISIONS · SEARCH · ASK past the
   window's right edge: web/src/desk/components/pullout.css:284
   `.desk-pullout-head.has-wings .desk-pullout-title { flex: none }`
   (HS-100-07) — the title never shrinks when wings are present. A
   window-chrome species bug: `flex: 0 1 auto; min-width: 0` (the
   ellipsis rule at :130-134 already exists) and the wings
   `flex-shrink: 0`. Every Room with a long name shows it.
2. **The Sources step is not legible** — the built face renders a
   provider's wizard INLINE inside the main column under the answered
   rows, beside THE BRIEF (SetupRoot.tsx:167-283: SurfaceColumns
   main=[SetupInterview, ToolsRow, wizard-or-cards], side=SetupBrief),
   so the user clicks a card and must scroll the same dialog to find
   the wizard; nothing on a card says it is the entry. The ratified
   law (167 D0, inherited by 168 D2) says "wizards own the whole body
   while open" — the build violated it. The fix is design-level and
   small: (a) every provider suggestion card carries ONE verb (`Set
   up`, primary on the card; `Tested · N` after), the click target
   named; (b) while a wizard is open it OWNS the body — the answered
   rows, the TOOLS row and THE BRIEF unmount; the ProgressPlan of the
   wizard's steps sits under the window's own plan; the footer carries
   only `Back · Test this Watch / Use this Watch`; closing returns to
   the cards with the chip flipped; (c) the Sources step's ProgressPlan
   label reads what the step is (`Sources · pick what to watch`), never
   just `Sources` — if a token can carry it; (d) re-shoot at both widths
   and re-walk on his desk BEFORE asking him again.

Story 05 stays IN PROGRESS; the phase does not close on this verdict.

## THE SECOND SITTING (2026-09-04, Muad'Dib VII) — both roots PAID

Root 1 — the wings (window chrome, species level; every window that
passes `wings=` is covered — nine callers):
- pullout.css:129 `.desk-pullout-title` gains `min-width: 0` (the flex
  item's `min-width: auto` had blocked the ellipsis everywhere);
  :285 `.has-wings .desk-pullout-title` `flex: none` → `flex: 0 1 auto;
  min-width: 0`; :295 `.desk-wings { flex-shrink: 0 }`;
  DeskWindow.tsx:873 wraps `{actions}` in `.desk-window-actions`
  (window-chrome.css: `flex-shrink: 0`).
- Pinned: tests/e2e/test_hs168_window_wings_glass.py (a Room with a
  70-char name at 1440 and 393; the wings' box inside the head and the
  window; the title's scrollWidth > clientWidth). Before the fix:
  `Wings right edge (898) exceeds head right edge (392)`; after: 2
  passed. CSS-contract guard windowWings.test.ts (4). Shots:
  assets/story-05-shots/wings-1440.png, wings-393.png.
- Rider (he did not name it; he would have): the Room said the project
  name four times — name, outcomeText and purpose all derive from the
  ONE outcome answer at project_setup_service.py:689-710 (name =
  outcome[:80]; purpose = the original text). The band now shows the
  name once when they coincide (ProjectRoomCore.tsx RoomIdentityBand;
  3 vitests). The derivation is untouched — ledgered for the close.

Root 2 — the Sources step (built to the RATIFIED artboard, which the
first build had left):
- SetupRoot.tsx: an open wizard (GitHub, Jira) or ClarifyStep OWNS
  the body — the answered rows, TOOLS, the brief and the setup footer
  UNMOUNT (an early return, never CSS); Back / Use this Watch return
  to the cards. In the proposals state the two answered rows span the
  full window above the columns (`.setup-answered-band`), TOOLS +
  SUGGESTIONS left, THE BRIEF right — as Sources.dc.html.
- SuggestionCards.tsx: one named verb per card species, all library
  Buttons — connected+untested `Set up` (primary; body click enters
  too); tested `Tested · N` chip + `Remove` (ghost); disconnected
  `Connect` (ghost → the same openConnectionsInPlace the TOOLS card
  uses; the scroll-to-TOOLS hunt is deleted); native cards unchanged.
  The cards sit under `SUGGESTIONS N`.
- SetupBrief.tsx: the brief's watches block is `SOURCES N` = the chosen
  ones only (`NONE YET` token when empty); the PROPOSED-9 ledger of
  every proposal's chips is gone (noise the artboard never had).
- Mockups amended first (D7c card verbs on Sources.dc.html +
  SourcesPhone.dc.html; assets/story-01-shots/amend-sources-*.png) and
  the canvas republished (same URL, version "D7c amendment: card verbs").
- Pinned: ProviderWizardMounted.test.tsx ("wizard owns the body":
  cards, TOOLS, brief, answered rows absent while open; back after
  Back), SuggestionCardVerbs.test.tsx (9), SetupInterview.test.tsx
  (brief = chosen only). Setup vitest 8 files / 244. The sources rig
  (test_hs168_sources_glass.py) enters via `setup-card-setup-<id>`
  and asserts TOOLS/cards count 0 while the wizard is open + the
  wizard's top within 120px of the root: 4 passed; shots
  github-wizard-owns-body-{1440,393}.png. The walk runner + walk-script
  rows 12/16/20 click `Set up`.
- Not taken: (c) the plan label — `Sources` stays (ratified); the
  cards' section label and the card verbs carry what the step asks.

Laws (into the handover + memory): "owns the body" means UNMOUNT;
a card that is an entry carries its verb; a window's wings never
leave the window — titles shrink first; walk it with HIM in mind.

### Found live by the re-walk (his desk, read-only sqlite)

1. **The Jira Watch was born broken — PAID.** Every walk project (both
   sittings) and the owner's OWN project (proj-10b35905777c, created
   08:29 local today) stored `issue_types: [""]`: JiraWizard.tsx fired
   `onToggleType("")` 100 ms after the first project pick; the setup
   route stored it (`issue_types or []` is truthy); finalize wrote it
   into query_json; `_compile_jql` emitted `issuetype in ('')`; Jira
   answered `failed to parse JQL query: the value '' does not exist for
   the field 'issuetype'`; baseline_state stayed `pending` — while the
   Test step said passed, because `_native_test_read` merged
   `scope.projects` but never `scope.issue_types` (Test and evaluation
   compiled DIFFERENT queries). Paid at three seams: the wizard no
   longer injects a blank; `_compile_jql` drops blank entries in every
   list clause (his saved watches heal on the next tick, no migration);
   the Test path merges scope.issue_types (parity). Tests:
   tests/unit/test_hs168_walk_fixes.py (10: blanks, parity, the
   owner's exact stored query). Live: the compiled JQL for his stored
   query ran through acli and returned KAN-2. Re-walk after the fix:
   1440 passed, the new project's jira row `baseline_state =
   established`, `last_error` empty, no `issue_types` key.
2. **The Jira scope step showed a BLANK `PROJECT` section while
   discovery ran** (no loading token) — the 393 shot caught it. Paid:
   `LOADING PROJECTS` token (JiraWizard.test.tsx +2). The 393 leg then
   failed three times at `LOADING PROJECTS` for >27 s while the unit
   fast lane (`-n auto`, 12 min, every core) ran beside it; with the
   wire timed and the machine idle, discovery took 2.2 s and the leg
   passed. Law: a live desk walk never shares the machine with the
   parallel suite. The runner now prints every /api/providers request
   with its duration on failure.
3. **Paused watches on ARCHIVED projects are still evaluated hourly**
   by the automation conductor's legacy pump (holdspeak.log: `Watch
   conductor: {'status': 'failed'…}` for watch_8a19439d72e4 /
   watch_1c6c1382f526 every ~35 min since 06:16 — real acli egress for
   archived projects; the 165 "legacy-side watch guard" debt made
   visible). Being paid at the selection seam in this sitting.
4. **The owner's own project carries a native `meeting` Watch that
   fails every tick**: `native can accept pushed snapshots but has no
   local query adapter yet` (watch_980edbb89697). A Watch the face let
   him activate cannot evaluate — ledgered for the close (final-summary
   debts); not paid here.

**THE OWNER'S ATTENDED WALK — recorded above (BOUNCE).** His desk: the hub restarted
on the branch build (`cd web && npm run build`, then restart
`holdspeak web`); walk assets/walk-script.md's connected steps by hand
at his hub and on the 393 glass; the Tuesday question. His verdict,
verbatim, closes this story.

## SUPERSEDED (2026-09-05) — closed by Phase 169

The owner's bounce on this door (above) was paid at its roots in the
second sitting, and then his mandate went further: "really refine and
really streamline the UX… the first module we BOTH will be proud of."
Phase 169 The Streamlined Door replaced this phase's Sources step and
the Room with the one-screen door and the four-question Room; its
walk ran on his desk (5 clicks) and he gave his word to merge. This
story's evidence is the OLD door's walk (isolated + real legs, green)
and the two rigs captured after the roots were paid; its verdict is
the bounce recorded above, answered by 169. Closed as superseded; the
owner's own attended walk of the NEW door is owed in 169's ledger.

## Test plan

- **Live:** `HS168_WALK=1 HS168_WALK_DB=isolated uv run pytest -q tests/e2e/live168_walk.py` (real HOME, from a real shell); then `HS168_WALK_DB=real` on his desk; the transcript + PNGs under assets/story-05-walk/.
