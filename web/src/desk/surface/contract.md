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
(`NEEDS YOU 5 OF 17`, via `attentionCaption` in `desk/attention.ts`), and
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
