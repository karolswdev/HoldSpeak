# The Power-User Usability Doctrine — HoldSpeak DeskOS

**Status: PROPOSAL — awaiting the owner's ratification sitting.**
Commissioned by the owner mid-Phase-111 ("ask an isolated Fable agent
on how to make the usability of the entire thing absolutely,
maximally amazing for power users"). The doctrine (§1) is written to
be ratifiable as project canon; the findings (§2) and gap map (§3)
route into Phase 111 stories and drafted charters. P0 palette/ledger
riders were folded into HS-111-07/08 the same day; the rest awaits
the sitting.


Isolated fresh-eyes review, 2026-08-01. Method: live desk walk at
1440x900 and 393x852 (screenshots in `.tmp/usability-shots/`), keyboard-
only probes on the real hub, and a full code audit of `web/src`
(keyboard handlers, palette, focus, aria, affordances). Everything here
is measured against a keyboard-native architect using this as his daily
operating surface, and constrained by the Constitution (Articles cited),
the Signal Workbench material canon, and the Article XI / Phase-87
consent spine — nothing below recommends against them.

Already chartered and NOT re-recommended here: xterm.js terminal panes
(HS-111-11), desktop right-click NEW>/LAUNCH> (HS-111-07 rider),
debug-behind-RAW, the error-surfaces-never-overlap law, and the
interior refits of stories 05–10.

---

## §1 THE DOCTRINE

Ten principles, written to be ratifiable as project canon.

**1. Enter is the fastest verb.**
Any surface that takes a query — the palette, a filter, a ledger search
— runs its best answer on Enter. A query surface where Enter does
nothing is a dead end at the exact moment of highest intent. The Prefs
filter already honors this (`settingsPrefs.tsx:218-220` opens the top
hit); the ⌘K palette does not. The law: type, Enter, done — arrows are
for choosing the *second* answer, never for reaching the first.

**2. One registry of verbs; every invoker derives from it.**
Article II says UI is derived from primitives. Extend it to acts: every
verb the OS can perform lives in one registry (`desk/verbRegistry.ts`),
and the palette, the menu bar, the context menus, and the shortcut
sheet all derive from that one source. Today the palette runs on its
own parallel `DESK_TOOLS` list, so verbs the menu bar can do are
unreachable from ⌘K. A verb that exists in one invoker and not another
is a registry defect, not a styling choice.

**3. Arrows walk, Tab exits.**
Every ledger, grid, menu, and result list is ONE Tab stop with roving
arrow-key focus inside (wrap, Home/End, type-ahead where rows are
named). Tab moves between instruments; arrows move within one. A
100-row ledger that costs 100 Tab presses (the history ledger today) is
a keyboard tax no power user will pay — he will reach for the mouse,
and the OS will have taught him to.

**4. Every noun has an address.**
Article I already rules that routes are deep links that open the Desk
in the right state. Finish it: every meeting, settings module, agent
session, journal entry, and process is URL-addressable, and the address
is copyable from the object itself. An architect lives by references —
in commit messages, in notes, in another terminal. An object he cannot
link to is an object he must re-find by hand every time.

**5. The hands stay where they are.**
Article IV makes voice a first-class input; make it reachable without
reaching. The flagship capture flow (Speak's TALK) must be operable by
a held key from anywhere on the desk, not only by clicking a button.
Symmetrically, every text input takes the mic (the law already), and
every mouse-only press target is a defect. Measure flows in hand-moves:
capture-a-thought should cost zero.

**6. Undo outranks confirm.**
A two-step confirm protects against the first click; it does nothing
against the second. Destructive acts on user data (delete row, clear
journal, delete records) are soft for a window and reversible from the
receipt bar — the receipt IS the undo affordance (Article V.2: the
audit is part of the act). Confirm-only deletion is permitted solely
where reversal is physically impossible (revoking a grant, killing a
process).

**7. Attention rides one ladder and never leaves the desk.**
A needs-you item surfaces as: token in the ledger → count on the
program's dock chip → count on the bell → (optionally) the ambient
card. Every rung opens the same in-world surface; no rung may reload
the page or navigate to a feature-owned screen (Article I.3). A blocked
agent that is invisible until its window is opened has fallen off the
ladder.

**8. Operating state is a register, not a memory.**
Filters, search scopes, and view modes are visible as tokens while
active and persist across window close/reopen, exactly like window
rects already do. The operator must never wonder "is a filter on?" —
the register says so — and never rebuild a filter he built an hour ago.

**9. Selection is plural, and verbs scale to N.**
Every ledger supports range selection (Shift-click, Shift+arrows), and
every verb that accepts one object states what it does with N —
export N, delete N, ask-about N. A multi-select whose only consumer is
Ask context, and an Object menu that goes dead at two selected items,
teach the user that selection is decorative.

**10. One grammar, finished everywhere.**
The phase-110/111 work is right: one search species, one footer
receipt bar, one composer, one menu vocabulary, one empty-state
species. This doctrine adds the enforcement clause: a surviving second
species is a P1 defect with a named owner, not ambient debt. (The
current survivor census is §2 F13–F16 and the Phase-111 stories 05–08
are the vehicle.)

**11. Keys are law, and the sheet is the statute book.**
Every shortcut lives in the registry (verbRegistry `key?` field —
built, currently populated by zero verbs), is rendered beside its verb
in menus and the palette, and appears in the ⌘/ sheet automatically.
A hand-maintained sheet drifts; a derived sheet cannot.

**12. Accessibility is the power interface.**
Roving focus, real roles, live-region receipts, and visible focus are
not compliance — they are what makes the OS drivable blind at speed.
The no-modal law (Article VII.2) already forbids focus traps; the
counterpart obligation is that every capability reachable by pointer
(resize, reorder, press-a-row) has a keyboard and AT equivalent.

---

## §2 FINDINGS (severity-ranked)

Legend: P0 blocks flow daily · P1 friction every session · P2 polish.
Shots referenced from `.tmp/usability-shots/`.

### P0

**F1 — The palette ignores Enter.**
Evidence: shots `04-palette-query-meeting.png` vs
`05-palette-after-enter.png` (identical — Enter consumed nothing);
`DeskToolShelf.tsx:268-285` (arrow-walk only, no default selection, no
Enter dispatch, no wrap, no Home/End).
Flow: every launch/find — the single most-used keyboard path in the OS.
Today: ⌘K → type → **ArrowDown → Enter** (and the arrow walk starts
from the input, clamped, non-wrapping). Muscle memory from every other
launcher on earth (⌘K → type → Enter) lands on nothing.
Fix: maintain a highlighted top result (aria-activedescendant), Enter
activates it; wrap the walk; Home/End. ~30 lines in `DeskToolShelf`.
Doctrine 1. Lands in HS-111-07 (system chrome owns the palette).

**F2 — ⌘K is a launcher wearing a palette's keybinding.**
Evidence: `DESK_TOOLS` static list `DeskToolShelf.tsx:16-106` is a
second registry parallel to `desk/verbRegistry.ts`; menu-bar verbs
(`desk.new-note`, `object.edit`, `object.ask-project`,
`verbRegistry.ts:48-125`) are unreachable from ⌘K; the Prefs deep-
setting index (`settingsPrefs.tsx:168,198-203`) and the meetings
server-side search (`HistoryCore.tsx:814-815`) are likewise invisible
to it. Matching is naive substring `.includes` with fixed section
order — no fuzzy, no ranking, no frecency, no recents
(`DeskToolShelf.tsx:181-248`).
Flow: "do X without touching the mouse" for any X that isn't one of 11
tools; "jump to that setting"; "find that decision by content".
Fix: palette consumes verbRegistry (verbs section), the Prefs deep
index (settings section with module deep-open), and object-content
search endpoints; add token-prefix ranking (verb: `>`-style sections
are optional; ranking is not) and an MRU head.
Doctrine 2. Lands in HS-111-07, and it is the biggest single lever in
this report.

**F3 — Ledgers are Tab-only; no roving focus anywhere in the kit.**
Evidence: `SurfaceLedger` is a bare div, rows are individual tab-stop
buttons (`Surface.tsx:550-615`); history ledger renders up to 100 rows
(`HistoryCore.tsx:943-1099`); `GadgetTable` navigation is native Tab
order only. The codebase's own comment knows the cost: "the shelf was
Tab-only, which buried distant results behind many keystrokes"
(`DeskToolShelf.tsx:264-267`) — the fix was applied to the shelf and
never to the ledgers. Live probe: Tab×3 + ArrowDown×2 in Meetings left
focus on the menu bar (`13-meetings-arrow-probe.png`, activeElement =
`desk-verbbar-title`).
Flow: find-a-decision, approve needs-you rows, walk the journal, walk
the crew board — every archival flow, every session.
Fix: roving arrows + Home/End + wrap in `SurfaceLedgerRow` handling
(one component; Meetings, Journal, Agents, needs-you GadgetTable all
inherit). Add first-letter type-ahead for titled rows.
Doctrine 3. New story (see §3 G1) — this is kit work, not one
program's interior.

**F4 — No undo anywhere; two one-confirm mass wipes; one no-confirm delete.**
Evidence: zero undo infrastructure in `web/src` (no history stack, no
⌘Z handler; global grammar is only ⌘1-4/⌘W/⌘M/⌘/,
`DeskWindow.tsx:1404-1445`). "Clear all?" wipes the entire journal
(`DictationCore.tsx:1169-1174`); DELETE all activity records behind a
single ConfirmVerb (`ActivityCore.tsx:141-143`); `GadgetTable` row `×`
deletes with no confirm at all (`gadgets.tsx:387-395`).
Flow: any edit session; one arming mis-click from unrecoverable loss of
the device's dictation history.
Fix: soft-delete with a receipt-bar reversal token (`DELETED · UNDO`,
15s or until next act) for row deletes; journal/activity mass-clear
becomes export-then-clear or a typed-count confirm. Receipt-as-undo is
Article V.2-native.
Doctrine 6. New story (§3 G2).

### P1

**F5 — The menu bar's dropdowns draw UNDER windows.**
Evidence: shot `14-menu-desk.png` — the Desk menu ("New Note / New
Knowledge…") is clipped by the Speak window title bar.
Mechanism: `DeskMenuBar` renders `DeskMenuList` inline
(`DeskMenuBar.tsx:55`, no `createPortal`) inside the chrome band,
which is `--desk-z-chrome: 30`, "UNDER windows by design"
(`styles/tokens.css:227-228`); windows start at 42. The palette had
this exact bug and fixed it by portaling (`DeskToolShelf.tsx:300-303`);
`--desk-z-transient: 81` exists precisely for open chrome transients
(`tokens.css:230`) and the menu bar doesn't use it.
Flow: every menu-bar act while any window is open — i.e. always.
Fix: portal the open `DeskMenuList` to the desk root at
`--desk-z-transient` (same pattern as the shelf). ~10 lines.
Lands in HS-111-07.

**F6 — No global talk key: the flagship capture flow needs a pointer.**
Evidence: `TransportKey` is `onClick` only (`gadgets.tsx:505-517`);
TALK in the deck has no keyboard binding beyond focused-button Space;
the welcome flow DOES have hold-Space-to-dictate
(`FirstWords.tsx:202-213`) — so the pattern exists and the daily
surface lacks it.
Flow: capture-a-thought — the product's headline flow. Cost today:
⌘1, Tab to TALK (or click), activate, speak, activate again.
Fix: while the Speak window is front, hold-Space = TALK held (with
`!typing` guard and `!event.repeat`, exactly as FirstWords does);
stretch: a desk-global push-to-talk chord (e.g. hold ⌥Space) that
raises Speak and arms capture. Voice arms, human confirms — unchanged
(Article IV.2).
Doctrine 5. Lands in a rider on HS-111-02's surface via story §3 G1 or
02 follow-up.

**F7 — Needs-you attention falls off the ladder.**
Evidence: (a) no dock badges — `Dock` never reads `launcher.badge`
(`DeskWindow.tsx:1394-1601`), deliberate per `DeskChrome.tsx:23-24`,
so a BLOCKED coder session shows nothing on the Agents chip; the count
exists only inside the window (`CompanionCore.tsx:133`). (b) The
ambient card's "Review source" does a hard
`window.location.href = detail_url` (`AmbientLayer.tsx:219-221`) — a
full SPA reload out of the desk, an Article I.3 violation in spirit.
(c) Processes' decision row is a fake anchor `href="/#attention"` to a
route that doesn't exist, saved only by preventDefault
(`ProcessCore.tsx:64-74`). (d) The bell shows one undifferentiated
count (222 in the live walk — shot `01-desk-1440.png`) mixing stale
object attention with actionable needs-you.
Flow: approve/deny — the consent spine's human half. If the human
can't see the ask, the spine stalls.
Fix: per-app dock chip counts for actionable items only (BLOCKED
sessions on Agents, needs-you on Meetings); ambient card routes through
`openSurface`; bell splits ACTIONABLE vs FYI as two tokens.
Doctrine 7. Dock/bell = HS-111-07; AmbientLayer fix is a quick win
(§4 Q4).

**F8 — Window management has no keyboard beyond close/minimize/one-way cycle.**
Evidence: `Ctrl+\`` always promotes the least-recent (`ids[0]`,
`DeskWindow.tsx:1463-1474`) — no reverse (`⌃⇧\``), no held-modifier
ring like Alt-Tab; no keyboard zoom/maximize; no keyboard restore of a
minimized window (⌘M is one-way — restore needs a pointer or ⌘1-4,
which only covers the four apps, not process/delivery/pullout windows);
no keyboard move/resize (grip is `aria-hidden`, pointer-only,
`DeskWindow.tsx:606`); no snap/tiling of any kind — the live walk shows
Speak+Meetings+Agents+Settings all overlapping in one pile (shot
`010-app-settings.png`).
Flow: steer-a-coder-while-reading-a-meeting; any two-window compare —
many times a session.
Fix: `⌃⇧\`` reverse; ⌘1-4-style focus for non-app windows via the
cycle strip staying open while ⌃ is held; keyboard snap verbs (left
half / right half / zoom) as registry verbs so they land in palette +
menus for free (Doctrine 2). Snap physics are an Article VIII.2
contract addition — new story (§3 G3).

**F9 — Deep links stop at meetings; settings modules, sessions, and layouts have no address.**
Evidence: meeting deep link works (`/history?meeting=<id>`,
`routes.tsx:45-56`, `HistoryCore.tsx:774-782`); settings modules have
none (only `integration:destinations` and `guide` aliases,
`SurfaceWindows.tsx:264-273`; `PREF_MODULES` unreachable by URL);
agent/coder sessions none (`shell.ts:82-91`, in-process only); window
layout is localStorage-only (`SurfaceWindows.tsx:220-259`).
Flow: "link this setting in a note", "reopen the session from the PR
description", cold-start into a working arrangement.
Fix: extend the demoted-route table: `/settings?module=hotkey`,
`/companion?session=<id>`; add "Copy link" to the window head menu for
any addressable subject.
Doctrine 4. New story (§3 G4).

**F10 — Multi-select exists but only feeds Ask, and the menus go dead at N=2.**
Evidence: `toggleSelected` one-at-a-time (`store.ts:857-863`); the
only checkbox UI is desk list view labeled "Select … for Ask context"
(`DeskListView.tsx:148-154`); no Shift-range anywhere (`shiftKey` used
only for Enter-vs-newline); Object menu computes
`selectedRef = selectedIds.length === 1 ? … : null`
(`DeskMenuBar.tsx:21`) so every object verb vanishes with two selected;
Meetings/Journal/Agents ledgers have no selection model at all; no
bulk export (single-record only, `HistoryCore.tsx:896-910`), no bulk
delete between "one" and "all".
Fix: Shift-click/Shift+arrow range select in ledgers and list view;
verbs declare N-arity in the registry; export/delete accept N.
Doctrine 9. New story (§3 G5).

**F11 — Seven search boxes, three species, two apply-contracts, zero persistence.**
Evidence table in the affordance audit: `StringGadget` live-apply
(Meetings `HistoryCore.tsx:948`, Journal `DictationCore.tsx:1163`,
Prefs `settingsPrefs.tsx:213`) vs raw `<input type=search>` (⌘K shelf
`DeskToolShelf.tsx:332`, Project memory `ProjectMemoryCore.tsx:616` —
Enter-submit) vs legacy `Field`+`TextInput` (Activity
`ActivityCore.tsx:148-156`) vs form-submit-only (AttentionDrawer
`:84-113`). Placeholders: "FILTER" / "search" / "Search". All filter
state is `useState`, reset on window close (`HistoryCore.tsx:783-799`);
Meetings' active filters hide behind a collapsed panel with only a
`· FILTERED` footer token (`HistoryCore.tsx:786,1269`).
Fix: one `LedgerFilter` species (StringGadget + mic + live-apply +
Enter-opens-top-hit), filters persisted per-surface next to window
rects, active filters rendered as removable tokens in the ledger
controls row.
Doctrine 8, 10. Lands in HS-111-08 (one kit) + the persistence bit in
§3 G6.

**F12 — The mic law has ~18 open violations, clustered exactly where the refit hasn't reached.**
Evidence (worst first): the ⌘K search input — the most-used input in a
voice-first OS (`DeskToolShelf.tsx:332-338`); the SystemShade
deny-reason free-prose field written TO an agent
(`SystemShade.tsx:120-126`); InlineEditor's recipe System prompt /
User template / Tools / Role / Tags / workflow params
(`InlineEditor.tsx:162-315`); CommandsCore keyword/payload
(`CommandsCore.tsx:213-272`); WorkbenchCore prompt/material
(`WorkbenchCore.tsx:395-419` — while the same "material" field in
`Pullout.tsx:715-730` HAS a mic: same need, two answers); CadenceCore
loop-reply (`CadenceCore.tsx:162-169`); AttentionDrawer filter
(`:93-96`); InfoWindow rename (`:44-58`).
Fix: mechanical — `StringGadget`/`MicButton` adoption; belongs to
HS-111-08's "every control type" charter; add a lint/test that any
`<input type=text>`/`<textarea>` outside the kit fails the suite
(Article IV.1 enforcement).

**F13 — Three conversation grammars still alive.**
`SurfaceTraffic` (Ask `AskPanel.tsx:327-448`, PersonaChat) vs the coder
session's raw `<pre className="desk-session-pane">`
(`SessionPullout.tsx:703-711`) vs the delivery terminal's own composer
with a `⏎` toggle chip (`DeliveryTerminalWindow.tsx:88-109`). Also two
send-contracts: Enter sends in Ask (`AskPanel.tsx:465`) but ⌘Enter
sends in Pullout (`Pullout.tsx:495`), and PersonaChat's composer is a
single-line `<input>` (`PersonaChat.tsx:310-314`) while Ask's is a
textarea. Survivors for HS-111-05/06 to kill — named here so they
don't slip: session pane grammar (06/11 will replace with xterm),
delivery composer (06), Pullout ⌘Enter (05), PersonaChat input species
(05).

**F14 — Five footer-bar species plus one program with none.**
`surface-receiptbar` (Meetings/Live) vs `prefs-status` (Settings —
including a permanently disabled DEFAULTS button,
`settingsPrefs.tsx:335-342`) vs `speak-status` `<p>` (Speak) vs
`desk-ask-foot` without an EgressChip on the one surface most likely to
egress (`AskPanel.tsx:566-591`) vs `desk-pullout-foot` (Sessions shows
two stacked footers, `SessionPullout.tsx:720,741`); Processes has no
footer and states status at the TOP (`ProcessCore.tsx:107-115`).
Fix: one footer species with the fixed slot order
`EgressChip | receipt | verbs` desk-wide; Ask gets its egress chip.
Lands across HS-111-05/06/08; the Ask egress chip is also a §4 quick
win (Q6) because it is an Article III.2 honesty gap, not just styling.

**F15 — Two menu vocabularies and a menubar that isn't a menubar.**
`DeskCreateMenu` hand-rolls the popover/escape/roving instead of using
the declared one-menu primitive (`DeskCreateMenu.tsx:30-110` vs
`DeskMenu.tsx:1-5`); the menu bar has no ArrowLeft/Right between
Desk/Object/Go and no arrow-open (`DeskMenuBar.tsx:40-53`) — Tab-only,
unlike every OS menubar since 1984. Lands in HS-111-07.

**F16 — Empty/error/loading states diverge, and Agents shouts.**
Kit `SurfaceState` sentence-case ("Nothing here yet", "No dictations on
this device") vs Agents' hand-rolled uppercase `"NO SESSIONS · NO ONE
WAITING"` where loading, error, and empty share one slot
(`CompanionCore.tsx:142-177`); Processes has no empty state at all
(`ProcessCore.tsx:116-136`); strays: `<p class=quiet>Empty</p>`
(`ZoneWindow.tsx:123`), `PrReceiptsSection.tsx:77`. One species, and
errors must teach (Article V.3: refusal by name) — an error state that
renders in the empty slot refuses namelessly. Lands HS-111-08.

**F17 — Clipboard and export are afterthoughts outside Speak/Meetings.**
No copy on an Ask answer (`AskPanel.tsx:566-591`), a persona turn
(`PersonaChat.tsx:261-294`), a meeting transcript, or a session pane
(bare `<pre>`, `SessionPullout.tsx:709-711`). Export exists only as
meetings single-record MD/TXT/JSON/SRT (`HistoryCore.tsx:898-910,
1273-1300`); no journal export at all — the only exit for dictation
history is row-by-row copy or destruction. Fix: COPY verb on every
transcript/turn/artifact surface (kit-level, HS-111-08); journal export
MD/JSON on the Speak footer (§4 Q5).

### P2

**F18 — Palette focus not restored on click-outside or ✕ close**
(`DeskToolShelf.tsx:158-171, 259-262` — only Escape restores). Ten
lines.

**F19 — `verbRegistry.key` is built and empty.** The menu bar renders
`v.key` beside labels (`DeskMenuBar.tsx:76-78`) and no verb defines
one (`verbRegistry.ts:29,48-140`) — the shortcut-hint affordance ships
dark. Populate as shortcuts are ratified (Doctrine 11).

**F20 — Escape is ~20 independent listeners.** Layering mostly works
(capture-phase discipline in `WorldStage.tsx:130-143`,
`DeskMenuBar.tsx:31`) but there is no single escape-ladder authority;
two composers even block Escape while busy (`PersonaChat.tsx:96`,
`AskPanel.tsx:149`). Consolidation candidate when HS-111-07 touches
chrome.

**F21 — ⌘1-4 fire while typing** (no `typing` guard on the app keys,
`DeskWindow.tsx:1414` — guard exists for ⌘W/⌘M). Mostly harmless
(browser tab muscle memory conflict) but inconsistent; add the guard.

**F22 — Mouse-only press rows** in GroundingSection
(`GroundingSection.tsx:207-210, 348-351`) and RailsPicker
(`RailsPicker.tsx:151-159`) — clickable divs, WCAG 2.1.1; the inner
CheckGadget saves them from total inaccessibility. The remedy pattern
already exists at `Surface.tsx:770-787`.

**F23 — The palette is `role=region`, not combobox/listbox** — no
result-count announcement, no active-option for AT
(`DeskToolShelf.tsx:310`). Fold into F1's fix.

**F24 — Desk icon grid: no arrow-key navigation or type-select** on
the icon plane (Tab-only via the a11y mirror), and the live desk shows
four objects named "The context envelope ships…" and four "The
grounding cap stays at…" (shot `01-desk-1440.png`) — truncation makes
siblings indistinguishable at grid density; the list view
(`?view=list`) is the workaround but isn't reachable by keyboard
shortcut. Icon-plane arrows + a title-disambiguation rule (front-load
the differentiator) — backlog.

**F25 — 393 ergonomics:** stacked full-width windows with no window
switcher other than scroll (shot `21-speak-393.png`); dock hidden on
the dictation route at 393. Held per web-desk-is-the-spec, but note
hit targets and the switcher before any mobile pass.

---

## §3 THE POWER-USER GAP MAP

Each missing affordance → where it lands.

| Gap | Landing |
|---|---|
| Palette: Enter-runs-top-hit, ranking, MRU, verbs from verbRegistry, settings deep-index, content search (F1, F2, F23) | **HS-111-07** (system chrome owns the palette) — expand its charter with one line: "the palette is a verb palette: one registry, Enter runs the top hit." |
| Menubar dropdown z-order portal; menubar arrow-roving; DeskCreateMenu onto DeskMenu (F5, F15) | **HS-111-07** |
| Dock chip counts for actionable attention; bell ACTIONABLE/FYI split (F7) | **HS-111-07** (chrome) |
| One filter species + one footer species + one empty-state species + mic-law sweep + COPY verb everywhere (F11, F12, F14, F16, F17) | **HS-111-08** (interactive elements — already chartered as "one kit, one language"; this report supplies its checklist) |
| Session pane / delivery composer conversation grammar (F13) | **HS-111-05 / HS-111-06 / HS-111-11** (already chartered) |
| **G1 — The keyboard grammar, part II** (new story): roving focus in SurfaceLedger/GadgetTable (F3), hold-Space TALK on the Speak deck (F6), ⌃⇧` reverse cycle + keyboard restore of minimized windows (F8 part), ⌘1-4 typing guard (F21), populate verbRegistry.key + sheet derives from registry (F19, Doctrine 11). Charter: *"Every act on the desk is reachable and repeatable without the pointer: ledgers walk by arrow, TALK holds by key, windows cycle both ways, and every ratified key is printed in the sheet from the one registry."* | **New Phase-111 story** (fits the phase: it is interior refinement of the interaction layer) |
| **G2 — Undo outranks confirm** (new story): soft-delete + receipt-bar UNDO for row deletes; typed-count or export-first for mass wipes; kill the unconfirmed GadgetTable `×` (F4). Charter: *"No user datum dies from two keystrokes: deletions are receipts with a reversal token for a named window; mass wipes cost proof of intent; Article V.2's receipt becomes the undo affordance."* | **New story** (kit + per-program adoption) |
| **G3 — Window physics: snap and the ring** : left/right-half snap + zoom as registry verbs; held-⌃ cycle ring with reverse (F8). Charter: *"Two windows side by side is one chord, not eight drags: snap verbs join the registry (palette, menus, keys derive), and the cycle strip becomes a held ring, forward and reverse. Article VIII.2 gains 'snap' as a contract."* | **New story** (or backlog until after 111 — but the two-window compare is daily) |
| **G4 — Every noun has an address**: `/settings?module=`, `/companion?session=`, Copy-link on the window head menu (F9). Charter: *"Article I.3's deep links finish the roster: every settings module, agent session, and addressable subject has a URL, and every window can hand it to you."* | **New story** (small; could ride HS-111-07 as a rider) |
| **G5 — Plural selection**: Shift-range in ledgers/list view; N-arity verbs; bulk export/delete (F10) | **Backlog** (post-111; needs verb-registry N-arity design first) |
| **G6 — Filter persistence + filters-as-tokens** (F11 second half) | **Backlog**, after HS-111-08 unifies the species |
| Desk icon-plane arrows + type-select; disambiguating titles (F24) | **Backlog** |
| Journal export (F17 part) | Quick win Q5 → HS-111-02 follow-up ledger |

---

## §4 QUICK WINS (each ≲50 lines, disproportionate daily payoff)

**Q1 — Enter runs the palette's top hit** (F1). Track an active index,
render it inverted, dispatch on Enter. The single highest
value-per-line change available.

**Q2 — Portal the menubar dropdown** to `--desk-z-transient` exactly as
the shelf does (F5). ~10 lines; kills a daily visual bug.

**Q3 — Roving arrows in `SurfaceLedger`** (F3). One keydown handler on
the ledger walking `.surface-ledger-row button`, wrap + Home/End;
every ledger in the OS inherits. (The full story G1 covers type-ahead
and GadgetTable; this is the 80%.)

**Q4 — AmbientLayer stops reloading the page**: replace
`window.location.href = detail_url` with the `openSurface` dispatch the
rest of the desk uses (`AmbientLayer.tsx:219-221`), and fix the fake
`/#attention` anchor in `ProcessCore.tsx:64-74` to a real button.

**Q5 — Journal export**: MD/JSON download verbs on the Speak footer
reusing Meetings' `download()` helper (`HistoryCore.tsx:178-186`).
Ends the "copy row by row or destroy" regime.

**Q6 — EgressChip on the Ask footer** (`AskPanel.tsx:566-591`): the
surface most likely to leave the device is the one missing the badge —
Article III.2. One component drop-in.

**Q7 — Mic on the ⌘K search input and the SystemShade deny-reason
field** (F12's two worst): two `MicButton` mounts.

**Q8 — `⌃⇧\`` reverse cycle**: same handler as `⌃\``, take `ids[ids.length-2]`
instead of `ids[0]`.

**Q9 — Dock chip attention counts**: `Dock` already receives
`useLaunchers()`; render `launcher.badge` on the matching app chip for
actionable classes (BLOCKED sessions, needs-you) — small, and it puts
the consent spine's asks where the eyes already are.

**Q10 — Restore focus on all palette close paths** (F18): call the
same `launchRef.current?.focus()` from click-outside and ✕.

---

*Shots: `.tmp/usability-shots/01…22`. Key evidence shots:
01 (desk + 222 bell + duplicate icon names), 04/05 (palette Enter
no-op), 06 (the full 11-shortcut sheet), 010 (four-window overlap
pile), 11 (exposé — good), 12 (cycle strip — good), 13 (arrow probe
dead in ledger), 14 (menu under window), 21 (393 stack).*
