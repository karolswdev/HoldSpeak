# Surface Library Contract (HS-156-03)

## Import path
Feature code imports from `desk/surface` (the barrel). Private paths are fenced.

## States vocabulary
The closed state set: idle, active, working, success, warning, failure, unreachable.
Every state renders icon + text; never color alone.

## Accessibility
- Composites (ChoiceCardGroup, ProgressPlan) use roving tabindex via useRovingRows
- Disclosures have button triggers with aria-expanded, content regions with aria-labelledby
- Popovers trap focus, dismiss on Escape
- Status updates use aria-live="polite" on transition only
- Radio groups use real input[type=radio] with proper grouping

## Tokens
All styling uses design tokens from design-tokens.json. Raw values are forbidden (validate-tokens.cjs enforces).

## surface-token[data-chip] (HS-167-05)
The chip variant of `surface-token` gives it the full chip geometry (border, well bg, etch shadow, 10px mono, 0.06em tracking) used by token rows (steward grant, run receipt refs). Stamp `data-chip` on any `surface-token` that should render as a discrete chip rather than inline text. Tone data-attrs still work.

## Motion
All transitions use --duration-* tokens and --ease-* curves. prefers-reduced-motion removes animation.

## Container behavior
Patterns respond to the surface container (@container surface). They push layout (in-flow); never overlay/modal.

## Composition
- ProvenanceChip and Receipt compose into SurfaceFooter's egress/receipt/verbs slots
- StateChip composes into SurfaceVerbs status slot and standalone
- ActionNotice is a standalone flow element
- ProgressPlan and ChoiceCardGroup are section-level patterns
- Disclosure wraps any content as a collapsible section

## ChoiceCardShell (HS-159)
The card visual language without an interaction model. Owns all `surface-choice-card-*` CSS classes: shell, head (emblem + label), description, summary anchor, fact chips, cost, fold (behind Disclosure), selected/recommended/disabled presence.
- `as` — wrapper element tag (default "div"); ChoiceCard passes "label", features may pass any semantic element
- `beforeHead` — content before the head (e.g. a visually-hidden radio whose `:focus-visible + .head` needs DOM adjacency)
- `selected` — stamps `data-selected` for the accent-wash selection presence
- `recommended`, `disabled` — stamp `data-recommended`, `data-disabled`
- `tier` — accent-temperature key stamped as `data-tier`
- `children` — rendered after the built-in slots, before the fold
- All extra props pass through to the wrapper element (role, aria-*, data-*, event handlers)
- ChoiceCard composes the shell internally (one source of material)

## SurfaceIdentity (HS-167-03)
The project orientation band: name (the Primary type step, 15px/600), chip row (wraps at the narrow container), optional purpose (folds past two lines via Disclosure), outcome as a target token row, optional fold body, trailing token (e.g. read time).
- `name: string` -- rendered at `--desk-type-primary-size`
- `chips: ReactNode` -- StateChips + tokens, one row, wraps
- `purpose?: string` -- one line, folds past two lines via Disclosure
- `outcome?: string` -- rendered as a target token row with a target mark
- `fold?: ReactNode` -- Disclosure body (additional content)
- `trailing?: ReactNode` -- right-aligned on the chip row (e.g. read-time token)

## SurfaceLedgerRow.trailing (HS-167-03)
A new prop: one quiet verb or a chevron, right-aligned after `cells`, its own grid slot (never overlapping the 52px time column). The grid extends to 6 columns when `trailing` is present (stamped via `data-has-trailing`).
- `trailing?: ReactNode` -- quiet Button or chevron
- `wrap?: boolean` -- when true, primary wraps instead of ellipsizing; at the narrow container cells fall under

## SurfaceVerbs.active (HS-167-03)
A new prop: the verb key rendered lit (`aria-current="true"` on the verb button, the verb bar stamps `data-active-verb` on the wrapper). The active verb gets the etched lit state (sunken well via `--desk-window-etch`). Count chips inside verb buttons use the `.surface-verb-count` class.
- `active?: string` -- the verb key rendered lit

## ScrollHint (HS-167-03)
Gradient edge fades for scrolling wells. ONE species with an `axis` prop. Promoted from DoorBoardLane.tsx (horizontal) and steward/model.ts (vertical); both copies replaced with barrel imports.
- `axis: "x" | "y"` -- fade direction
- `scrollRef: RefObject<HTMLElement | null>` -- the scrollable element (when null, falls back to wrapRef.parentElement)
- `className?: string` -- additional class on the wrapper
- Pure function: `computeScrollHint(scrollOffset, scrollExtent, clientExtent)` returns `ScrollHintState` ("none" | "start" | "end" | "both")
- Hook: `useScrollHint(wrapRef, scrollRef, axis)` -- attaches scroll/resize listeners, sets `data-scroll-hint` on the wrapper
- Fence: `computeScrollHint`/`computeVerticalScrollHint` must not be defined outside `desk/surface/`, `desk/chair/lanes/DoorBoardLane.tsx` (thin re-export), and `features/project-room/steward/model.ts` (thin re-export)

## DeskEditor (sanctioned non-barrel import)
`web/src/desk/components/DeskEditor.tsx` is the ONE sanctioned non-barrel import for feature code. It provides the rich text editor used by the Update posture. Feature code may import DeskEditor directly from `desk/components/DeskEditor` without going through the barrel.

## ChoiceCard object slots (HS-156-08)
A ChoiceCard is an OBJECT, not a list. Beyond label/description/facts/cost:
- `summary` — the one-line anchor the eye lands on (what this choice does, one breath)
- `emblem` — a tier mark beside the label, aria-hidden, colored by `tier`
- `tier` — accent-temperature key stamped as `data-tier` (library palettes: light/balanced/full; unknown keys fall back neutral)
- `fold` + `foldLabel` — per-item detail behind a Disclosure; clicks inside the fold inspect, they never flip the radio
- `facts` and `cost` render as chips, not rows
- ChoiceCardGroup `layout="row"` lays cards out as equal siblings where width allows (stacks narrow); RECOMMENDED renders as presence (accent wash + rail), not just a corner tag

## countToken / countLabel (HS-170-02)

- `countToken(n, singular, plural?)` → `"N NOUN"` or `null` at zero — the one way a face says a count (UX-CANON A8: no counters of zero). Render nothing (or the face's one true line) when it returns null.
- `countLabel(label, n)` → `"LABEL N"` at n>0, `"LABEL"` at zero — for section captions.

## FilterTokens (HS-176-03)

The flat one-tap filter strip: `role="group"` over library `Button` species,
one active at a time. Promoted from the composition ratified on the Project
Room's history wing (`ProjectRoomCore.tsx:1550-1566`) per canon B — a
recurring element the library lacked.

- `options: FilterTokenOption[]` — `{ value, label }`; the label is a
  caption-step word (`ALL`, `DICTATION`), never a sentence
- `value: string` — the active option's `value` (the caller owns the state;
  an empty string is the usual "no filter" wire value)
- `onChange(next: string)` — the one-tap toggle
- `label: string` — the group's accessible name (e.g. `"Source filter"`)
- `className?: string` — an extra class on the group span
- `options[].ariaLabel?: string` — HS-200-13: a per-token accessible name
  richer than its visible label (`Filter — Decisions` over `Decisions`),
  when the design names it; the visible word stays the caption-step token
- `disabled?: boolean` — Conductor R7: the whole strip (or its phone-width
  menu Button) takes the library `Button`'s disabled state; the pressed token
  still shows the held value. No prose explains it: a token beside the strip
  names what holds it (Settings › People: `SOURCE · HOLDSPEAK_MCP_PEOPLE_ACCESS`)

Presence rules (they are the species, not the caller's business):

- The active token is `Button` **secondary dense** (accent-tinted, raised),
  the resting ones **ghost dense**; each carries `aria-pressed` and the
  active one `data-filter-active`. Never **primary**: a face has one filled
  primary and it is the action the face is for, not a filter. No raw
  `<button>` (UX-CANON A.1).
- **No sparse rule — it never returns `null`.** A strip that vanishes on a
  short or empty list leaves no way to widen the view; it renders over an
  empty stream. This is the difference from `LedgerFilterBar`, which returns
  `null` below `SPARSE_THRESHOLD` (`LedgerFilter.tsx:104`, `sparse.ts:4`).
- **It carries no count.** `matchCount/total` would be a second count on a
  face that says its one count elsewhere (UX-CANON A.7/A.8).
- Not to be confused with `SurfaceWings`: filters are flat tokens, wings are
  the beveled strip, and the two never look alike (canon D).

### The strip menu form (PHILO-13-11, C1 §3a)

Strips of choices — `FilterTokens` and the window wings (`SurfaceWings`) —
obey one rule: nothing clips, nothing scrolls sideways (HS-200-12).

- At the phone width a strip that does not fit its row becomes ONE library
  `Button` (`StripMenuButton`, `stripMenu.tsx`): the current choice and ▾
  (`RANKED ▾`, `OUTCOMES ▾`), 44 px tall. It opens the DeskMenu species
  (`WorkMenu`) with every choice as a `menuitemcheckbox`, a check on the
  current one; a window's gear door joins after a separator. A keyboard
  press opens it with focus on a row.
- "Does not fit" is MEASURED (`useStripFit`): the strip folds when its
  content runs past its box or its choices wrap to a second line, and
  unfolds when the row is wide enough again. Never a fixed count; a strip
  that fits stays a strip. Where nothing can be measured (jsdom), it stays a
  strip.
- The desktop strip never folds.

## StringGadget.micLabel (HS-200-13) / PadGadget.micLabel (HS-201-12)

The text well's mic is the voice law (canon B: MicButton on every text
input). Its accessible name defaults to `Speak <label>`; a face whose design
names the mic (`Dictate into the search`, board P5Recall) passes `micLabel`.
The mic itself, its placement and its behaviour are unchanged — only the
name the screen reader says. HS-201-12 gave `PadGadget` the same prop with
the same default, so both text species answer to one rule (the Thought
window's answer pad names its mic `Speak your answer`).

## EditInPlace (HS-101 rule 1, documented HS-200-41)

The presented text IS the editor — data is the material, so there is no
separate "edit mode" chrome. Click or Enter swaps the presented value for a
same-geometry editor; Enter or blur commits, Escape reverts. Documented here
under canon B (a species in use is a species documented): it has been in use
across the product since HS-101 and appeared nowhere in this contract.

- `value: string` — the presented text; it is also the editor's seed
- `onCommit(next: string)` — fired only on a real, non-empty change
- `label: string` — the accessible name; presented state reads `Edit <label>`
- `disabledReason?: string` — a value that CANNOT be edited stays presented
  and names why (`aria-label` becomes `<label>: <reason>`). **Never a bare
  disabled input** — a dead field that does not say why is the bug this prop
  exists to prevent
- `multiline?: boolean` — textarea instead of input
- `mic = true` — every text editor carries the speak-to-fill mic (mic law,
  HS-111-08); pass `false` only where the host renders its own

## ConfirmVerb (rule 5, documented HS-200-41)

The inline two-step for a destructive verb: the first press arms, the second
fires, and arming self-disarms after 3 s. **Never a modal** (owner ruling: no
modals, edit in-world). Composes the library `Button` — ghost when resting,
`danger` when armed — so a destructive verb never needs a raw `<button>`.

- `label: ReactNode` — the resting label
- `confirmLabel = "Sure?"` — the armed label, in place
- `ariaLabel?: string` — a STABLE accessible name when the visible label is a
  glyph (×), so the control does not rename itself between the two presses
- `busy?`, `disabled?` — ride the Button's `loading` / native `disabled`
- `onConfirm()` — fired on the second press only

## TaskResume / TaskResumeList (HS-200-41)

The ratified `UNFINISHED` row: one piece of work the owner walked away from,
drawn so he can pick it back up. Promoted to the library BEFORE any face drew
it (canon B; story AC2).

`TaskResume` draws, in order: the purpose at the primary step, the state
chip, `SAVED HH:MM`, the recipe when it HAS one, the custody token, why it is
stopped, the Project button, and **ONE verb**.

- `purpose: string` — the work itself, said once
- `state: TaskResumeState` — `saved | running | waiting | failed |
  incomplete | accepted | discarded`. The state's chip tone, its word and its
  ONE verb are the species' business, not the caller's:

  | state | chip | default verb |
  |---|---|---|
  | `saved` | `SAVED HH:MM` (idle) | `Resume` |
  | `running` | `RUNNING` (working) | `Stop` |
  | `waiting` | `WAITING ON YOU` (active) | `Answer` |
  | `failed` | `FAILED · <reason>` (failure) | `Check` |
  | `incomplete` | `INCOMPLETE` (warning) | `Re-read` |
  | `accepted` | `ACCEPTED MM-DD` (success) | `Open` |
  | `discarded` | `DISCARDED` (unreachable) | — |

- `savedAt?`, `settledAt?` — ISO/epoch; formatted to `HH:MM` and `MM-DD`
- `recipe?: string` — drawn as `RECIPE · <name>`
- `projectName?` + `onOpenProject?` — the way back (design D2(g)); the button
  is a ghost `Button` named `Open the Project: <name>`
- `stoppedReason?: string` — the target's OWN words, quoted, never composed
  by the face (ruling B5). Inside the chip on `failed`, its own token
  otherwise, and never in both places
- `stoppedCode?: string` — the bounded refusal token the record always
  carries. The store quotes the destination only while it still observes the
  state the code names, so a row can hold a code and no words: the face falls
  back to the code, never composing a sentence out of it. **Both empty draws
  nothing at all** (A.8)

**The quoted reason is a ROW, not a chip.** Whichever of the two is shown
rides `.surface-task-resume-reason` on its own grid line, wrapping (`
overflow-wrap: anywhere`), and the state chip says only `FAILED`. `StateChip`
neither wraps nor truncates, and ruling B5 quotes the engine verbatim — where
that is a filesystem path, the ordinary case, a `FAILED · <path>` chip ran
534px inside a 341px row and was sliced off-glass mid-token. The engine's
words are never truncated to fit a chip.
- `custody?: "here" | "elsewhere"` — `SAVED HERE` on the machine that holds
  the row, `SAVED ON ANOTHER DESK` otherwise. **Never `THIS DEVICE`** (ruling
  B7): that string is the egress vocabulary (`desk/surface/egress.ts:16,25`)
  and egress badges are a hard boundary — two different facts must not wear
  one token. **And never a host id.** There is deliberately no host prop: the
  hub's machine identity is an opaque token, a face does not print opaque
  tokens (canon `raw-ids`), and the wire carries the verdict rather than the
  id. B7's literal `SAVED ON <host>` is superseded — the store holds no name
  a person could read
- `detail?: string` — the trailing fact the state's OWNER can supply
  (`00:52`, `3 OF 4 SOURCES`). A record whose owner has no clock must not
  pass one
- `verbLabel?`, `verbAriaLabel?`, `onVerb?` — override the default verb; the
  accessible name defaults to `<label>: <purpose>`
- `verbDisabledReason?: string` — a refused verb is **native `disabled`**
  plus `aria-disabled`, and its name says why. There is no `unavailable`
  Button variant and none is to be invented
- `primary?: boolean` — the face's ONE filled primary
- `onDiscard?` — `Discard` as a `ConfirmVerb` inside a `MORE` `Disclosure`,
  never a bare destructive verb. Discard is a STATE, never a delete (B6)

Presence rules (they are the species, not the caller's business):

- **No token for an absent fact** (UX-CANON A.8). No recipe → no recipe chip;
  never `RECIPE · NONE`. No custody → no custody token
- **No fact drawn twice.** `saved` owns the clock, `accepted` owns the day,
  `failed` owns the quoted reason — so none of them is repeated in the token
  row beside its own chip
- **No prose.** Tokens and labels only; the only free text is the purpose
  itself and the target's quoted reason
- Every verb is the library `Button` (UX-CANON A.1)

`TaskResumeList` is the container: ONE Tab stop for the whole list via
`useRovingRows` (kit law — never re-implemented in a consumer), Up/Down rove
rows, Left/Right walk a row's own verbs. It **returns `null` when it has no
children**, so no face can draw a caption of zero; its optional `label` rides
`countLabel` (`UNFINISHED 1`).

The state vocabulary is deliberately wider than any single record: it is the
union of the six work states across three owners (design D2(f)). A Room ask
reaches only `saved`, `failed`, `accepted` and `discarded` — it is one
blocking POST with no job row, no clock and no progress record (ruling B8),
so no caller may hand it a running clock or a `Stop`.

## CoverageRow / CoverageLedger (HS-200-15, species S1)

ONE grammar for "a source that was not observed", on every face that reads
sources (the arrival first; the brief, the meeting and the repair faces
consume it). Promoted from `ChairHome.tsx`'s `CoverageSection` (HS-200-07),
where the token was a raw span while `ConciergeCore.tsx` drew the same fact
as a `StateChip` — converged here on `StateChip`.

A row draws, in order: the emblem (`RM` · `SRC` · `MTG` · `CMT`, via
`coverageEmblem(kind)`), the source's name at the primary step, the source's
own reason, the state chip (the repair TOKEN: `CANT CHECK` · `STALE` ·
`READ FAILED` · `FORBIDDEN` · `PAUSED` · `NEVER CHECKED` · `NOT OBSERVED`),
`OBSERVED hh:mm` (`OBSERVED MM-DD hh:mm` on another day, `NEVER OBSERVED`
when never), and the OWNING verb as the library `Button`, raised.

- `gap: CoverageRecord` — one record from `readCoverage(...).gaps`
- `onRepair(gap)` — the verb was pressed; the FACE maps it (`Retry`
  re-reads, `Reconnect` opens connections, `Open source` opens the Room).
  The species draws the verb the record names and never invents one
- `now?: Date` — the clock the `OBSERVED` token is read against
- `CoverageLedger({ gaps, onRepair, now, rowTestId })` — the ledger of
  every gap; renders `null` over no gaps (A.8)

Rules the species enforces:

- **The reason is the source's own words, uppercased, or nothing.** A raw
  id (`needsYou_read_failed`, a dotted path) is refused by `plainReason`
  and the token carries the class alone (162's no-raw-ids law, A.10).
- **`stale` is a warning; every other gap is a failure** — the ink
  `coverage.ts` orders gaps by. `Coverage incomplete` is never danger
  (verdict Q6).
- **Coverage rides ABOVE the answer** (design D1): the face places the
  ledger between the head and the first result, never under it.

## ProjectButton (HS-200-15, species S6)

The way back to the originating Project, on every posture (story 09 AC2;
design D1). A library `Button` (ghost, dense, caption step) inside a
`role="group"` region named `Project` (canon D); accessible name
`Open the Project: <name>`. It is a READ; a write is never named as a way
back.

- `name: string` — the Project's name, drawn uppercased
- `onOpen()` — opens the Room
- `withheld?: boolean` — true when the desk holds exactly ONE Project: the
  species renders nothing (repeating one word on every row says nothing,
  A.7). The caller passes the fact; the species holds the rule
- Never a decorative token: a Project name the owner can read but not
  follow is a verb that does nothing (A.11)

## LedgerRemainder (HS-200-15, species S4)

The cap and the remainder as one grammar under a capped ledger: the TRUE
total lives in the head (the display line), the cap in the section caption
(`ACTIONS 5 OF 17` on the Chair since PHILO-13-03, via `attentionCaption` in
`desk/attention.ts`), and
the remainder is this row — a real count and a real verb:
`12 MORE · Show all`. Pressing it reveals the rest IN PLACE (A.4) and the
verb becomes `Show fewer`.

- `remaining: number` — rows not shown while collapsed; `<= 0` renders
  nothing (A.8)
- `expanded: boolean`, `onToggle()` — the caller's state
- `noun = "MORE"`, `subject?` — the count noun and the verb's accessible
  subject (`Show all: the remaining 12`)
- `ref` — forwarded to the verb, so `Escape` inside the revealed rows can
  return focus to it (the arrival does)
- The count is `countToken`; the verb is the library `Button`

## Disclosure: `ariaLabel` and `controlsId` (HS-200-15)

- `ariaLabel?: string` — an accessible name richer than the visible label
  (`Sources: Priya confirms the freeze window` over `2 SOURCES`).
- `variant="dense"` — the caption-step trigger that rides a ledger row's
  meta line (`▸ 2 SOURCES`); its styling lives in `disclosure.css`, so no
  face restyles a library trigger.
- `controlsId?: string` — the id of a body rendered ELSEWHERE, such as a
  `SurfaceLedgerRow`'s own expansion slot (`open` + `children`), so a body
  that must span the row's full width is not trapped inside a cell. The
  trigger keeps `aria-expanded`, names the body via `aria-controls`, and
  renders no body of its own; the external body carries the `role="region"`
  and closes on `Escape` itself (the Disclosure's focus-return to the trigger
  still fires). Used by the arrival's `N SOURCES` row.

## ClaimAxes (HS-200-06, promoted HS-200-11)

The three INDEPENDENT axes of one claim, as three chips on one line: kind ·
support · acceptance, then any typed unknown (design D2.0, species S2).
Promoted from the update posture so the brief (P3), the meeting review (P4)
and recall (P5) say the same word for the same fact.

- `kind: string` — `observation | inference | proposal | decision |
  execution_result | outcome_measure`; drawn as a `surface-token[data-chip]`
  (`DECISION`, `EXECUTION RESULT`)
- `support: string` — `unknown | source_linked | supported | disputed`;
  drawn as a `StateChip`: `SUPPORTED` (success) · `LINKED` (idle) ·
  `DISPUTED` (failure) · `UNSUPPORTED` (warning). A valid reference buys
  LINKED, never SUPPORTED (C2)
- `supportEdited?` → `LINKED · EDITED` (warning); `supportMigrated?` →
  `LINKED · MIGRATED` (idle). The history suffix is honest, never "reviewed"
- `acceptance: string` — `unreviewed | accepted | rejected | superseded`;
  `ACCEPTED` (success) · `REJECTED` (failure) · `SUPERSEDED` (warning) ·
  `UNREVIEWED` (idle). Never inferred from a score
- `unknowns?: {type, value}[]` — each printed AND typed unsupported, in the
  warn tint: `DEADLINE 2026-12-31 · NO SOURCE`, `NUMBER 95% · NO SOURCE`
- `testIdPrefix?` (default `claim`) — `<stem>-axes`, `-kind`, `-support`,
  `-acceptance`, `-unknown`, so a face keeps its own ids

The token functions (`claimKindToken`, `claimSupportToken`,
`claimAcceptanceToken`, `claimUnknownToken`) are exported beside it and are
the ONE vocabulary; a feature that needs the words imports them, never
re-spells them.

## Button `variant="chrome"` (HS-202-03)

The verb species WITHOUT the button plate. Some verbs are not plated
buttons — a menu row (`DeskMenu`), a wing tab (`SurfaceWings`), a dock chip
(`Dock`), the editor's formatting rail (`DeskEditor`), the mic, the record
orb, a ledger row's own body — and their material is drawn by the strip they
ride (`chrome-menus.css` keys off `.desk-menu-list button`, `pullout.css` off
`.desk-wing`, `window-chrome.css` off `.desk-dock-*`). For `variant="chrome"`
the plate classes (`btn`, `btn--secondary`, `btn--sm`) are therefore
WITHHELD; only the marker `btn--chrome` is stamped, so the strip keeps its
ink to the pixel and the verb is still the library `Button` (UX-CANON A.1).

- It always rides a host className that already owns the control's material.
  A `chrome` verb with no class draws nothing — that is a caller bug, not a
  new look to invent here.
- `dense` is ignored (there is no plate to shrink).
- Everything else is the species: one element, `type="button"` by default
  (a raw `<button>` in a form submits; this one never does unless asked),
  and one `loading` / `disabled` / `aria-busy` grammar.
- Fenced by `components/signal/Signal.test.tsx` and
  `desk/__tests__/hs202ChromeSpecies.test.tsx` (no plate; the first-use
  screens carry no raw `<button>`), and counted by the A1 source ratchet
  (`tests/unit/test_ux_canon_ratchet.py`).

The surface inventory of 2026-09-20 (§3.3) is why this exists: raw buttons
outnumbered library Buttons more than two to one, and the worst sites were
the shared species themselves.

## SendWell (PHILO-11-04)

The SEND well: ONE species for sending any stored document through the
channels (Phase 10's well with its eight update bindings replaced by one
document reference). Ratified on canvas E (phase-11 story 03). Every face
that sends a document composes it; no face draws its own rows.

**Import path.** `desk/surface/send` — a sanctioned sub-barrel, like
`DeskEditor`. It carries the channel wire (`features/channels/channels.ts`),
so it stays out of the main barrel, which is wire-free.

- `SendWells({ doc, head?, onSettled?, history? })` — what a host composes:
  the well, then its history, over ONE read of the document's sends.
  - `doc: DocRef` — `{ ref, title, label }`: `ref` is `<kind>:<id>` (the
    wire's `document_ref`), `title` the well's accessible name
    (`Send <title>`), `label` the short token a prepared row shows
    (`REV 4`, `BRIEF SEP 29`, `D-1a2b3c`).
  - `head?` — sits first inside SEND (the meeting's form picker).
  - `history?(sends)` — the slot only the update fills: its `DELIVERY N`
    with the manual To + Mark delivered row (R8), drawn exactly as Phase 10
    ratified it (canvas E1a). It is NOT in the species' row grammar (the
    unification waits for the owner's canvas; BACKLOG). Every other document
    gets `SendHistory`.
- `SendWell({ doc, sendsRead, onSettled?, head? })` — the well alone, for a
  host that shares one sends read (`useSends(ref)`).
- `SendHistory({ sends })` — `SENDS N` over the ended sends (N = sent rows;
  `SENDS` with no number when only UNKNOWN rows; nothing at all when none).
- `PreparedChip({ docRef })` — `◆ PREPARED ×K` for a host head or row;
  nothing at zero. It carries `data-head-chip` (below).
- Pieces for other channel faces: `PreviewWell`, `ProofCell`, `Unreadable`,
  `accountChip`, `useDestinations`, `useConnections`, `latestFor`,
  `mergeKnown`, `resetSendStore` (test seam).

Rules the species holds (they are not the host's business):

- **Reads and actions belong to one document.** A sends read is keyed by
  `doc.ref`: an answer for another document (a late read after the host
  changed document) is dropped, and only rows whose `document_ref` is this
  document enter (`useSends`, `mergeKnown`). So a prepared row's Send can
  never submit another document's `send_id`, and a late read never fills
  another document's history (Astra built-check r1 F1 on #708). The
  preview is keyed the same way.
- **One state per document.** Pick, press, held key and outcome live in a
  module store keyed `<ref>|<target>`: two seats of one document (the
  Chair's brief and Intelligence → BRIEF) show one pick and one press, and a
  lost answer's Retry sends the same `command_id`.
- **The words.** SEND · Send · Send again · Retry · Discard; SAVED, POSTED,
  COMMENTED, BLOG POSTED, ACCEPTED BY <PROVIDER>; REFUSED + its word +
  NOTHING SENT; FAILED + its word + NOTHING SENT; RESULT UNKNOWN; PREPARED;
  SENDING. Each from `features/channels/channels.ts`, never re-spelled.
- **A preview refused by name** (consumer behaviour; story 02 proves the producer and the route) shows `REFUSED`, its word, the size and the
  limit when the answer carries them as TOP-LEVEL integers `size` and
  `limit` beside `code` / `error_code` (`41,099 / 39,000 CHARACTERS` for
  `payload_too_large:slack`; story 02 produces them; no nested form), `NOTHING SENT` and the egress chip — never
  `NO ANSWER`. Only a preview with no answer at all is
  `NO PREVIEW · NO ANSWER` with Retry. `PREVIEW CHANGED` reads a fresh preview.
- **Slack is POSTED with no link**: the proof is the channel label.
- **The receipt survives the click that leaves its row.** A CLOSED
  destination row keeps its whole last result at its last-send seat (line 2,
  beside the egress chip): LAST SEND FAILED + its word + NOTHING SENT; a
  refusal newer than the latest send, REFUSED + its word + NOTHING SENT;
  LAST SEND UNKNOWN + its word; NO ANSWER · RESULT UNKNOWN. An open row
  shows the receipt under Send and keeps the one-chip summary on its line.
- **The egress chip** rides every destination row, every open preview and
  every waiting prepared row (UX-CANON: egress where egress happens).
- **Its own look** (`send/send-well.css`, G3): the UI face at 14 px; the
  preview's headings in the display face; mono only for fields, paths and
  chips; the `SEND` / `SENDS` head at 12 px in every host (a
  pullout's 10 px `h3` rule does not reach it). ONE row grammar in every
  host at every width: line 1 the lead (16 px) and the name, line 2 the
  chips (`.send-cells`) under the name; an open row's preview at the name's
  indent. No host rule for `section`, `h3`, `ul`, `p` or monospace reaches in.
- **The 44 px narrow target in every host** (G4, implemented; its proof on
  the Chair and the meeting's picker is owed by story 05): the well is itself a
  `surface` container (`container: surface / inline-size`), so every narrow
  rule of the kit (the 44 px picker, string field and check token; the
  ledger's narrow reflow) answers to the well's own width, also in a host
  that is not a surface container (the Chair at 393). The kit still never
  reads the viewport (DESIGN_SYSTEM.md rule 2).

### `data-head-chip` on a section head

A `SurfaceSection` head whose `actions` hold an element with
`data-head-chip` keeps its label whole on the first line; when the label and
the chips do not fit on one line, the chips and verbs wrap UNDER the label
(`surface.css`). The label is never squeezed into a column. The rule is
intrinsic (no width query), so it holds in any host.

## HeardQuote (first run C1, 2026-10-05)

The owner's own words played back as the face's one big fact. Born on the
first-run face "C1 · Heard first" (canvas FzBum28aTJQbsqwBvLuP16 v2, owner
ratified 2026-10-05: people must feel excited, heard and validated).

- `text: string` — his words, exactly as the transcript gave them; rendered
  in curly quotes. Content, not prose (UX-CANON A3 does not apply to it).
- `seconds?: number | null` — the take's length; renders `0:04`.
- `at?: string | null` — the clock time of the take (`14:03`).
- `local?: boolean` — an `ON DEVICE` lamp (LampGadget; the copy law wants the axis named, so never a bare `LOCAL`): the take ran on this device.
- `verbs?: ReactNode` — the take's library Buttons (Play · Again · Keep as note).
- `size?: "display" | "primary"` — `display` (default) is the display step
  (26/650): the ONE display element of the face. A face that shows a
  HeardQuote at `display` gives no other element the display step.
  `primary` (15/600) is a small echo.

Under the quote: `HEARD` (StateChip success) and ONE facts token,
`8 WORDS · 0:04 · 14:03`, built by `heardFacts()` — each part only when
known, the word count through `countToken` (never `0 WORDS`). Helpers
`heardWordCount`, `heardDuration`, `heardFacts` are exported with it.

## ProgressPlan: the label stays whole (first run C1, 2026-10-05)

A species fix, not a face fix. At 393 the running step's rate
(`1.1 / 2.7 GB · 46 MB/s`) took the row and cut the label to `Ch…`. The
step row now wraps: the label keeps its own width (`flex: 1 0 auto`), and
the bar and the rate go to the next line when they do not fit beside it
(the rate keeps to the right). Only a label wider than the whole row
ellipsizes. No prop changed.

## FoundBy (⌘K memory results, 2026-10-05)

The retriever that found a memory hit, as one caption token. Born on the
⌘K palette, option B "Two-line hit" (canvas YDTpkaJqFs3hyrZ4g581Mx §3,
owner ratified 2026-10-05).

- `origin: unknown` — the hit's `retrieval_origin` from
  `GET /api/memory/search`. The word: `lexical` → `KEYWORD`, `vector` →
  `MEANING`, `time` → `TIME`, `entity` → `NAME`, `relationship` → `LINK`.
  A hit carries one origin (the first retriever that found it), so one
  token. Any other origin (`observation`, a new retriever) renders nothing.
- The geometry of `surface-token[data-chip]` without the well: a hairline
  box. `MEANING` has the ember border and `--text` ink. On a selected or
  hovered command-deck row the token takes the row's ink.
- `foundByWord(origin)` gives the word or null; `foundByDay(at)` gives the
  hit's day (`10-01` this year, `2025-10-01` another year, empty when not
  a time).

## Command deck: the selected row's plate (⌘K canvas, 2026-10-05)

A species fix, not a face fix. The selected, hovered or focused
`desk-deck-row` is painted on `--accent-ink` (5.24:1 with
`--text-on-accent`), not `--accent` (3.79:1). The matched words of a
snippet use `--mark-bg` / `--mark-fg` (14.7:1), which read on the plain
row and on the selected plate.

## StandingPage + RefTokens (memory on the Desk, canvas section 2, option B)

Ratified 2026-10-05 ("Where the work lives"). A standing answer memory
keeps (MEMORY-DESIGN.md §3.4), drawn where the work lives: the Room shows
its project's four pages, the Brief the desk's two
(`web/src/desk/standingPages.tsx`, one read: `GET /api/memory/pages`).

- `title` — the question as the boards name it (`What did we decide`)
- `sentences` — the served sentences, a numbered list; each carries its
  `RefTokens`. A withheld sentence is simply not drawn: no gap, no
  counter, no marker. A page with no sentence renders nothing
- `built` — `BUILT 09:12` / `BUILT MON 08:02` / `BUILT 09-28`
- `stale`, `newSources` — the warn border and `STALE · 3 NEW SOURCES`
  (`STALE` alone at zero: no counter of zero)
- No verb: no on-demand rewrite exists, so none is drawn

`RefTokens` — the short source tokens (`MTG 10-01 · 14:20`, `DEC 10-01`,
`CMT 10-01`). A ref the Desk opens is a library `Button` that opens its
window through `openRef`; a ref with no window is plain text (A.11); a
ref that contradicts reads `AGAINST · <token>` in the danger ink. The
belief card (`features/project-room/recall/BeliefCard.tsx`, one more kind
of the recall card) draws its evidence with the same species.

## ReadyStrip (first run option A "One screen", 2026-10-05)

Every finished step's success token in one wrapping row. Born on the
first-run face, option A "One screen" (canvas YDTpkaJqFs3hyrZ4g581Mx §1,
owner ratified 2026-10-05), where Ready goes to the top when every step is
done.

- `items: { key, label }[]` — one success `StateChip` (icon `✓`) per item,
  in order. The label is the step's facts as one token
  (`CALENDAR · 14 THIS WEEK`). An empty label gives no chip; no chips, no
  strip (UX-CANON A8: no empty section).
- `ariaLabel?: string` — the list's name; default `Ready`.
- Renders a `ul` (each chip in an `li`). A chip wraps its text inside the
  strip at a narrow width; it is never cut.

## StartVerb / StartVerbs (first run option A "One screen", 2026-10-05)

The "what you can do now" verbs at the top of a finished face, made from
the owner's own data (`Record Atlas weekly · 10:30`, `Dictate`,
`Ask about this week`).

- `StartVerb` IS the library `Button` (UX-CANON: every verb the library
  Button) on a larger plate: 72 px tall, a glyph (`glyph`, one character,
  `aria-hidden`) over the word. `variant` is `primary` (the one verb the
  face leads with) or `secondary`. All Button props pass through
  (`loading`, `disabled`, `onClick`, `aria-*`).
- `StartVerbs` lays the set out as equal columns (`role="group"`,
  `ariaLabel` default `Start`); they stack into one column at the narrow
  container (`@container surface (max-width: 720px)`).
- A verb the face cannot honour is withheld, never drawn disabled
  (no dead verbs).

## ChoiceCardShell `lit` (first run option A "One screen", 2026-10-05)

`lit` stamps `data-lit`: the card is the next step that waits for the
owner's press. The material is the library's (`choice-card.css`): an
`--ok` ring and glow that fades in once
(`--duration-medium`); with `prefers-reduced-motion: reduce` it does not
fade (no animation). A face lights one card at a time. `lit` and
`selected` may both be set; `lit` draws over `selected`. (Moved from the
first-run face's own stylesheet into the library.)

## The object species (PHILO-14 B1)

The species the ratified A boards are drawn from
(`docs/internal/philo/phase-14/canvas`, alternative **A Workbench** plus C's
station track; `harness/p14.tsx` / `p14.css` are the drawing, these are the
library). Faces compose them; none draws its own icon, list, rail or well.
Import from the barrel (`desk/surface`); `surface/objects` is a private path
(fenced by `scripts/guard-architecture.mjs`). Previewed in the Components
window (`/design/components`, section "Object species (PHILO-14 B1)",
`pages/cores/ObjectSpeciesGallery.tsx`). Fenced by
`surface/__tests__/objects.test.tsx`.

Shared vocabulary (`objects/kinds.ts`):

- `ObjectKind`: project, meeting, decision, action, note, artifact,
  repository, agent, pr, person, conductor, smart, parked.
  `objectKindWord(kind)` is the KIND word (`ACTION ITEM`).
- `objectSprite(kind, id, state?)`: the one sprite from the mold (the A
  boards' mapping; a project/repository/drawer is the drawer, an agent the
  automaton). Every species also takes `sprite` (a URL) so lane A0's new
  mold lands without a species change.
- `ObjectTone`: ok · warn · fail · info · ask. Lamp colours are the
  `--lamp-*` tokens (ask = the ember of the boards). A lamp is never colour
  alone: the word sits beside it or is in the accessible name. Row lamps are
  `LampGadget`, which carries all five tones (`info` and `ask` joined it in
  B1 round 2), so ONE object is ONE colour on its icon, its list row and its
  Needs-you row. `lampGadgetTone` is now the identity (kept for callers).
  Board A-2L drew ASKS amber and WORKS green in the list while the icons
  were ember and blue: that was the board's inconsistency, and UX-CANON D
  (one object, one drawing) wins over it.
- Activation (DeskIcon, ObjectList rows): a click from ANY source selects
  (pointer, Space, `element.click()`, an assistive press). Enter opens: it
  is handled on keydown with its native click prevented, so one key is one
  callback.

### DeskIcon / IconLamp

The object on the glass: the 64 px sprite over its name; no plate at rest.
The library `Button` (`variant="chrome"`).

- `id`, `kind`, `name`; `kindWord?`; `sprite?` / `spriteSelected?`
- `selected?`: the `_sel` sprite and the inverted label plate (ink on
  paper); `aria-pressed`
- `lamp?: { tone, count?, label? }`: the 12 px raised square at the top
  right; `count` is the notch at the top left (the Dock's ember plate),
  never drawn at zero; `label` joins the accessible name
- `badge?`: a 32 px sprite at the bottom right (the Conductor's automaton)
- `drop?` (lit as a drop target: dashed paper ring, label on blue),
  `ghost?` (dimmed: the object being dragged, or parked)
- `onSelect?` (a press, Space), `onOpen?` (Enter, a double press),
  `ariaExtra?`, `draggable?`, `onDragStart?`, `className?`, `style?`
- The name wraps to two lines, then ellipsizes.

### IconGrid

A drawer's or the Floor's objects as icons: 112 px columns, 6 px rows,
4 px gutters; four columns in a `surface` of 520 px or less.

- `label` (the group's name), `children` (DeskIcons)
- Selection is the caller's: `marquee?: GridRect | null` draws the rubber
  band; `onMarquee?(rect | null, grid)` reports it while the pointer drags
  on empty glass (null at the end); `iconsInRect(grid, rect)` returns the
  ids under it; `onClear?()` on a press on empty glass
- One Tab stop, 2-D (`useRovingGrid` in `roving.ts`): Left/Right move within
  the visual row (no wrap), Up/Down move by the column count READ from the
  rendered layout on each key (the icons that share the first icon's top
  edge), Home/End jump to the first/last icon.

### ObjectList

The drawer's list view (A-2L): a `grid` with Name (sprite + name), Kind,
When, State (one lamp + word).

- `label`, `rows: ObjectListRow[]` (`id, kind, name, kindWord?, when?,
  whenSort?, state?: { label, tone }, sprite?, group?`); `group` (PHILO-14
  A2) sorts first, lower above (the Floor's zones above its objects)
- `sort: { key: "name"|"kind"|"when"|"state", dir }`, `onSort?(key)`: the
  header is a strip of chrome Buttons on the Steel plate (raised; the
  active one sunken, `aria-sort` on its `columnheader`); the species sorts
  by `sort` (When by `whenSort` when given)
- `selectedId?`, `onSelect?(id)`, `onOpen?(id)`: the selection IS the row
  (the blue plate). No `[ ]` / `[x]` mark, ever. The row's one verb is the
  name Button, stretched over the row.
- `selectedIds?` (PHILO-14 A2): a set selection (the Floor's Ask context);
  when given it wins over `selectedId`, and every row in it is a selected
  row. `selectedLabel?` (`in Ask context`) joins a selected row's
  accessible name.
- One Tab stop; arrows walk rows; Space selects; Enter opens.
- Rows are at least 44 px and never shrink below their content in a short
  scrolling list (PHILO-14 A2: the 393 fold line ran below the row). In a `surface` of 520 px or less Kind and When
  fold under the name (`KIND · WHEN`, the FoldLine of DeskListView without
  its marks) and the sort gadgets grow to 44 px. The fold is VISUAL only:
  all four headers stay, the Kind and When cells stay in their columns for
  assistive tech (clipped off the glass, never `display: none`) and the
  fold line is `aria-hidden`, so headers and cells name the same four
  columns at every width.

### GetInfo

The Get Info window body (A-2): sprite at 64 px, name (primary step), KIND
word; then a facts grid.

- `id, kind, name, kindWord?, sprite?`
- `facts: { where?, from?, made?, due?, owner?, state?: { label, tone },
  branch? }`: an absent fact is no row (no "None", no zero)
- `verbs?`: the caller's Buttons, drawn in the window footer
  (`SurfaceFooter`).

### TimelineRail / StationTrack

TimelineRail (A-4): an `ol` of entries `{ time?, word, tone?, text?, code?,
quote?, verbs?, pending? }`. `word` is BRIEF · READ · SAYS · WRITE · RUN ·
COMMIT · PR · HELD · ASKS · MERGE. `quote` is the agent's words: a `q` in
its curly quotes, italic body text, flat (no rail, no plate). `verbs` are the entry's own (Brief; Deny / Approve).
`pending` is the step that waits (MERGE · Your press in GitHub): a hollow
square, muted words. Props: `label`, `entries`.

StationTrack (C-4 on the A lane): an `ol` of `{ word, sub?, state:
"reached"|"current"|"ahead", tone? }`. Reached: filled with its tone
(default ok); current: lit (a paper ring), `aria-current="step"`; ahead:
hollow. The sub-lines fold away in a `surface` of 520 px or less. Props:
`label`, `stations`.

### AskWell

The question well (A-4), a raised plate: `<AGENT> ASKS · <AGE>`, the
question at the primary step, a StringGadget (with its mic) and the
**Answer** Button (primary; Enter in the field answers; an empty answer is
never sent, the press focuses the field), then the DRAFT line: the draft,
**Use draft**, the EgressChip of where it was made.

- `agent, age?, question, value, onChange, onAnswer(answer)`, `draft?`,
  `onUseDraft?(draft)`, `draftEgress?: { label, scope? }` (where the DRAFT
  was made, on the draft line), `egress?: { label, scope? }` (where the
  ANSWER goes, beside Answer, drawn with or without a draft), `busy?`

### PRCard / FilesChanged

PRCard, a FLAT card (read-only facts): sprite, `#N title`, the checks,
`REVIEW <WORD>`, `branch → base`. The checks never show a zero (UX-CANON
A.8): with some passed, `CHECKS p OF t` (fail tone when one failed) plus
`N FAILED` / `N RUNNING` above zero; with none passed yet, `CHECKS · N
RUNNING`, `CHECKS · N FAILED` or `CHECKS · N PENDING`, never `0 OF`. Props: `number, title, checks?: {
passed, total, failed?, running? }, review?, branch?, base?, sprite?`.
The verb that opens the PR is the face's (Open PR, by its egress chip).

FilesChanged: a SurfaceSection `Files changed · N` of `{ path, added?,
removed? }`, the counts `+a −r` with zeros not drawn; no files = nothing.
Props: `files`, `label?`.

### ConfirmLine

The YOLO hand in one line (A-3), a sunken well: from-sprite → to-sprite,
the title (primary step), the fact line (`CLAUDE CODE · YOLO · hs/...`),
**Brief ▸** (ghost, `aria-expanded`), **Cancel** (ghost), **Hand**
(primary). Props: `from, to: { kind, id, sprite? }, title, fact, onBrief?,
briefOpen?, onCancel, onHand, handLabel?, busy?`.

### NeedsRow / NeedsList / DropTarget / DragGhost

NeedsRow (A-5): an `li`: sprite (40 px), name, one fact line, ONE lamp and
its word, the object's verbs at the right. In a `surface` of 520 px or less
the lamp falls under the name and the verbs under the row. Props: `id,
kind, name, fact?, lamp: { label, tone }, verbs?, sprite?`. NeedsList is
the named `ul` (`label`, `children`).

DropTarget (`lit`, `children`, `className?`) lights any target with the
dashed paper ring. DragGhost (`kind, id, sprite?, x, y`) is the dragged
sprite at viewport `x, y`: fixed, `aria-hidden`, no pointer events, the
hard `--desk-ghost-shadow`. Both are presentation only; the drag logic is
lane C3's.

## The bevel grammar (PHILO-14 B1)

**A control that must be clicked LOOKS clickable** (UX-CANON D). Three
classes in `surface.css`, from the tokens `--bevel-raised` /
`--bevel-sunken` (built on `--bevel-light-strong` / `--bevel-dark`):

- `.bevel-raised`: a control you press, a plate you act on (the AskWell,
  which holds the answer gadgets; the IconLamp and rail squares, which are
  the LED gadget's own material). Pressed (`:active` on a
  button, `aria-pressed="true"`) it sinks.
- `.bevel-sunken`: a well you type or drop into, a pressed gadget (the
  ConfirmLine).
- `.bevel-flat`: a fact you read. Facts are never beveled (the PRCard,
  the SAYS quote, the facts grid).

On the Steel plate (the window frame, the ObjectList header) the same
grammar rides `--wb-raised` / `--wb-sunken`.

Not done in this lane (for the material pass, Movement B): the existing
species still draw flat where the grammar says raised: the plated
`Button` variants (`global.css .btn`), `StateChip`, `surface-token[data-chip]`
(the six-chip rows the PROPOSAL names), `SurfaceLedgerRow`, the
`SurfaceVerbs` strip and `FilterTokens`; and the window body
(`desk-pullout-body`) has no well. Move each onto `.bevel-*` there.
