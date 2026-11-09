# The UX Canon — what every face must do (ratified by the owner's rulings)

The Constitution is the supreme canon (docs/internal/CONSTITUTION.md),
and its Seven Tenets sit above every rule here: no over-engineering for
safety; not even pre-alpha; help and accelerate, never a million
interfaces; ASD-STE100 on every face; a component framework in the
manner of Intuition; Workbench 2.0+ on steroids; the first user is a
Senior Software Architect with reports.
DESIGN_SYSTEM.md is the material canon (tokens, the interior type
scale, the composition rules, the chrome ladder); the surface library
contract (web/src/desk/surface/contract.md) is the species canon. This
document is the FACE canon: the rules a Fedaykin must build to before
touching anything a user sees, gathered from the owner's rulings and
the scars of Phases 100–169. Where a face disagrees with this, the
face is wrong. Every rule names its ruling.

## The language, 2026-11-08

The owner, 2026-11-08: "Make the color scheme a little more refined please.
More contrast. Don't make it so bland." He rejected Space Grotesk, then
Bricolage Grotesque, Archivo and Schibsted Grotesk: "modern, but unique".
This section replaces the colour and display-face values below where they
differ. The tokens are in `web/design-tokens.json` (`--hs-*`).

- **Ink.** Words are `--hs-ink` `#10192b`; secondary words `--hs-ink-2`
  `#44536b`. A word is never a mid grey. Each text and ground pair is
  4.5:1 or more, 12 px labels too.
- **Six colours, six meanings.** Steel `#2b55a7`: ours, running; the primary
  Button. Brass `#b8800f`: waits on you; the ONLY warm colour. Moss `#1d7a4c`:
  done, on track. Coral `#c23a26`: at risk. Graphite `#4a5568`: parked,
  quiet. Navy `#0f1829`: the desk floor at night. Tints: steel `#d9e3f2`,
  brass `#fcefcf`, moss `#dff3e8`, coral `#fbe3df`. A colour as a word uses
  its ink token (`--hs-brass-ink`, `--hs-moss-ink`, `--hs-coral-ink`):
  brass, moss and coral are fills and marks, not small text.
- **Three material tiers.** Ground `#e6ebf3` (the window), plate `#f7f9fc`,
  raised `#ffffff` with `--hs-raised-shadow` (a soft drop and a 1 px top
  highlight). Title bar tint `#d9e3f2`, edges `#b3c0d3`, row lines `#d6dde8`.
- **No display face.** Titles, masts and the wordmark are the text face, Inter, by weight (600; the wordmark the one 700), size and tracking. Space Grotesk, Bricolage Grotesque, Archivo, Schibsted Grotesk and Fraunces were rejected by the owner on 2026-11-08: do not propose another display face.
- **Kind hues are cool.** A kind is a glyph seat, a row wash, a card rule
  and a kind word, never a state: project `#3460bf`, meeting `#16699a`,
  person `#176c5f`, decision violet `#6a4bc4`, note slate `#4a5d7a`, pull
  request `#226b40`, action plum `#8a3b86`, agent indigo `#3d3a9c`; a
  Program takes the steel of `--kind-other`. Each is 4.5:1 or more on the
  window ground. The floor glows and the zone tints are cool too.
- **State words take one table.** At risk, Blocked, Late, Overdue and
  Failed are coral ink; Done and On track are moss; Parked is graphite;
  Waits on you is brass. The table is `STATE_TONES` in the kit
  (`web/src/desk/surface/kit.tsx`); `DotWord` reads it, so a face does not
  pick the tone of a state word.
- **The brass Button** (`variant="brass"`) is the one verb that waits on
  him: a deep brass plate (`--hs-brass-deep`, white words 4.6:1) with a
  dark brass edge. One for each face.
- **The mast** (`Mast`): the object's sprite at 32 px, the title in the
  display face (24/28; 20/24 when the mast is under 560 px, by a container
  query, never a viewport query), one mono 12 px facts line in secondary
  ink, and the verbs as library Buttons.
- **The spine** (`Spine`): a 4 px bar under a mast or in an object row, in
  the meaning colours (steel, brass, moss, coral, graphite, idle), as
  segments or as one tone and a fill.
- **A glyph is always the desk's illustrated sprite**, never a coloured
  block.
- **Four motion words.** Settle 160 ms (a thing comes to rest), raise
  220 ms (a thing comes forward), breathe 1.6 s (a thing that waits on you),
  slide 200 ms (a thing moves on its track): `--motion-settle`,
  `--motion-raise`, `--motion-breathe`, `--motion-slide`. Reduced motion
  sets them to zero.

## Current material direction (owner, 2026-10-22)

“Workbench meets PopOS”: modernize the shared shell, not only Ask. The older
heavy Steel bevel, square frame and title hatching are historical treatments.
Fine borders, restrained rounding, soft depth and quieter sans controls now
express the same native Workbench framework. DESIGN_SYSTEM.md records this
owner amendment. All functional, readable, focus and pointer ownership floors
below remain binding. CLAUDE.md's latest fast cycle governs review: build the
direction on a canvas, then judge aesthetics live on the deployed desk.

## Owner direction — Icons D, flat Workbench (2026-10-24)

The owner called the tilted richer family "absolute cringe" and picked D
from the direction canvas: "Yes, I like D." This supersedes the 2026-10-22
construction below (shallow perspective, layered facets). Icons are front-on
flat silhouettes with two or three flat tones for each material, a navy
outline and a hard Workbench bevel (light top left, shade bottom right). There
is no gradient, perspective or tilt. A zone folder's front wears the zone's
colour. Three optical levels: 64, 32 (1 px bevel) and 20 (no bevel, heavier
outline) for dense rows and title glyphs. Title glyphs sit on a paper chip.
Rules, pipeline and parked family: betterment/ICONS-D-2026-10-24.md. The
2026-10-22 text stays as history.

## Shipped 2026-10-24 to 2026-10-27 (the window grammar week)

Recorded 2026-10-27 by the docs-currency lane so this canon matches the live desk.
Each line names the ruling, its canvas or design note, and the PR.

- **The window grammar (owner 2026-10-24: "still look like … pages inside
  OS-like containers").** Every window is title bar → one 36 px kit
  `Toolbar` → content edge to edge → one 24 px kit `StatusBar`. No page H1,
  no verbs floating in blank bands, no card in card; list rows 30–32 px;
  metadata quiet sans 12 px in sentence case; a state is a dot and a word
  (`DotWord`); mono only for code and ids; no dead footer. Design:
  `betterment/native-experience/WINDOW-GRAMMAR-2026-10-24.md`. Built
  #1457–#1472 (kit species #1459, Settings rail #1458, every manifest window
  by #1472), audited #1485 (`WINDOW-AUDIT-2026-10-25.md`).
- **Icons D (owner 2026-10-24: "Yes, I like D").** See the section above;
  `betterment/ICONS-D-2026-10-24.md`, #1468.
- **Egress at the act (owner 2026-10-25: the labels "feel like an ancient
  relic").** A.9 below as amended: no host, address or scope chip on rows,
  toolbars or status bars of working windows; disclosure only at the act
  (Send preview, Destinations, Engines, Accounts, Setup, the Door); a hover
  title on the verb is allowed. Inventory
  `betterment/native-experience/EGRESS-LABELS-2026-10-25.md`; #1481, #1489;
  guard `tests/unit/test_egress_labels_canon.py`.
- **The floating dock (owner 2026-10-26: "why is the bottom menu so ugly";
  picked direction 1 with D objects).** A centred slate-glass plate, 48 px D
  objects, no words under the icons (the name shows on hover and focus), a
  16 px count badge at the icon's corner, one tile per iconified window.
  Canvas `betterment/canvases/dock-direction-2026-10-26.html` (#1494); built
  #1497, #1498 (the floor runs under the plate). Open: the owner still
  rejects the dock icons live; the symbol set is the next offer.
- **The floor (2026-10-26).** The floor holds drawers, Projects and Notes
  only. The Talk orb and the Archive icon are gone; **Go ▸ Archive** and ⌘K
  open the Archive. #1495.
- **The Note (owner bundle e7524147, 2026-10-27).** It opens at 760 × 560
  with a one-row toolbar (Done, Ask about this, Find the tasks, Project ▾,
  Send…) and a one-line title, and renders its Markdown in place (live
  preview: headings, emphasis, lists and task boxes, links, code, quotes,
  tables) and Mermaid fences as diagrams. #1499, #1502; the workspace
  canvas `betterment/canvases/note-workspace-2026-10-27.html` (#1501) is the
  next design and is not yet ratified.
- **Settings ▸ Accounts (2026-10-27).** One paper, one label/control grid,
  dot-and-word states, one verb per row; Services, Calendar, Calendar feeds
  and Destinations on the same paper. #1491, #1503.
- **Programs (owner 2026-10-28: "a proper, well built-out … and well
  delightful software orchestration engine").** The Programs window
  (`surface-programs`, Go ▸ Daily and ⌃7: `Toolbar` with New program and the
  Templates `WorkMenu`, a banded `ListView` with `StateChip` and
  `countWords`, the `StatusBar`, `SurfaceState` empty with the program
  sprite) and the Program window (`pullout:program:<id>`: `Toolbar` with
  Control ▾ and the Agent: … ▾ picker as `WorkMenu`s and When idle as a
  `CheckGadget`; the Your turn well with library `Button` verbs; the board
  as `ListView` rows with the Programs' own `StationTrack` (dots, `Avatar`
  for a person station), `DotWord` states through `stateWords`; `FoldGadget`
  folds for Decided for you, Checkpoints and Gate (`SurfaceCode` for the
  command); `StringGadget`, `PadGadget`, `CycleGadget` and `Token` in
  Drafting; the place line and the "No project" `Token` in the
  `StatusBar`). Design `betterment/programs/PROGRAMS-DESIGN-2026-10-28.md`
  (the "Built" section names the faces' divergences), canvas direction C
  "the ledger" (`betterment/programs/CANVAS-NOTES-2026-10-28.md`), user doc
  `docs/programs.md`; the Programs PR.
- **Phone (owner 2026-10-28: "Do it. And definitely swallow the paradigm
  and 'vendor' it").** The desk reaches him on his phone (a message, or a
  call by rule at his control level and quiet hours) and he reaches the desk.
  The faces are kit only (design §9): Settings ▸ Calls ▸ Phone (Pair a phone
  with its QR, Reach you as Message · Call · Nothing per kind), Phone in the
  Calls window (the thread with a mic composer, the calls, the phones), the
  Needs you rows ("Asked on your phone", "Missed call", "Call you about …?",
  "No phone is paired") with library `Button` verbs, and the Reach line under
  a Program's Decided for you. A call is egress: it waits for his press at
  the act, in Needs you. Design `betterment/phone/PHONE-DESIGN-2026-10-28.md`
  (with "Built"), absorption `betterment/phone/ABSORBED-FROM-AGENTRING.md`,
  user doc `docs/phone.md`; the Phone PR.
- **The Line (owner 2026-10-29: "I'm choosing the second").** HoldSpeak's
  own phone line. Settings ▸ Calls ▸ Line, between Set up calls and Phone,
  kit only (canvas direction A, `betterment/line/CANVAS-NOTES-2026-10-29.md`):
  Where it runs (the place, its Engines word, its measured cost; on This Mac
  the own-venv install commands with Copy), The line (the free SIP address
  with Copy, or a Telnyx number whose password and key are write only:
  "Stored in your keystore" / "From the environment: move it to the
  keystore" / "Missing"), Test call (Ringing, then the result word), From
  Calls (read only), Adapter (The Line · ai-phone), egress once. The
  machine is named only there and as the hover title of Test call; the
  Calls window's status bar says Ready for calls, Line starting, Line not
  running, or No line: set one in Settings ▸ Calls ▸ Line (A.9). Design
  `betterment/line/LINE-DESIGN-2026-10-29.md` (with "Built"), recipe
  `betterment/line/RECIPE.md`, user doc `docs/calls.md` "The Line"; #1606,
  #1607, #1608 and the LINE-4b PR.
- **Program requirements, browse and adjust (owner 2026-10-31: "not that
  clear to browse, adjust … how to add additional requirements/checks, see
  how they are met").** Kit only, no modal: the Requirements board (canvas
  direction A, the checklist: 32 px `ListView` rows `R3 · DotWord · sentence
  · Token(kind) · scope · evidence · library Button verbs`, the Add
  requirement row), Find a program (`StringGadget` with mic), Project ▾,
  Person ▾ and Group ▾ (`WorkMenu`), the Met column ("4 of 5 met"; never "0
  of n"), the step fold with `FilterTokens`, the Ledger folded per step, and
  frozen fields drawn as text with their reason as the hover title. Design
  `betterment/programs/PROGRAMS-REQUIREMENTS-2026-10-31.md` (#1664), recipe
  `betterment/programs/RECIPE.md` "PG-REQ", user doc `docs/programs.md`; the
  PG-REQ PR.
- **The Program text and the change well (PG-LANG LANG2).** Board · Text
  (`FilterTokens`, in More ▾ at 393); the kit's `TextPane` (gutter lamp and
  mark, lamps at the line end, never in the value) and the `ChangeWell` of
  `DiffRow`s: Preview, Apply / Apply n, Not this, Apply this on a row that
  lowers the bar. Canvas direction S-A; `docs/programs.md` "The Program
  text"; #1670.
- **The shaping bar (LANG4, LANG5).** `StringGadget` "Change the program"
  with its one mic and Shape under the toolbar; "Reading the program ·
  engine" lamp; "Heard: …"; the ShapedWell with Overturn and Keep at YOLO.
  `docs/programs.md` "Shape it by a sentence"; #1673, #1675.
- **The planning draft (LANG7).** Plan it on the Drafting toolbar,
  "Planning · engine", drafted rows with size lamps ("7k of 32k", "Too big
  for … · 61k of 32k") and Split. `docs/programs.md` "Plan it from a goal";
  #1676.
- **The round strip (LANG10, direction R-A).** Ask me first; the strip of
  five rounds as `FilterTokens` with lamps; one `QuestionRow` at a time;
  answered questions as `QuestionFold`; Skip question, Skip round, Done
  with, Ask more. `docs/programs.md` "The interview rounds"; #1680.
- **The briefing page (DIR2, direction A).** `/b/<token>`, its own entry
  with the thin kit: the question first, 44 px library Buttons with what
  each does, Later ▾, the evidence folded and read only, the expired face
  with no data. Copy page link and Revoke on the rows, the row's line
  ("Page open until 06:30"), no chips. `docs/programs.md` "Decide from
  anywhere"; #1674.
- **Settings ▸ Reach (DIR6).** Notices renamed Reach: Channels, Pair
  Telegram with its code sheet, Bot token "Stored in your keystore", When
  to reach you, quiet hours, Digest and Later, egress said once. Needs you
  rows gain Later ▾ and Send ▾. `docs/reach.md`; #1678.

- **The Program window as one object (PG-WINDOW, direction A "the line
  and the note").** The program's station track at the top (one station per
  step and Done when; the held step and a running step breathe); what waits
  on him is the headline with no box: the brief in his terms
  (`brief_words.item_brief` on each `your_turn_items` row), the question in
  the display step, and the tray of library Buttons with each consequence
  under it as the one raised thing; the open step under its row with What it
  must prove (requirement lines, Add a requirement at the step), What the
  agent did (`story`, at most three plain lines) and its parts; Done when as
  the last row; the shape bar as the composer at the foot. The step rows lost
  the six grey dots. Canvas `betterment/programs/canvases/program-window-2026-10-31.html`,
  design `betterment/programs/PROGRAM-WINDOW-2026-10-31.md`; #1685, built
  #1688, Drafting and plain rows #1692.

- **The fold (owner 2026-11-01: "that left chevron something: fuck off.
  Invent something a lot clearer").** A section that opens in place draws no
  triangle and no chevron: its title and count on the left, the verb **Show**
  or **Hide** at the right, the open body under a hairline rule. The kit's
  `FoldGadget` and `Disclosure` and Today's folds draw it, so every fold on
  the desk changed at once. A Button that opens a menu (More ▾) keeps its
  caret. Canvas `betterment/canvases/fold-2026-11-01.html` (direction B),
  #1694, built #1695; fence `surface/__tests__/fold.grammar.test.tsx`.

## Shipped 2026-11-01 (Programs and Reach faces)

Recorded 2026-11-01 by the docs sweep (PG-DOCS-3). User words are in
`docs/programs.md` and `docs/reach.md`.

- **The Programs list (direction A).** Each row is one line in his terms and
  a mini track; Done stays Done when parked; a park with a reason folds
  under **Show** · **Hide**; the Programs a Program made fold under it. #1701,
  #1712, #1723.
- **The step report in registers (IMP1).** Checked, The agent says (marked as
  not checked by HoldSpeak), Not checked, Files; the finished mark. #1706.
- **The to-do row and the ending word (IMP2).** A Your word walk line is a
  row with **Done** and **Can't do it**. #1710.
- **Wait sentences (IMP3).** A waiting step and a list row say what they wait
  on in one sentence; Today starts with Since you were last here, one line a
  Program, a press opens it, nothing when nothing happened. #1713.
- **Take it over, hand it back (IMP6).** One Button each on a running step's
  row; "You have the lane"; neither asks first. #1718.
- **The family (IMP7).** Came from and It made under the board, plain rows.
  #1723.
- **The audit's faces.** "Reviewer only: nothing is written", "Reads …" on a
  step row, stations BRIEF · WORK · REVIEW · FILE, the Findings board with
  **Open Door task**; File, Make and the lesson rows in Your turn and Needs
  you. #1734, #1736.
- **The race in the Program window.** The contenders and the winner row
  ("Codex won the race · 34 min"); no Overturn on a winner. #1740.
- **A ledger row opens its record.** "Proposed as a decision" is a press
  that opens the decision. #1733.
- **The brief as a note (owner 2026-10-31: "didn't even make sense").** The
  brief is a chief-of-staff note in his terms; after his press it settles to
  one line; never a raw error or path as the question; no callout box, no
  left chevron. #1684.
- **One briefing page for several items (DIR9, DIR10).** Each item decided in
  place, its one line after the press, "1 waits on you." at the top; a send
  shows its preview (destination and lines) and goes from the page only; an
  agent's question is one text field with no microphone, because the page's
  thin kit is outside the desk and the phone keyboard has its own (named in
  `scripts/ux_canon_scan.py` `MIC_ALLOWLIST`); Door and blocker lines
  are plain text with no Buttons. A permission never goes to a page. #1703,
  #1708, #1735, #1739.
- **Settings ▸ Reach, the ladder (DIR7).** The rungs in order with their
  waits: Desk, Phone, Telegram, Call. #1704.
- **Today's Prepared block.** Plain rows, no address chip, no raw id, a
  chief-of-staff line. #1732.

## Owner direction — crisp illustrated icons (2026-10-22)

The owner rejected the first implementation as “toilet bowls” and too basic.
The next material pass uses richer desktop illustrations: shallow perspective,
coloured enamel, paper edges, metal facets, narrow seams and distinct object
construction. Folders have visible contents and coloured fronts; agents have
head-and-shoulder portraits. Avoid repeated white basins and hinged blue lids.
Small-size recognition still comes first. Settled correction and canvas:
betterment/RICHER-ICONS-2026-10-22.md. The first illustrated family is parked.

After reviewing the modern shell, the owner asked for better icons and chose
“Crisp illustrated icons” over minimal line or refined pixel icons. This
supersedes D1's hard-pixel medium, thick casing and nearest-neighbour sampling
for the shared app, object and Settings family. Workbench semantics and the
library framework remain. Use a strong recognisable object silhouette,
restrained colour, cool paper, rounded slate outlines and subtle depth.
Small icons remove fine detail and use a stronger optical outline. Labels,
selection, stale state, microphone state and app identities remain honest.
SVG originals are shared source; existing 64/32 PNG and real state-image
contracts remain compatible. DOM/GPU sampling is smooth for this family.
Scope and before-build canvas: betterment/ILLUSTRATED-ICONS-2026-10-22.md.
Owner aesthetic acceptance stays live and open.

## A. The owner's rulings (verbatim where he ruled)

1. **Every verb is the library Button.** A raw `<button>` in a face is
   a bounce ("Why is the edit button such a generic HTML button, but
   not a button of our design component library…?", 2026-09-04).
   Lead/primary splits are species bugs, fixed in the library.
2. **Design the face on the library, on the canvas, BEFORE build.** The
   owner ratifies artboards, not code ("HECK YES, a BIG YES to this",
   2026-09-03; "word", 2026-09-04). Then: **build what was ratified** —
   the artboard beside the shot every round (169's five rounds).
3. **No prose in the UI.** Tokens, verbs, counts, names. A sentence on
   a face is a defect; a helper paragraph is a bounce ("Walls of
   text…, complete disregard to our component", 2026-09-03). The one
   exception: an empty state is ONE true line with the next time
   something happens.
4. **No modals; edit in-world.** Wizards, pickers, Adjust, answers:
   wells that unfold under the row, or aerogel insets. A modal is a
   bounce.
5. **Streamlined means one screen where one screen will do.** The
   169 door: what was 17 face steps is 5 clicks. A plan of steps, a
   review page, a wizard with its own plan — each must earn its place
   against "will you use this on a Tuesday?" (Phase 139).
6. **A window's wings never leave the window** — titles shrink first
   (`min-width: 0` on every nowrap ellipsis title).
7. **The name is said once per face.** The title bar carries it; the
   head repeats the outcome only when the title bar truncates it.
8. **No counters of zero.** `0 Watches`, `REV 1`, `0 today` are bounces;
   omit the zero token or say the true thing (`CLEAR`, `Nothing today`).
9. **Egress where the choice or the act is made (owner ruling
   2026-10-25).** Owner, on a Today shot with `KAROLSANEAPPLE.ATLASSIAN.NET`
   chips on every Jira row: "I'm also pissed off at the ever-present
   'labels' (the LAN, the 192.168.1.36, the jira label as visible on that
   screen) - I know it was a core tenet of the entire app, but you know
   what? It feels like an ancient relic now..." The rule:
   - No host, IP address or scope word (LAN, CLOUD, LOCAL, REMOTE, MIXED)
     on the list rows, toolbars or status bars of a working window: Today,
     Needs you, the Room (Now, History, Prepare), Ask, Speak, Agents,
     Meetings, the drawers, Activity, Automations.
   - An engine is named by its name (`Codex`, `qwen3.8-27b`), with no scope
     word and no address.
   - Egress stays disclosed where the choice or the act is made: Settings ▸
     Engines and What runs where (the inspector may show the address), the
     Send preview and confirm before the press (the channel destination),
     Setup and the Door, the Processes window. There the address is a fact
     row, not a chip.
   - A press that leaves the device from a working window names its
     destination in its confirm or preview; a link, or a run whose route
     the owner chose in Settings, names it in the verb's hover title.
   Inventory: `docs/internal/betterment/native-experience/EGRESS-LABELS-2026-10-25.md`.
   Fences: `tests/unit/test_egress_labels_canon.py` and the desk sweep's
   `labels` fence.

   *Superseded 2026-10-25, kept for the record:* **Egress exactly where
   egress happens.** The host chip on the row that leaves the machine,
   never in a header for decoration, never missing where a fetch is
   triggered (Article III).
10. **Honest states, plain reasons.** `CAN'T CHECK · Jira rejected the
    query`, never a stack, never a smoothed-over green.
11. **A verb that does nothing is a lie.** Withhold it (and ledger it)
    rather than ship it dead; a section-level interim verb is honest
    when it opens a real face.
12. **Setup flows must be joyful** (2026-08-17): the first open is the
    most important face; a stranger must know what to do first without
    narration.
13. **Beauty pass after every functional pass; the owner sees shots
    before merge** (Workbench 2.0 directive).

## B. Core species a face composes from (never hand-rolled)

This is the core roster, not an exhaustive export list. The
[surface contract](../../web/src/desk/surface/contract.md) and its public
barrel define supported APIs. The Components desk window demonstrates
working patterns and controls; a local specimen does not establish live
adoption or owner acceptance. Update the matching specimen and contract
when a shared pattern changes.

Button (primary · ghost · dense) · StateChip (success · warning ·
failure · idle · unreachable; `●` for health) · EgressChip (the host;
only where the choice or the act is made, A.9)
· ProvenanceChip · surface-token[data-chip] · SurfaceLedger /
SurfaceLedgerRow (52px lead slot; hover verbs; `wrap`) · SurfaceSection
(caption + count) · SurfaceIdentity · SurfaceStream/Day/Entry ·
SurfaceWell · SurfaceFooter (egress · receipt · verbs; portaled — use
its `className` hook) · ChoiceCard/Group · CheckGadget (incl.
`variant="token"`) · StringGadget · CycleGadget · Disclosure ·
EditInPlace · MicButton (square; on every text input — the voice law)
· ScrollHint (every scrolling well announces itself) · LedgerFilterBar
· ProgressPlan (only for things that genuinely RUN). A recurring
element a face needs and the library lacks is ADDED to the library,
documented in contract.md, then used — never invented inline.

## C. The type steps (the interior canon)

display 26/600 `--font-display` — ONCE per face, the one big fact ·
primary 15/600 `--font-sans` — the thing's name · body 14 · secondary
12 mono — counts, times, hosts · caption 12 mono uppercase 0.06em —
section labels, chips. A face uses at least three steps; a face that
collapses to one is a defect (the geometry probe).

The four rules below are the type-scale ruling of 2026-09-21
(`docs/internal/checks/type-scale-ruling-2026-09-21.md`, §3). They
replace the earlier 11 px caption allowance.

- **The 12 px floor.** Readable text is 12 px or more. Captions, chips
  and verbs obey the floor. Only a nontext glyph goes below it, and
  only when a readable word or an accessible control name says the
  same thing. A word is not a glyph. A number is not a glyph.
- **The three roles by surface kind.** Display is the leading fact on
  a Chair face, an application face or an object face. Use it once.
  Use body and mono for editors, settings, lists, menus and chrome.
  Caption and secondary share 12 px; weight and letter-spacing keep
  them apart.
- **Contrast.** Small text makes 4.5:1 on the background that it is
  really on. The ink values are in "The language, 2026-11-08" above:
  secondary ink is `--text-muted` (`#44536b`, 6.5:1 on the window
  ground) and faint ink is `--text-faint` (`#56657c`, 4.9:1). A word is
  never a mid grey. A disabled control stays different through its
  disabled state and its flat treatment, not through gray alone.
- **Hit ownership at 393.** Each PLATED library Button — the Button
  that wears a face of its own — owns a 44 × 44 px area
  (`--desk-button-hit-size`). A transparent halo carries the area; the
  painted face keeps its height. Layout can grow. A clipped area is a
  defect, and two controls must not own the same point. Prove it with
  `elementFromPoint` and a real pointer at the center, the edges and
  the corners. A rectangle measurement is not proof.
  A chrome Button has no plate: it is a row in a strip (a menu row, a
  wing tab, a dock chip). A halo on it would reach over its neighbours,
  so the STRIP owes it the target: each such row is at least 44 px high
  at 393. Measure the row, do not add a halo.
  Two things are not defects here. A control under a window in front is
  occluded, and the layer order is correct. A halo that reaches under
  that window is covered, not clipped. Record both; fail neither.

## D. Grammar rules the scars taught

- One row grammar per species at both widths; the same object never
  drawn two ways (compose repeated things as one object).
- 393 stacks under a container query named `surface` (the desk's
  container; `surface-window` never matched) — never viewport media.
  ONE exception, and only this shape (HS-202-05): a DEVICE rule that
  sets a target size and stacks no content. The 44 px Button area is
  the only one. It lives in `web/src/styles/global.css` under
  `@media (max-width: 420px)`, and `global.css` is named in the
  allowlist of the container-query law
  (`web/src/desk/__tests__/containerQueryLaw.test.ts`). The reason is
  reach, not preference: the Dock, the menu bar, the Chair shell and
  the first-use pages sit outside every named `surface` container, so
  no container query can find them. Content layout still answers to the
  window, never to the viewport.
- A control that must be clicked LOOKS clickable (the beveled gadget
  with a stroke chevron), and an entry card carries its verb.
- Owning the body means UNMOUNT the rest; an inline wizard under other
  content is a scroll hunt.
- The empty first paint never happens: first paint carries the counts
  already fetched; sections rise in; idle never moves; reduced motion
  = instant. Four named motion moments per face at most.
- Empty slots never move their neighbours (the footer's egress slot).
- Filters are lightly raised tokens (the soft bevel, no plate); wings
  keep the full Steel bevel; the two never look alike (PHILO-14 B2, #958).
- One word, one meaning per face (176): the wing is the noun (LEARNED),
  the receipt is the act (TAUGHT), the chip is the fact (APPLIED); a
  chip renders only from a stored per-run fact, never a read-time
  "would match"; a count on a face is a real count of what it names
  (`N APPLIED` = firings; `N TODAY` = today).
- The species that has the value wins the face: a single-line field
  cannot wrap, so a value that must wrap at 393 is a PadGadget; the
  pick over a closed set is CycleGadget until a picker species exists;
  a chip that must sit inline is a library Button with a region, not
  Disclosure.
- A `mic={false}` on a gadget is a voice-law hole the raw-element count
  cannot see; the scanner counts per element with a reasoned allowlist,
  and one mic authority per face (Talk on the Speak face).
- A rig never types into the machine's focused window; the real landing
  is the owner's walk.

## E. The review protocol (how a face flips)

1. Artboards at 1440 + 393 on the ratified shell; counsel hunts the
   canon before the owner; the owner's word.
2. The build's rig asserts the ARTBOARD, not presence: type steps,
   token positions, no intersecting row children, the well in frame,
   an honest count, one display element; shots at both widths.
3. The orchestrator reads every PNG beside the artboard; a worker's
   "matches" is a claim.
4. Guards make the canon mechanical: no raw `<button>` in a face; no
   `border-left` accent rail; no emoji glyphs; no raw snake_case kinds
   on a face; no counters of zero in copy; the product-copy guard; the
   design-system token guard; the density guard.
5. The owner's walk on his desk, both widths, the window shot per
   step; his words verbatim; scars become laws here.

**Guards.** `tests/unit/test_ux_canon_ratchet.py` runs the canon
scanner (`scripts/ux_canon_scan.py`) against the live `web/src` tree.
The rules that are defects stay at zero: A1 (raw `<button>`), A4, A8
(a counter of zero), A9 (missing egress), DS6 (accent rail) and mic.
A hit fails the test and names the faces. The other rules (prose, raw
ids, emoji, B, C) are findings for the face lanes, not a gate. The
per-rule ceiling ratchet is parked (2026-11-09, the fences diet): it
had to be re-recorded on every face change. Every verb is the library
Button; a raw `<button>` is a species bug.

The review order is: read the shot, read
the artboard, then read the canon. A face that matches its artboard but
violates this canon is still wrong.
