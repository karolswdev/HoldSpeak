# The Streamlined Door and the Room — the settled design (Phase 169)

Written 2026-09-04 from the owner's words on his walk of Phase 168:
"I really don't understand why everything's still so complicated...
this stuff is still not streamlined at all"; on the Room: "that
interface I really didn't honestly like and/or understand"; the
mandate: "really refine and really streamline the UX... this module
to be the first one that we BOTH will be proud of... absolutely
world-freaking-class". He ratified the thesis below in conversation
(2026-09-04): the one-screen door, and the Room as four questions.

Canon this rides on: CONSTITUTION Articles III (egress at the point
of decision), VI (honest), VII (the interface serves), VIII
(native-grade craft); DESIGN_SYSTEM.md — the interior canon (type
scale, composition rules 1-6, the aerogel receipt, the banned left
rail); the surface library species (web/src/desk/surface). Every
verb is the library Button. Zero sentences in the UI except the ones
written here. Every chip names a fact the wire has.

## D0 — the two jobs

1. **The Door** (New Project): "Tell HoldSpeak what you are
   delivering and which tools to watch." ONE screen, no plan, no
   wizard, no review page. Connected desk: repo + Jira project to a
   live Room in 5 clicks, no scrolling at 1440.
2. **The Room** (a project, opened): answers four questions, in this
   order, every time: What needs me now? What am I watching, and is
   it working? What changed since I last looked? What did we decide
   and what do I owe people? Then one ask box.

## D1 — what is cut (and where it goes)

| Cut | Where it goes |
|---|---|
| The Notice question | Gone from the door. Meeting-derived suggestions surface later INSIDE the Room (a "Suggested" row under SOURCES), never blocking creation. |
| Suggestion cards, rationale disclosures | Gone. Sources are rows with pickers. |
| THE BRIEF side panel | Gone. The rows are the brief. |
| The 4-step ProgressPlan (Outcome · Notice · Sources · Review) | Gone. One screen has no steps. |
| Provider wizards (Repository · Population · Test) | Gone. A picker + defaults + an Adjust disclosure. |
| The Test button / Review page | Gone. The count IS the test: picking a scope fetches the count at once; the row reads it. |
| The native `meeting` Watch | Never offered until it can evaluate (no local query adapter). Existing ones show their failure in plain words with `Remove`. |
| Room counters (Meetings 0 · Resources 0 · Watches 0 · Changes 1), `REV n`, raw journal lines (`Created · name, source, watches_activated`), the footer PROJECT token | Gone. Counts live on the source rows; the journal speaks in phrases; the name is said once. |
| Wings TIMELINE · DECISIONS · SEARCH · ASK | Two wings: ROOM · HISTORY. Ask is a box at the foot of the Room. Search lives in History. |
| The Updates and Steward peer verbs | One primary verb in the head: `Draft update`. The steward's automation settings live under the source rows (`Adjust`). |

## D2 — the type scale and the palette (from the ratified 168 mockups; real tokens at the build)

- display 26/650 `--font-display` (Space Grotesk) — ONCE per face: the
  Room's headline count ("3 need you" / "Nothing needs you").
- primary 15/600 Inter — the outcome line; a row's title.
- body 13 — continuous copy (rare).
- secondary 12 JetBrains Mono — counts, times, sources.
- caption 11/600 mono uppercase 0.06em — section labels, chips.
- Palette: desk #0e0f13 · window #15171d · head #242833 · well
  #1c1f27 · hairline #2a2e3e · edge #363b50 · text #f2f3f5 · muted
  #9ba2b0 · faint #767e8d · accent #a86e4a (hover #bc8058) · success
  #34d399 · warning #fbbf24 · danger #f87171 · info #56c7f5. Radius
  2px. Bevel: inset 1px 1px 0 rgba(255,255,255,.14), inset -1px -1px
  0 rgba(0,0,0,.40). The window shell markup is Main.dc.html's (168).
- **Motion — four moments, named (composition rule 5; nothing moves at
  rest; reduced motion = instant):**
  1. *The picker unfolds* — the well grows from the row's lower edge
     with the window spring (`--duration-med`, `--ease-quart`); cards
     settle in with `surface-rise-in` staggered 30 ms.
  2. *The count arrives* — the `○ CHECKING` token pulses
     (`surface-chip-pulse`); the count crossfades in over 200 ms and
     the token fades out; the footer receipt's number ticks.
  3. *First paint of the Room* — sections rise in order (head, NEEDS
     YOU, SOURCES, …) 40 ms apart; the headline number is the last to
     land.
  4. *Something new needs you* — while the Room is open, a new NEEDS
     YOU row rises in at the top with a faint accent-tinted field that
     fades over 1.2 s, and the headline count re-lands with emphasis
     (a 1.04 scale-settle); the desk's bell carries the same fact when
     the Room is closed.

## D3 — the Door (window "New Project", 640 wide at 1440; 393 glass)

Body, top to bottom, gap 18px:

1. **The outcome line.** An EditInPlace well (well fill, 15/600
   primary text, min-height 44px, the MicButton at its right edge —
   the voice law). Placeholder, faint: `What are you delivering?`.
   Filled example: `Ship the Q4 platform on schedule with zero
   incidents`. This one line is the project's name (first 80 chars)
   and its outcome. No label above it — the placeholder is the
   question. A small caption under it, faint: `THIS BECOMES THE
   PROJECT'S NAME`.

2. **SOURCES** (caption label with a count token, e.g. `SOURCES 2`).
   One ledger row per connector provider from `GET /api/connections`
   (GitHub, Jira; calendar and models are NOT project sources). Row
   grammar (SurfaceLedgerRow, lead slot 52px):
   - lead: the provider emblem (`GH`, `J`) in mono 600.
   - primary: the SCOPE PICKER trigger — a ghost Button whose label is
     the picked scope or the verb: `Choose a repository` /
     `karolswdev/HoldSpeak ▾`; Jira: `Choose a project` /
     `KAN · WRONG ▾`. The trigger is the only click to scope.
   - cells: the DEFAULT WATCHES as toggle tokens (CheckGadget species,
     pressed = on): GitHub `OPEN PRS` `CI` ; Jira `OVERDUE` `DUE 7
     DAYS` `BLOCKED` (BLOCKED off by default). Then the LIVE COUNT in
     secondary mono, arriving as soon as a scope is picked: `12 open
     PRs · CI green` / `3 overdue · 5 due this week`; before it
     arrives a StateChip `○ CHECKING` (pulse); on failure a StateChip
     `⚠ CAN'T CHECK` + the plain reason as a secondary line.
   - trailing: EgressChip naming the host (`GITHUB.COM`,
     `KAROLSANEAPPLE.ATLASSIAN.NET`) — the point of decision — and a
     ghost `Adjust` (Disclosure) that unfolds under the row: GitHub →
     base branch (StringGadget, default `main`), labels; Jira → issue
     types, JQL (optional). Adjust is the ONLY place the old wizard's
     population lives.
   - A NOT-CONNECTED provider row: emblem · the provider name ·
     StateChip `⚠ SIGN IN` (the 168 vocabulary: Sign in / Not set up /
     Unreachable) · one primary Button `Connect` → opens Settings →
     Connections in place (168 D2 round trip) · no picker, no
     toggles. On return the row re-reads and becomes a picker row.
   - Rows sort: connected first, then not connected.

3. **The picker, open** (no modal — in-world, under the row): a well
   that unfolds below the row with a typeahead StringGadget + mic
   (`Search repositories`), then ChoiceCards in a single column:
   `K karolswdev/HoldSpeak · public · GH GITHUB.COM`, recent first,
   max 6 then `Show more`. Jira: projects `KAN · WRONG · software`,
   `SAM1 · (Example) Bi-annual…`. Picking collapses the picker and
   fires the count. A KNOWN SCOPE (a repo another project watches)
   sits first with a token `ALSO WATCHED BY <project>` — offered,
   never applied.

3b. **The three states a row passes through:** UNPICKED — the trigger
   reads `Choose a repository` in muted, the toggles present but
   quiet (no count line); CHECKING — the moment after a pick: the
   trigger holds the scope, the count slot shows `○ CHECKING` pulsing
   and the receipt does not yet count the source; LIVE — the count in
   secondary with the source counted. The very FIRST open of the Door
   (nothing typed, nothing picked) is its most important face: the
   outcome well's placeholder `What are you delivering?` at primary
   weight is the only loud element; both rows UNPICKED; `Create
   Project` present but disabled (a muted primary) until the outcome
   has text; the receipt reads `NO SOURCES · BLANK PROJECT`.
3c. **Adjust, open** (a Disclosure under the row, the same well as the
   picker): GitHub → `BASE BRANCH` StringGadget (default `main`),
   `LABELS` StringGadget (empty, placeholder `any`), `DRAFTS` toggle
   (off); Jira → `ISSUE TYPES` toggles from discovery, `JQL` StringGadget
   (optional). No verb inside; clicking `Adjust` again folds it. The
   old wizard's population lives here and nowhere else.

4. **Footer** (SurfaceFooter): receipt `2 SOURCES · 4 WATCHES` (live
   totals; `NO SOURCES · BLANK PROJECT` when none); egress slot empty
   (each row carries its own); verbs `Cancel` (ghost) ·
   `Create Project` (primary; enabled when the outcome line has text;
   with zero sources it creates a blank project — allowed, named by
   the receipt).

Click count, connected desk: outcome text (typing) → GitHub trigger
(1) → repo card (2) → Jira trigger (3) → project card (4) → Create
Project (5). The counts arrived while he picked. Cold desk: Connect
(1) → the command well in Connections (copy = 2) → Recheck (3) →
back on the same door, then the five above.

393: the same rows, one column; the cells wrap under the primary
(the row's `wrap`); the picker is full-width; the footer stacks
verbs right.

## D4 — the Room (window default 800 wide at 1440; 393 glass)

Title bar: the project name (ellipsis; wings never leave the window —
168's law). Wings: `ROOM` (active) · `HISTORY`.

Body, top to bottom, gap 20px:

1. **The head** (SurfaceIdentity recomposed): the HEADLINE at display
   step — `3 need you` (accent) or `Nothing needs you` (muted); a chip
   row: StateChip health `● AT RISK` (danger) / `● ON TRACK` (success)
   with its reason token (`3 OVERDUE` / `CI RED` / `REVIEW WAITING 3
   DAYS`), then — when the project has a target date (the wire's
   `targetAt`) — `TARGET OCT 15 · 41 DAYS` (danger-toned `OVERDUE BY 3
   DAYS` once passed; a passed target is an AT RISK input), then
   `CHECKED 3 MIN AGO`. Trailing: ONE primary Button `Draft
   update`. The outcome line appears in the head ONLY when the title
   bar cannot show it whole (the name is the outcome's first 80 chars;
   when the title bar ellipsizes it — 393, or a long outcome — the
   head carries the full line at primary; otherwise the title bar says
   it once and the head does not repeat it — counsel S4, the 168
   four-times scar). No host chips in the head (the source rows carry
   them at their own decision points — counsel N1). No REV, no ACTIVE
   chip (an archived Room says `ARCHIVED` here instead).
   **Health derivation (counsel, hunt 6):** AT RISK when ANY of:
   overdue Jira entities > 0 · CI failing on the base branch · a
   review waiting on the owner > 3 days; ON TRACK when none. The reason
   token names the first true input in that order. Named in code and
   pinned by tests (story 04).

2. **NEEDS YOU** (caption label + count). Ledger rows, severity-first:
   lead = source emblem; primary = the thing's title (`#612 Rig
   settles animations before every shot`); cells = WHY as one token
   (`WAITING ON YOUR REVIEW · 3 DAYS`, `40 MIN AGO`, `OVERDUE · 2
   DAYS`, `DECISION PENDING`); a CI row's TITLE is the thing itself —
   `CI failing on main` — never a bare branch name; trailing = `Open` (ghost, external —
   the url the wire has) and, for a pending proposal, `Decide`.
   Sources of these rows, all real: PR entities with `reviewRequests`
   naming the owner or `reviewDecision` = CHANGES_REQUESTED aged by
   updated_at; CI on the base branch — NEW WIRE (counsel M1): a
   `branch_ci` query kind on the GitHub source (`gh run list --branch
   <base> --limit 1`, the conclusion + age), the default `CI` Watch
   the Door offers; Jira entities from the OVERDUE query; Delta
   proposals with review.pendingCount. Story 04 owns the new kind.
   Empty: ONE line, `Nothing needs you · next check 09:35` — no well.

3. **SOURCES** (caption + count). One row per Watch: lead emblem;
   primary the scope (`karolswdev/HoldSpeak`); cells the live counts
   as tokens (`12 OPEN PRS` `2 WAITING ON YOU` `CI GREEN`); secondary
   `checked 3 min ago`; trailing EgressChip host + hover verbs
   `Adjust` · `Pause`. A failing Watch: StateChip `⚠ CAN'T CHECK` and
   the reason in plain words on the secondary line (`Jira rejected
   the query` / `No local adapter for meeting activity yet`) with
   `Fix` (opens Adjust) or `Remove`. A `SUGGESTED` row (from meeting
   facts) sits last with `Add` — offered, never applied.

4. **SINCE YOU LOOKED** (caption + the last-read time token `WED
   09:21`). The read marker is SERVER-SIDE (counsel S3): today
   `readAt` is React local state that dies with the window; story 04
   adds a per-project read marker (one nullable column, additive) the
   Room writes when read. Grouped by source: a group line (`GitHub · 2 opened · 1
   merged`) over entry rows in phrases (`#618 opened by mira · 2 h
   ago`, `KAN-2 moved to In Progress · yesterday`, `Update drafted ·
   Tue`). Never a field name. Reading the Room moves the marker.

5. **DECISIONS & COMMITMENTS** — hidden entirely when empty. When
   present: rows `Decided · use acli for Jira · Tue` (from decision
   records) and `You owe · review PR #612 · by Fri` (commitments),
   EVERY row with `Open` (a row that can be acted on carries its verb). The project link (counsel M2): decision records have no
   project column; a project's decisions are the records whose source
   MEETING is linked to the project (the existing project ↔ meeting
   link the Room's meetings section already reads); commitments follow
   their decision. A query, not a column; when no meeting is linked
   the section is hidden. Story 04 owns it.

6. **Ask** — a well at the foot: `Ask this project…` with the mic; the
   model EgressChip (`MODEL · 192.168.1.43 LOCAL` or the assigned
   host) at the well's right; answers arrive as an aerogel inset above
   the well (rule 6), never a modal.

Footer: receipt `READ 09:21 · NEXT CHECK 09:35` · ghost `Refresh`.

HISTORY wing: the dated stream (SurfaceStream): day headers, entries
in phrases, a filter bar (LedgerFilterBar) by source; search is the
stream's typeahead. The day's count at display step in the stream
head (the one display fact of that face).

393: the head stacks (headline, outcome, chips, the verb full-width);
rows wrap; the ask well is sticky at the foot.

## D5 — laws and counsel's hunts

Counsel's read (2026-09-04): RATIFY-W-C — M1 CI wire, M2 decisions' project link, M3 mic shape; S1 glyph, S2 picker counts, S3 read marker, S4 outcome twice; N1 head hosts, N2 box-vs-hairline rows defensible (controls vs facts), N3 Create without Review lawful (the rows are the points of decision), N4 SUGGESTED row documented. All M+S paid on the design and the artboards before the owner saw it.

- The count is the test: creation never asks for a Test; a scope
  whose count cannot be fetched still creates, and the Room's source
  row says why (Article VI).
- Egress exactly where egress happens: every source row and the ask
  well carry the host chip; the Door's footer egress slot stays
  empty on purpose.
- Offered, never applied: known scopes, suggested sources.
- No credential crosses the face (168 D8).
- Every empty state is one true line with the next time something
  happens; no empty wells; no counters of zero.
- The name is said once per face (the title bar carries it; the head
  repeats the outcome only when the title bar cannot show it whole).
- The MicButton is the library's square (never round); the meeting
  emblem is `▣` (the glyph vocabulary in tools.ts); a source row
  counts as a SOURCE only once it has a scope (the Door's label and
  receipt count scoped rows).
- Counsel hunts: a chip the wire lacks (the health derivation must
  name its inputs); a verb that is not a library Button; a sentence
  in the UI beyond the copy above; a face collapsing to one type
  step; an accent left rail; a modal; a Test path that compiles a
  different query than the Watch (168's scar); a "since you looked"
  that has no read marker on the wire (a build need, not a face
  promise).

## D6 — the artboards (both widths; the sources are .dc.html on the 168 shell)

1. Door · connected · picked (GitHub + Jira, counts live)
2. Door · picker open (GitHub repositories, known scope first)
3. Door · cold (both providers Sign in / Connect)
4. Door · 393 (connected · picked)
4a. Door · first open (nothing typed, nothing picked; Create disabled)
4b. Door · checking (the moment after a pick)
4c. Door · Adjust open (GitHub: base branch, labels, drafts)
5. Room · needs you (3 rows; sources 2 + 1 failing; since you looked; decisions present)
6. Room · nothing needs you (fresh project: counts live, since-you-looked empty line, decisions hidden)
7. Room · 393 (needs you)
8. History · 1440

The owner ratifies the canvas before any build. Counsel reads it
first (the hunts above). The build brief hands workers these sources
and the species names; the rig asserts every step at both widths.
