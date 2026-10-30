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
All styling uses design tokens from design-tokens.json. Raw color, z-index
and duration values are forbidden outside the token source and documented
exceptions (`npm run tokens:gate` enforces this).

## surface-token[data-chip] (HS-167-05)
The chip variant of `surface-token` gives it the full chip geometry (border, well bg, current material, 12px mono, 0.06em tracking) used by token rows (steward grant, run receipt refs). Stamp `data-chip` on any `surface-token` that should render as a discrete chip rather than inline text. Tone data-attrs still work.

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

## Executable reference and shared host composition (2026-10-23)

Open **Components** on the desk (`/design/components`). The core is
`pages/cores/ComponentsCore.tsx`; complete local examples live in
`pages/cores/design-reference/DesignReference.tsx`. The earlier control
catalogue remains in `ControlsGallery.tsx`. These import production species;
they do not establish that every example's complete composition has already
been adopted by a production feature.

| Reference | Shared implementation | Real consumers of those species |
| --- | --- | --- |
| Forms | PrefWindow/PrefSection (settingsWindow), PrefStatus → kit StatusBar, OwnerNameFields + useOwnerPreferences(useOwnerName), GadgetGroup/GadgetRow, StringGadget, OwnerAliasField, Button | Settings is the production consumer; Components renders the same rail, pane and kit status bar with fixture-only IO |
| Reading | ReadingDocument/Material, source doors, SurfaceWell | Ask results, Automation results, notes and source readers |
| Lists | SurfaceRows/SurfaceRow, SurfaceSplit, StringGadget | People, Memory and object readers use these list/detail species |
| Resources | RepositoryBrowserView + useRepositoryBrowser, DeskSortableTable fold/roving, ScrollHint, read adapter | RepoWindow is the production consumer; Components runs the same view/controller with an isolated fixture adapter |
| Editing | ThoughtDocumentPane + DeskEditor captured target, bindThoughtVoiceTarget, ThoughtVoiceRecovery + draft IO | Active Thought is production; Components uses local IO and synthetic text through the same binder |
| Conversation | DeskComposer/ComposerWell, shared reading material | Live Ask uses ComposerWell; the PR DeskComposer host is parked; the reference is a local consumer |
| Progress | ProgressPlan, Receipt, StateChip | Project Prepare/Steward and frontDoor source consumers; the reference's run is local specimen state |

`DeskWindowFrame.preserveInitialRect?: boolean` keeps an explicitly pre-seated
saved first rectangle through mount. It suppresses the automatic head-overlap
reseat, while retaining work-area clamping, focus, hub reconciliation and all
other frame behavior. Additional repository windows use it after the opener
chooses a sibling seat; ordinary windows retain the default placement policy.

The resource pattern keeps window identity outside the reader: each RepoWindow
owns its view-local controller and uses a real tree/file adapter; Components
supplies fixture reads to that same boundary. Back/Forward, selected inspection,
stale-response fencing, retained-copy labels, missing/refused reads and narrow
list/detail return belong to this pattern. Domain Git operations and resource
write authority stay with RepoWindow/provider services. The reference is not a
second production application. Durable view-history restoration and shared
collection adoption are follow-on work, not claims made by this first consumer.

The preference pattern shares `OwnerNameFields` and `useOwnerName(adapter?)`,
not a generic form engine. The production adapter keeps the existing settings
endpoint, revision guard, serialized autosave and leave keepalive policy.
Fields show Edited immediately, Saving for the captured in-flight value,
Saved only for an acknowledged current value, and Not saved with retained
input plus one Retry. Window grammar (2026-10-24): no pill per field. Each
field carries its word as `data-save-state`; the window's status bar
(`PrefStatus`, which composes the kit `StatusBar`: a lamp, the word, Retry
in the bar's verbs) says the worst word of the
fields, and "Saved just now / N min ago / 4:22 PM" only after an
acknowledgement in this window. The general preferences writer says its
state in the same bar; its plain refusal reason stays in the pane's alert.
`PrefWindow` is the rail (rows with illustrated glyphs, the selected row a
blue plate, Up/Down/Home/End) and the pane (label/control grid, captions in
the display face); at a content width of 520 px or less the rail is the
first view and a pane opens with Back (`settings-back`). On a compact
viewport the window's own title-bar Back is that Back: `useWindowBack`
(`surface/back.tsx`, a slot like `useWindowTitle`) hands the hosted frame's
compact Back and its test id to the open pane, and the title bar names the
pane; a narrow window off the phone, or a specimen, keeps the pane's Back.
A newer edit cannot inherit an older write's
Saved receipt. Raw alias text is an edit until committed and must survive
section leave. The local Forms adapter cannot write configuration or start
hardware audio; production StringGadget microphone behavior stays unchanged.
Thought's document writer and Ask's append policy remain separate authorities.

The active document pattern keeps CodeMirror and its native selection/IME/undo.
`DeskEditorHandle.captureVoiceTarget()` binds the original editor, range and
document generation; `insertAtCapturedTarget(target, text, { focus? })` rejects
stale, destroyed, non-editable or composing targets. It makes one isolated undo
transaction. Targets are view-local objects, never serialized domain identity.
`MicButton.bindText?` captures a consumer-owned delivery callback at the first
gesture, before asynchronous work; callbacks own their captured resource even
if the originating view leaves. A running mic still exposes Stop when new
capture becomes disabled. Default input policies of other consumers stay theirs.

Thought's `ThoughtVoiceDraftIO` defaults to existing Desk draft persistence;
Components supplies local memory to the exact composition with `mic=false`
and a local input control. Stale voice words live under `thought/voice/<noteId>`
separately from body drafts. NOT INSERTED offers explicit Insert at caret and
Copy; only a successful insertion clears retention. Clipboard failure never
claims Copied, and new retained text resets that receipt. This is browser
editing adoption, not proof of native OS targeting or ASR quality.

Keep consumer claims at their actual granularity: a shared control, a pattern
and a complete journey are different adoption claims. Parked code is not a
live consumer. Examples offer only the states they implement, with local
state labelled, no external effects or provider completion claim. A source
action must reveal the source; save/retry must preserve edits. Long reading
uses the window's content scroller. Bounded editor, terminal, code/table and
source-preview scroll regions remain intentional exceptions.

Shared host rules in `surface.css` cover `.desk-surface-body`,
`.desk-pullout-body`, `.chair-window-body` and explicit `.surface-host-body`
hosts. They own semantic group spacing, wrapping and the 68-character reading
measure. `Material` and `ReadingDocument` share it; code/tables retain their
horizontal overflow species. `.surface-group-well` supplies quiet group
material to specialised lists/results without taking their layout or state;
SurfaceLedger receives the same fine-edge material. Do not copy this skin
into a feature stylesheet. `kit.css` owns common head/filter/figure rhythm.

When a shared component or pattern changes, update its contract and matching
reference example in the same change. Record actual production adoption in
the existing implementation/release record. Keep material guidance in
DESIGN_SYSTEM and ownership guidance in the web author map, rather than
duplicating them in every feature plan.

## Native preference sheets (2026-10-14)

These opt-in variants extend the current gadget kit. Their defaults keep the
existing material and layout. They add no schema, form state, or save behavior.

- `GadgetGroup({ label?, material?: "default" | "inset", actions?, children })`:
  `inset` is a paper control sheet with a sunken outline and quiet engraved
  legend. A supplied label names the section through `aria-labelledby` and its
  heading ID. Content remains in a block `div.gadget-sheet`; actions render in
  a sibling `footer.gadget-group-actions` after the content. Pass library
  Buttons to actions; each keeps its intrinsic width. The group adds no window
  bar, toolbar, card shadow, or form behavior.
- `GadgetRow.controlWidth?: "standard" | "short" | "full"`: the opt-in
  preference row uses a 118–160 px label column beside a value column capped
  at 190 px. At 559.9 px or less the cap is 172 px and labels can wrap. `short`
  keeps small values at 84 px inside the aligned value column; `full` spans
  the row for longer editors. Opt-in rows use a block gadget slot. `wide`
  retains its existing span behavior. An inset group supplies the shared row
  rhythm to nested gadget rows too.
- `GadgetDivider()`: an exported semantic `hr` with the native etched rule.
  Use it between related rows within one sheet.
- `CheckGadget.variant="state"`: the same real checkbox and square well plus
  a visible On/Off word in its label. The native input covers the whole label,
  including decorations and word; at a narrow width the target is at least
  44 px high. The word is `aria-hidden` so the native checkbox retains one
  accessible name. Focus, disabled state, keyboard operation, and change
  callbacks remain native. `default` and `token` retain their current faces.
- `GadgetTable.layout?: "table" | "fields"`: `fields` retains the existing
  native cells, row identity, armed delete/verbs slots, and roving behavior.
  It derives repeated visual labels from `head` beside each cell below
  560 px; native input names remain the caller's. Fields and row actions
  have 44 px narrow targets. Omit `onAdd` when a containing group owns the
  Add action. The default table is unchanged.
- `SurfaceColumns.variant?: "default" | "preferences"`: `preferences`
  retains the current `main` and `side` slots, uses equal columns bounded at
  960 px with a 24 px gap, and stacks at 920 px or less in a column bounded
  at 620 px. The default 3:2 split remains unchanged.

All reflow responds to the named `surface` container. These are control
sheets inside the existing window; the window remains the only chrome.

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
- Vertical wells may set `--scroll-hint-background` and `--scroll-hint-depth` to match their material. Defaults remain `var(--surface-1)` and `28px`; paper readers use `var(--alive-paper)` and `12px`.
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

The one-tap filter strip (lightly raised tokens, PHILO-14 B2): `role="group"` over library `Button` species,
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

- The active token is `Button` **secondary dense** (Phase 16: the selection
  blue with light text), the resting ones **ghost
  dense** (quiet controls with a fine outline where required); each carries `aria-pressed` and the
  active one `data-filter-active`. Never **primary**: a face has one filled
  primary and it is the action the face is for, not a filter. No raw
  `<button>` (UX-CANON A.1).
- **No sparse rule — it never returns `null`.** A strip that vanishes on a
  short or empty list leaves no way to widen the view; it renders over an
  empty stream. This is the difference from `LedgerFilterBar`, which returns
  `null` below `SPARSE_THRESHOLD` (`LedgerFilter.tsx:104`, `sparse.ts:4`).
- **It carries no count.** `matchCount/total` would be a second count on a
  face that says its one count elsewhere (UX-CANON A.7/A.8).
- Not to be confused with `SurfaceWings`: filters change the current content
  selection; wings navigate the window. Both use the current shared material,
  with distinct placement and selected state.

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
- A window's wings also fold on a wide desk when their allocated head space
  cannot hold the choices. A wide viewport can contain a narrow window.
  `useStripFit` measures that allocation; window titles yield first, and the
  feedback/close/depth/zoom group retains its full space. The folded menu
  preserves every wing and the gear door. Ordinary desktop FilterTokens
  retain their existing rail behavior. Wing labels use the current sans,
  sentence-case material; uppercase labels in old canvases are historical.

## CycleGadget / WorkbenchSelect (2026-10-14)

CycleGadget keeps `label`, `value`, `options`, `onChange`, `disabled`.
Its visible native select owns the label, focus and selected value. Missing
values remain named; unavailable options remain listed and cannot commit.
The shared `components/signal/WorkbenchSelect` core also serves legacy
Signal Select, preserving native props, default values, form membership,
required validation, refs and input/change events.

The native popup is replaced by a library listbox portaled above window
clipping. Its fine frame and restrained radius use the shared ground; choice rows use paper,
the active row uses selection blue, the saved choice has a check, and
unavailable rows are flat with muted ink. Every choice is a chrome Button.
The portal copies the owner's computed custom properties. Long labels
wrap; long lists scroll within the space above or below the control.
At narrow device widths both owner and rows own 44px targets.

Pointer, Enter, Space or arrow opens without changing the value. Focus
stays on the select; arrows, Home, End and typeahead move the active row.
Enter, Space or a row press commits one native input/change pair only if
the value changed. Escape cancels and stops before the window's Escape;
Tab exits normally; outside pointer closes and keeps its destination
action. Blur, resize, ancestor scroll, disable, roster/value change and
unmount close. Scrolling the popup itself keeps it open. Native multiple
or sized list controls retain their native list behavior.

## StringGadget.micLabel (HS-200-13) / PadGadget.micLabel (HS-201-12)

The text well's mic is the voice law (canon B: MicButton on every text
input). Its accessible name defaults to `Speak <label>`; a face whose design
names the mic (`Dictate into the search`, board P5Recall) passes `micLabel`.
The mic itself, its placement and its behaviour are unchanged — only the
name the screen reader says. HS-201-12 gave `PadGadget` the same prop with
the same default, so both text species answer to one rule (the Thought
window's answer pad names its mic `Speak your answer`).

## PadGadget capture hooks (surface repair, 2026-10-14)

`inputRef?: Ref<HTMLTextAreaElement>` exposes the same textarea used by
auto-grow. `inputProps` accepts additional native textarea attributes, such
as combobox roles, source-list ARIA links, selection and paste handlers.
The species retains ownership of its label, value, change and key handlers,
disabled state, rows, placeholder and autofocus. Hosts keep custom capture
grammar singular with the existing `mic={false}` option.

`autoGrow` remeasures on value changes and native ResizeObserver width
changes. Height-only observer feedback does not trigger another resize;
the observer disconnects when the effect is replaced or the pad unmounts.

`micStartSignal?: number` and `micDraftScope?: string` mirror StringGadget.
They pass to the pad's existing MicButton. A direct agent message uses this
single mic for capture start, pending-answer sequencing and draft recovery.
No second mic or voice-law opt-out is needed.

## StringGadget.caption (PHILO-15 02)

`caption` shows the well's `label` as a visible caption above it (caption
step: 12 px mono uppercase). Use it where no GadgetRow label column names
the well, so a sighted owner reads what the field is (the Concierge's
`Server address` and `Key`). The caption is `aria-hidden`; the input keeps
its `aria-label`, so a screen reader says the name once. Off by default.

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

- `name: string` — the Project's name, drawn uppercased; with `plain`
  (window grammar 2026-10-24) in its own case
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
- `SendWellsFold({ doc, head?, onSettled?, history? })` — a compact Send/Hide
  host over one `useSends` read. Prepared and running work, past sends, read
  failures with Retry and refused outcomes stay discoverable while folded.
  Destinations and the ordinary preview mount on Send. An unresolved held
  press keeps the well open and disables Hide, so its exact Retry stays in
  view. Decision windows and decision records compose this host.
  `doc.version` is an opaque stable signature of the known saved document:
  a changed signature refreshes the ordinary preview; prepared payloads
  keep the bytes stored at preparation.
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
- **Betterment send S1.** After FAILED or RESULT UNKNOWN the verb is
  **Try again** (after SENT, **Send again**). A send the hub reads as
  `no_answer_in_time` (still running past its channel's limit + 30 s) shows
  "No answer from <channel>. Check <target> before you try again." with
  **Check** and **Try again**, never SENDING. `accountChip` shows a chip only
  for a sign-in failure, read from the hub's `connection` (where a good send
  counts as a good check).
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
- **The Send composition** keeps Add destination in the SEND section head,
  including when the built-in folder is present. Pending reads and previews
  use SurfaceState. PREVIEW names the frozen fields and payload; only the
  payload sits in SurfaceWell, without an inner scrolling cap. Dispatch and
  its receipt follow outside that well. The host owns the one scroll region
  and its Back action.
- **Its own look** (`send/send-well.css`, G3): the UI face at 14 px; the
  preview's headings in the display face; mono only for fields, paths and
  chips; the `SEND` / `SENDS` head at 12 px in every host (a
  pullout's 10 px `h3` rule does not reach it). ONE row grammar in every
  host at every width: line 1 the lead (16 px) and the name, line 2 the
  chips (`.send-cells`) under the name; an open row's preview uses the content
  width. The closed row carries the short target; the open row leaves it to
  the exact preview fields and retains channel, account, result and egress.
  No host rule for `section`, `h3`, `ul`, `p` or monospace reaches in.
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

`RefTokens` — the short source tokens in sentence-case words, sans 12 on
a soft plate (window grammar 2026-10-24; `refWords`: `Meeting 10-01 ·
14:20`, `Decision 10-01`, `Action 10-01`, `Risk`; dates, times, ids and
two-letter forms stay). A ref the Desk opens is a library `Button` that
opens its window through `openRef`; a ref with no window is plain text
(A.11); a ref that contradicts reads `Against · <token>` in the danger ink. The
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
  `objectKindWord(kind)` is the KIND word (`Action item`).
- `objectSprite(kind, id, state?)`: the one sprite from the mold (the A
  boards' mapping; a project/repository/drawer is the drawer, an agent the
  automaton). Every species also takes `sprite` (a URL) so lane A0's new
  mold lands without a species change.
  Sizes (Icons D, 2026-10-24): 64 (the icon), 32 (the list row,
  `listSprite`) and 20 (the dense row and the window title glyph,
  `glyphSprite`). A directory wears its zone's colour (`ZONE_HUES` in
  `sprites.ts`).
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
- PHILO-14 C3, the drag: `onDragEnd?` (the source's cleanup), and as a
  drop target `onDragOver?` (call `preventDefault()` to accept),
  `onDragLeave?`, `onDrop?`. HTML drag and drop; the lane owns the logic.
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
When, State (one lamp + word) by default. Providers can declare only the
columns their projection supplies.

- `label`, `rows: ObjectListRow[]` (`id, kind, name, kindWord?, when?,
  whenSort?, state?: { label, tone }, sprite?, group?`); `group` (PHILO-14
  A2) sorts first, lower above (the Floor's zones above its objects)
- `sort: { key: "name"|"kind"|"when"|"state", dir }`, `onSort?(key)`: the
  header is a strip of chrome Buttons on the Steel plate (raised; the
  active one sunken, `aria-sort` on its `columnheader`); the species sorts
  by `sort` (When by `whenSort` when given)
- `visibleColumns?: readonly ObjectSortKey[]`: omitted preserves all four
  columns; Name is always present, with other requested columns in canonical
  order. Header and row cells use the same declaration. Filed Notes uses
  Name/Kind without empty When/State columns; this does not infer provider
  capabilities or change selection, sorting or Open. One/two-column lists
  keep their columns at narrow widths instead of duplicating folded metadata.
- `selectedId?`, `onSelect?(id)`, `onOpen?(id)`: the selection IS the row
  (the blue plate). No `[ ]` / `[x]` mark, ever. The row's one verb is the
  name Button, stretched over the row.
- `selectedIds?` (PHILO-14 A2): a set selection (the Floor's Ask context);
  when given it wins over `selectedId`, and every row in it is a selected
  row. `selectedLabel?` (`in Ask context`) joins a selected row's
  accessible name.
- One Tab stop; arrows walk rows; Space selects; Enter opens.
- Rows are at least 44 px and never shrink below their content in a short
  scrolling list (PHILO-14 A2: the 393 fold line ran below the row). For the
  default four-column list, in a `surface` of 520 px or less Kind and When
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
  branch?, more? }`: an absent fact is no row (no "None", no zero)
- `facts.more?: { key, word, value }[]` (PHILO-14 C4): the facts a kind has
  beyond the seven (an agent's VERSION, HOOKS, SIGN-IN; a launch's
  LAUNCHED, CONTROL). Drawn after the seven, in order, each a
  `data-fact={key}` row; an empty `value` is no row.
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

### The Program StationTrack (Programs, 2026-10-28)

`web/src/desk/programs/StationTrack.tsx` (canvas
`docs/internal/betterment/programs/canvases/programs-2026-10-28.html`, kit
list "NEW StationTrack"): a step's six stations BRIEF · WORK · CHECK ·
REVIEW · PR · MERGE as one `ol.pg-track`, its accessible name the current
station in words (`At Check green`). Props: `stations` (from
`programs/model.ts` `stationsOf(step)`: `{ key, word, sub?, state:
"passed"|"current"|"ahead"|"skip", tone, live?, person? }`), `form`
(`"dots"`: six 8 px dots and 10 px links, the current one 10 px in its tone,
98 px in all, the board row's track; `"words"`: each station a dot and its
word with the quiet word after it, `Check green`, `PR #1591`, the Gate
fold's track), `label?`. Passed is filled grey, ahead hollow, a station
outside the step's gate (no reviewer, no merge) a short dash; a person's
review draws her `Avatar`. The live current station breathes with
`kit-lamp-live` (2.4 s, a box-shadow; none under reduced motion); nothing
moves on hover. It is a sibling of the lane's StationTrack above (the
square stations of a lane), not a replacement.

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
  (sending: Answer spins and cannot be pressed; the field stays editable,
  so a stalled send never locks the draft)
- `disabled?` (the answer cannot be sent now, as with no session: Answer
  is disabled without the spinner, the field stays open),
  `listenSignal?` (each new value starts the field's mic: a Speak answer
  press), `draftScope?` (the mic's draft scope), `inputRef?` (the field,
  for a caller that focuses it, as after Use draft).
- `arm?` (the hand's gate beside Answer, after the egress chip: in Secure
  or Normal, `MODE · ARM FIRST` and the ARM key; the answer row wraps).

TimelineRail, StationTrack, AskWell, PRCard and FilesChanged take a
pass-through `data-testid` (FilesChanged puts it on its file list).

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
briefOpen?, onCancel, onHand, handLabel?, busy?`. PHILO-14 C3: `disabled?`
(Hand cannot be pressed: the preview refused or is out), `egress?` (the
hand's EgressChip, on the Hand side), `status?` (a token line under the
fact: a refusal, the tracker read, the receipt), `verbs?` (the verbs after
the press, Close / Send again; they replace the three).
PHILO-15 16: `agentToken?` (the agent as a library Button at the head of
the fact line; the owner flips it, CLAUDE CODE ⇄ CODEX; `fact` then holds
mode · branch). The ⇄ mark is drawn, so the fact line still reads
`CLAUDE CODE · YOLO · hs/...`.

### NeedsRow / NeedsList / DropTarget / DragGhost

NeedsRow (A-5): an `li`: sprite (40 px), name, one fact line, ONE lamp and
its word, the object's verbs at the right. In a `surface` of 520 px or less
the lamp falls under the name and the verbs under the row. Props: `id,
kind, name, fact?, lamp: { label, tone }, verbs?, sprite?`. NeedsList is
the named `ul` (`label`, `children`).

`dotState?` (window grammar 2026-10-24, the Needs-you window): the state is
a DotWord in sentence case (`stateWords`: `OVERDUE · 23 DAYS` → `Overdue ·
23 days`, `PR OPEN` → `PR open`, `WAITING ON PRIYA` → `Waiting on Priya`;
mixed-case words and the acronyms in `KEEP_CAPS` stay), the Project is a
`plain` ProjectButton, and in a surface of 520 px or less the row is one
44 px line pair: the name over the state and the fact, the verbs at the
right. The Project's Button is not drawn at that width (its own 44 px
target does not fit the pair; the item opens its Project).
Today's Needs you draws the same rows (`NeedRow plates={false}`; needs.css
styles `.needs-drawer` and `.today-needs` with one rule set): no kind plate,
no box around the list, a hairline between rows, the egress chip in lower
case. Today keeps its own name step (sans 15/500, today.css).

DropTarget (`lit`, `children`, `className?`) lights any target with the
dashed paper ring. DragGhost (`kind, id, sprite?, x, y`) is the dragged
sprite at viewport `x, y`: fixed, `aria-hidden`, no pointer events, the
hard `--desk-ghost-shadow`. With `from?: {x, y}` (PHILO-14 C3) it also
draws the dotted path (`.drag-path`, A-3) from where the drag began to the
ghost's centre. Both are presentation only; the drag logic is lane C3's
(`desk/hand/`).

## Shared shell material (owner direction, 2026-10-22)

Workbench meets Pop!_OS modernizes presentation across the same components.
Fine frames, restrained radii, quiet secondary/ghost actions, sans labels,
white fields and continuous paper replace mandatory heavy Steel bevels.
Shared tokens in design-tokens.json remain the only color/material source.
A flat `none` shadow is intentional; an absent material token is a defect.
The historic bevel classes below remain compatibility vocabulary for pressed
and selected state, not a mandate to paint every Button or body as a plate.
Focus outlines, state names, keyboard/voice authority, contrast and 44px narrow
hit ownership remain mandatory. Surface hosts own layout, not their own theme.
The settled canvas is docs/internal/betterment/canvases/modern-shell-2026-10-22.html.

## Historical bevel grammar (PHILO-14 B1)

This section records the earlier material implementation. Its token/class
names remain compatible, but its raised/sunken painting prescriptions are
superseded by **Shared shell material** above. Read current values from the
token source; do not reintroduce the bevels below.

**Historical principle: a control that must be clicked LOOKS clickable** (UX-CANON D). Three
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

The material pass (PHILO-14 B2) moved the existing species onto the
grammar, in the library:

- **Button** (`global.css .btn`; Phase 16: the Steel plate, see "The
  interior kit" below): every plated variant (secondary,
  primary, ghost, danger) wears `--bevel-raised`; `:active` and
  `aria-pressed="true"` sink it to `--bevel-sunken`. The glass top line
  of the materials block is gone. Disabled stays flat. A Button on the
  Steel plate (the title bar's Raw) keeps `--wb-raised`.
- **StateChip** is a LAMP: no border, no well, no etch; the icon slot is a
  10 px square with the raised bevel, lit in the state's tone (active =
  ask, working = info, success = ok, warning = warn, failure = fail; idle
  and unreachable unlit). The glyph stays in the DOM, aria-hidden, and is
  not drawn; the word carries the meaning.
- **`surface-token[data-chip]`** is a flat fact: no plate, no bevel (the
  1 px border stays, transparent, so no row moves). A chip with
  `data-tone` (`warn`, `danger`, `ok`) wears the lamp before its word.
  No chip in the tree is pressable; a pressable token is a Button.
- **FilterTokens** and **ProjectButton** are raised TOKENS: the light
  bevel `--bevel-raised-soft` with no plate; the active filter (and a
  pressed token) sits in `--bevel-sunken-soft` on its accent tint. A wing
  is a Steel plate with the full bevel, so the two never look alike.
- **SurfaceVerbs** is a raised strip (`--bevel-raised`).
- **SurfaceLedgerRow** stays flat (a fact); its verbs are raised Buttons;
  an open row keeps its etched well.
- **The window body** (`.desk-pullout-body`, `.desk-surface-body`,
  `.chair-window-body`) is the well: `--bevel-sunken`, one per window (a
  body inside a body draws none).

Not moved: `EgressChip` (the egress law's own chip), the `desk-chip`
family of the older pullouts (outside the Chair, drawer, lane, Conductor
and Needs you faces), and the row why-token of Needs you (a flat word;
the row's lamp is its flight's StateChip).

## The interior kit (Phase 16, COMPOSITOR.md §11)

The APIs below remain useful. Material descriptions such as Steel, raised,
sunken and paper plate describe the original implementation, not current
paint. Current fine-border material and geometry in DESIGN_SYSTEM govern.
Composition follows the task: a reader or form need not add a FilterBar,
Ledger or AskWell merely to reproduce the historical sequence.

Every internal app (Needs you, a Room, the Conductor, a meeting, People,
Delivery, Settings) is composed from these, in this order: AppHead (with its
StatusStrip) → FilterBar → Section → Ledger / IconGrid → AskWell → Foot. The
canvas is `docs/internal/philo/phase-16/01-canvas/compositor.html` (the CSS
block "THE INTERIOR KIT" and its four windows). Two species are new
(`kit.tsx`, `kit.css`); the rest are the library's existing species in the
new material. The material tokens (`--wb-field`, `--wb-well`, `--wb-text`, `--wb-muted`,
`--wb-rule-soft`, `--wb-sel`, the `*-ink` tones) are lane A1's
(`tokens.css`, merged); the kit reads them directly, and A1's
`window-interior.css` remaps the interior tokens inside every window.

Every readable word is 12 px or more (UX-CANON §C outranks the canvas's
11 and 10 px captions, strip, meta and plates). Ordinary desktop Buttons use
`--size-btn` (32px); narrow Buttons own 44px targets. Chrome strips own their
44px rows rather than adding overlapping halos.

| Species | Where | The rule |
|---|---|---|
| **AppHead** | `kit.tsx` `AppHead({ fact, children, as?, className?, data-testid?, factTestId? })` | The ONE big fact (display 26/650, `--font-display`; the element carries `surface-display kit-disp`), once per window. Its child is the StatusStrip, on the same baseline; the pair wraps. `SurfaceIdentity` is not this species (its name is the 15 px primary step under a purpose fold) and is left as it is. |
| **StatusStrip** | `kit.tsx` `StatusStrip({ items, className?, data-testid? })` | Tokens, never prose: `{ lamp?, text?, value?, verb?, testId? }`. Mono 12 upper (0.04 em), muted ink; `value` bold ink; the lamp an 8 px square with a 1 px ink border in the lamp tone (aria-hidden: the word carries it); a `verb` is a library Button. Empty items are dropped; an empty strip draws nothing. |
| **FilterBar** | `kit.tsx` `FilterBar({ options?, value?, onChange?, label, trailing?, disabled? })` | The FilterTokens strip on one rail, a spacer, the trailing verb group at the rail's right. One per window at most. FilterTokens IS the bar's twin (restyled, not a third filter species): a resting token is a Steel cell with ink under the light bevel (`--bevel-raised-soft`, PHILO-14 B2: never a plate), mono 12 upper; the active token is the selection blue (`--wb-sel`) with paper ink in the light sunken bevel (`--bevel-sunken-soft`). A held (disabled) strip is flat on `--disabled-bg`. `LedgerFilterBar` has no caller and is left as it is. |
| **Section** | `Surface.tsx` `SurfaceSection({ label, count?, actions?, data-testid? })` | The caption (mono 12/700 upper, 0.06 em) reads `Name · count`; a zero or null count is not said (A.8); a string count is drawn as given. The verbs follow the caption; the hairline (`::after`, flex 1) runs to the right edge. A Section may be a head alone (a caption and its verb, no body). |
| **Ledger** | `Surface.tsx` `SurfaceLedger({ count?, controls?, cols?, label?, data-testid? })` | A sunken PAPER well (1 px ink border, `--wb-sunken`); inside it `--text*` read ink. `count` is optional now: a kit ledger says its count on its Section and draws no head. `label` names the well (`role=group`). `cols="kit"` is the kit row template (kit.css): plate · name · meta · verbs on one line; under 560 px the meta and the verbs fall under the name. |
| **LedgerRow** | `Surface.tsx` `SurfaceLedgerRow({ kind?, kindTitle?, meta?, metaTone?, … })` | A row: kind plate · name · meta · trailing verbs. `kind` draws the plate (`KindPlate`: raised Steel, 44 px, mono 12/700) in the 52 px lead slot; a given `lead` wins. The name is sans 15/500 ink; `meta` mono 12 upper, `metaTone` `ask` / `ok` / `fail` (lane A1's `--wb-ember-ink`, `--wb-ok-ink`, `--wb-danger-ink`). A soft hairline between rows; the hover tints selection-blue at 12 %. `wrap`, `trailing`, `open`, `selected` stay as they were. |
| **IconGrid** | `objects/IconGrid.tsx` `IconGrid({ well?, data-testid?, … })` | `well`: the objects INSIDE a window in a sunken paper well, five across at 900 px and wider (auto-fit 120 px columns below), the sprite at 40 px over a two-line sans 12 name, the hover tinted, the selected name on the selection blue. The same DeskIcon sprites as the Floor; the Floor's grid has no well. |
| **AskWell** | `gadgets.tsx` `StringGadget` (the well) and `objects/AskWell.tsx` (the question plate that holds one) | Every text well is a sunken paper well, ink words in the sans body step (13), the mic a raised Steel plate the well's full height on its right edge (`--size-icon-lg` wide; 44 px at the narrow container): the voice law. The Room's ask (`RoomAskWell`) is this well (its raw input retired). The AskWell question plate is raised Steel with ink. |
| **Foot** | `SurfaceFooter.tsx`, `surface-footer.css` | The Steel foot: an ink line and a shine along its top (inset), ink words; the egress chip a paper plate (ink border; its scope the word's ink tone); the receipt in the middle; the verbs right. Egress exactly where egress happens (A.9). |
| **Verb** | `components/signal/Signal.tsx` `Button`; its material in `styles/global.css` | A raised Steel plate with a 1 px ink border and ink; `primary` the selection blue with paper; `danger` the Workbench red (`--wb-rec`) with paper; `secondary` and `ghost` the same plate at the same height; pressed (`:active`, `aria-pressed`) it sinks (`--wb-sunken`); disabled is flat and faded. `chrome` is unchanged (the strip owns its ink). The 44 px narrow-desk halo stays. |

## The window grammar (2026-10-24)

`docs/internal/betterment/native-experience/WINDOW-GRAMMAR-2026-10-24.md`.
Every window reads: title bar → toolbar → content → status bar. There is one
Toolbar and one StatusBar in the product: Settings (`PrefStatus`), the Note
(`ThoughtDocumentPane`, `ThoughtWorkspaceWindow`), the Room, Meetings,
Projects and the automation window compose these species, and the
Components Forms and Editing specimens render through the same path.
Setup (the readiness list), New Project (the label/control grid; the egress
chip of each picked source in the status bar), Processes, Engines (two lists, below) and Speak (an editor window; the Talk
key is the toolbar's one primary; the level meter, the phase, a ticking
`m:ss` and the speech engine in the status bar) compose them too. No headline,
no stat tiles, no chip row inside a collection window (AppHead stays for
readers only). Components ▸ Window shows the composition with fixture rows.

| Species | Where | The rule |
|---|---|---|
| **Toolbar** | `kit.tsx` `Toolbar({ label, children, trailing?, trailingStays?, className?, data-testid? })` | A 36 px band (`--wb-toolbar-h`) directly under the title bar, a 1 px soft rule under it, `role="toolbar"` named by `label`. Children are verbs: library Buttons, icon + label (`ToolGlyph`), the quiet secondary form at rest; ONE primary at most. `trailing` (a search StringGadget, a filter) sits at the right. A selection never adds to the toolbar (a reflowed band moves the row under the pointer between the two presses of a double press): the selection's verbs go to the StatusBar's `verbs`. The trailing group wraps at any width (a filter such as Current only keeps its whole face, never clipped). Narrow (≤ 520 px): the trailing group takes its own line under the verbs and the search well the full width; every Button keeps 44 px. `trailingStays` (the Note's mic): the trailing control is the band's own, not a search well, and stays at the band's right end at every width (`data-trailing="stays"`). |
| **ToolGlyph** | `kit.tsx` `ToolGlyph({ kind })` | 16 px verb glyph, 1.5 px pen in the Workbench blue (paper on the primary): `record` (red dot), `import`, `engine`, `new`, `summary`, `retry`, `open`, `note`, `ask`, `tasks`, `project`, `send`, `done`, `run`, `edit`, `copy` (two sheets: Speak's Copy). Decorative; the label names the verb. |
| **StatusBar** | `kit.tsx` `StatusBar({ items, egress?, verbs?, className?, data-testid? })` | A 24 px band (`--wb-statusbar-h`) at the foot, sans 12 muted, tabular numbers: items `{ key?, text, value?, lamp?, testId? }` joined by a middle dot, `verbs` (the selected object's library Buttons: Open, Retry, Run summary) then the egress chip at the right (A.9); the band grows from the foot, so nothing above it moves. The items carry `role=status`, never the verbs. Warm true words (`5 meetings · 1 failed`); `countWords(n, noun, plural?)` (kit.tsx) says a count and returns null at zero, so the bar drops that item (A.8). Portaled into the frame's foot slot like SurfaceFooter, in place without one. No items and no egress: nothing, and the empty frame foot folds away (`.desk-surface-foot:empty`). Narrow (≤ 520 px): `--wb-statusbar-h` grows to 44 px and the verbs take their own line under the words, each a 44 px target (kit.css; no face restyles the bar). The Room's foot is a StatusBar too (`room-status`: the merged PR in warm words with the ok lamp, the sources count; Open PR and its egress chip as verbs). |
| **DotWord** | `kit.tsx` `DotWord({ tone?, children, className?, live?, data-testid? })` | A state fact in the window grammar: an 8 px round `kit-dot` and a sentence-case word, sans 12, no plate, no border (`● No engine for answers`). `live` (a state happening now: Checking, Downloading) makes the dot breathe as the status bar's live lamp does (a box-shadow; a still ring under reduced motion). `tone` is an object tone or `idle` (default, the grey dot). The sweep's material fence reads it (and the dense list's state cell) as a state fact: round 8 px dot, no border, shadow or fill, never mono or uppercase (`material_rig.dot_fact_fault`). |
| **Body inset** | `interior.tsx` `useWindowInterior("list" \| "editor" \| null)` | The core tells the host which interior it draws; the host sets `data-interior` on the body. `list` and `editor` run edge to edge (inset 0; the list scrolls inside); null keeps the 12–16 px form/reader inset; `undefined` says nothing (a host face that hands its window to a child face, the Meetings list drawing a meeting record, lets the child say it). |
| **ObjectList dense** | `objects/ObjectList.tsx` `density="dense"`, `columns?` | The list view of a collection window: rows 30 px (`--wb-row-dense`; 44 px in a surface ≤ 520 px), each led by its 20 px illustrated object glyph; headers sans 12/600 muted, sentence case; cells sans 13; the state a dot and a word (`state.testId` for a test hook); hover lifts the row (tint + 1 px ink rule), the selected row is the vivid blue (`--wb-sel-vivid`, paper ink); 120 ms eased; no zebra; fills its container. `columns` declares the provider's own columns in order (`{ key, word, track? }`); a non-built-in key reads `row.cells[key]` (sorted by `row.sortValues[key]` or the text). `nameTestId` puts a test hook on the name. `state.tone` adds `idle` (the grey dot and a muted word: Idle, Not installed, Quiet; the Conductor's rows use it) and `state.live` marks a running state (`data-live`). `avatar: { initials, hue }` leads a person's row with a 24 px initials disc in the person's hue (`initialsOf` / `hueOf`, the kit avatar's eight hues) in place of the sprite (People's roster; `data-avatar` on the row). Narrow (≤ 520 px) fold: the non-state cells start their own line under the name; only filled cells show, the first filled cell leads the line and a middle dot joins two filled cells (`data-fold="lead" \| "next"`), so no line starts with an orphan dot. Selection is the press; Enter or a double press opens (a touch tap opens: the phone list has no double press); keyboard as ObjectList. Default density and every current caller are unchanged. |

**List + inspector (a sanctioned shape of the grammar).** A collection whose
selected object has settings: the dense `ObjectList` runs edge to edge under
the toolbar (`useWindowInterior("list")`; the body scrolls), and under it the
selected object's inspector, a `PrefSection` caption (sans 12/600, sentence
case, a hairline) over a label/control grid (label sans 13 at 160 px, the
control at the right, a 1 px soft rule between rows; one column at ≤ 520 px).
The selected row's verbs and its egress chip go to the StatusBar, never to the
toolbar. A row with no value says so as a DotWord (`● Not assigned`), never a
blank. 
**Two lists (Engines, 2026-10-30, `betterment/engines/canvases/engines-2026-10-30.html`
direction B).** Two `ListView`s side by side from 880 px of window width
(stacked under it, the first one on top): What HoldSpeak does (one `ListRow`
per job: the job, its engine as a picker Button, a state only when it changes
what he does) and Engines (sprite, name, where it runs in words, the state).
A row names its partner in words; `selected` on a row lights its partners in
the other list (`lit`, a 3 px blue edge). A row's `fold` opens under it in the
same item: the engine's facts as label/value rows (the address there and only
there, A.9), its verbs. No host chip on a row or the status bar. Builder tools
never swap the face: the parked switchboard sits in a closed Wiring fold under
the lists. Components ▸ Window ▸ Two lists renders the same classes with
fixture engines.

| Species | Where | The rule |
|---|---|---|
| **ListRow** | `objects/ListView.tsx` `ListRow({ glyph?, name, meta?, state?, age?, verbs?, onOpen?, openLabel?, openTestId?, nameTestId?, selected?, lit?, expanded?, progress?, fold?, data-testid? })` | A 32 px row (44 px ≤ 520 px). `selected`: the vivid blue plate, paper ink (`data-selected`, `aria-current`). `lit`: a partner of the selection in another list (`data-lit`). `expanded`: `aria-expanded` on the open Button. `progress` 0–100: a 2 px info bar along the row's foot. `fold`: a node under the row inside the same item, on the field wash (`kit-listrow-fold`). `state.live` breathes its dot. |

## SurfaceSwitchboard (PHILO-16 C, the Runs on board)

## EngineLine and RunLine (Phase 17)

`useEngine(capabilityId)` reads the assignment roster and returns the shared
engine fact `{ state: "set" | "none" | "unread" | "failed", model, place }`.
`EngineLine` renders that fact before a run and owns the Choose engine or Try
again verb. `RunLine` renders one run state (`idle`, `running`, `success`, or
`failure`) and takes its closed reason from `runWords.ts`. Faces pass route
facts into these components; they do not map server sentences with regexes.

The picture of what runs on what (COMPOSITOR.md §12, canvas Board 2). It
replaces the parked HS-101 list switchboard (`Surface.tsx`, rendered
nowhere). It decides nothing: the app answers `accepts` and writes in
`onPatch`.

- `jobs: SwitchJob[]` — the left column. Each: `name` (sans 14/600),
  `tasks` (one readable 12px mono token line), `state` (one of the five:
  `ready · limited · broken · waiting · off`, drawn as the plug's colour:
  green, amber, red, steel, dim steel), `verb` (Try it), `result` (the
  answer on the job), `isDefault` (the Default for AI work row).
- `engines: SwitchEngine[]` — the right column. Each: `emblem`
  (`MAC · LAN · API · CLI` plate), `name`, `tokens`, `lamp`
  (`ok · busy · warn · broken · off`), `progress` (0..100 fills the bar on
  the plate; `null` draws no bar), `verb` + `egress` (the plate's one verb
  and the host it reaches), `draggable` (only an engine with a model record),
  `detail` (the plate unfolded in place, full width under its verb: an
  agent engine's Spend limit per run; a press or key inside it never drags
  or patches; a phone tap verb never carries it).
- `found: SwitchEngine[]` — under the engines, caption `Found · n`; a
  found plate has no plug and carries its one verb (Use it). No row, no
  caption (UX-CANON A8).
- `wires: SwitchWire[]` — `order 0` is the job's engine (solid ink);
  `1..` its fallbacks (dashed). `tone: limited` is amber, `broken` a red
  dash. The selected job's wires are `hot`; `pulse` names the job whose
  first wire flows while a Try it runs.
- Drag an engine plate onto a job: `accepts(job, engine)` lights the job
  `is-over` (accept) or `is-over is-refused`; the drop calls
  `onPatch(job, engine, asFallback)` (⌥ on the drop, and only when the job
  already has a wire) or `onRefuse(job, engine, reason)`. Keyboard twin:
  with a job selected, Enter on a focused engine patches; ⌥Enter adds a
  fallback.
- `layout`: `board` (three columns) or `list` (the job list for a phone
  width: the open job, its engine, `Or` the alternatives as tap verbs,
  then the other jobs as tap verbs; every tap target is 44 px).
  `useSwitchboardLayout(ref)` measures the container (never the viewport;
  below 720 px it is `list`).
- `engineFoot` — the row at the bottom of the engines column (Add an
  engine).
- Geometry is pure (`switchboardGeometry.ts`): `plugPoint`, `wirePath` (one
  cubic per wire, both control points on the horizontal midpoint), and
  `patchChain` (first moves to the head; a fallback appends; no duplicate;
  at most four).
- Material: the §11 tokens with the canvas values as fallbacks
  (`var(--wb-well, #eef0f3)`); reduced motion stops the pulse and the lamp.


## Shared reading material

`ReadingDocument` is the document species behind `Material` and full
`AgentWords`. It uses the installed `markdownLanguage.parser` grammar; no
host defines its own Markdown blocks. Headings keep their semantic depth,
lists can nest, tables retain header cells, and fenced code retains source
whitespace. Table and code overflow stays in a keyboard-focusable local
`ScrollHint` well. Hosts provide the surrounding material and title.

Known note doors use their existing library Buttons. A qualified object
reference is a Button only when `refOpener` supplies a supported opener.
HTTP(S) links retain their label and open only on a press. Unsupported
schemes and repository paths show the label plus an inert destination;
there is no verified repository-file opener. HTML is text, images are alt
text, and rendering never fetches external material. Compact `AgentWords`
keeps its last-ask selection, marks and truncation, with inert links.

Capture preserves original line breaks and indentation within the existing
bounds and question secret filter. Historic flattened text stays as stored.


## ComposerWell — shared writing material (2026-10-21)

One presentation species for text plus an explicit action. Ask and the
DeskComposer retained by parked PR receipt replies compose it. The live
component gallery exposes the same species as an interactive specimen;
/companion opens Agents, not that parked PR screen. This extends the existing
PadGadget, StringGadget and Button species; it adds no draft or send authority.

- `children`: host-owned editor and optional retained selection material.
- `context?`: the current engine and real egress at the action boundary, or
  other host facts. Never derives routing or adds a network request.
- `capture?`: the host-owned MicButton. Disable the editor gadget's default
  mic when this slot is used; one capture path per editor.
- `actions?`: library Buttons. The host owns disabled, pending and callbacks.
- `details?`: optional host-owned in-flow material above the editor, such as selected text.
- `className?`: host geometry hook; the shared species owns paper, focus,
  editor/control spacing and narrow reflow.

The surface keeps context beside capture/actions while space permits. At the
560px surface breakpoint it wraps without overlap; plated targets own 44px.
Long engine names and failures wrap. The editor stays a real library gadget,
with the host's labels, refs, keys, value and voice scope unchanged. The well
never clears drafts, submits, starts recording, chooses an engine or stores
state. `patterns/conversation.css` owns shared document reading measure and
turn typography. Ask's intro/context remain host composition, and a restored
Thread uses the same Ask face through ThreadToAsk.

The species owns input/textarea font, paper, border, padding and vertical
resize. Hosts do not restyle those internals. The gallery's Conversation
composer is local state with a Preview action, not a provider or PR send.

`useReadingEndAnchor(ref, active)` preserves a reading viewport's bottom edge
across material and viewport changes only while its reader is at the end.
Reading above the end stays in place. `active` follows conditional reading
nodes; the hook owns no draft, engine or action state. Ask uses this shared
pattern so opening Tools keeps the answer verbs in reach.


## AskSourceFrame — captured source and return (2026-10-23)

Ask owns the Note handoff and its thread/draft. AskSourceFrame is the controlled
view for quote, fold state, Clear quote and Back to note. Back remains
outside the fold and reachable at narrow width while a run is pending. The
view holds no source, window, model or writer authority. Components Conversation
uses the exact view with local callbacks and a disabled composer mic.

The active Thought writer supplies saved body, qualified Note, selected UTF-16
range, source window and scroll. Returning validates saved and local draft
body before applying the captured range. Closed-window return queues for its
canonical opener; changed body preserves current work and reports SOURCE
CHANGED. This transient return capture is not server source freezing. Ask's
context is independent of floor selection; closing, removing About or starting
a new Ask changes Ask's owned context only.

Save as note keeps editable Markdown provenance. Only refs supported by
refOpener become Markdown destinations; other refs remain visible text. The
active Note editor has no link opener yet; saved-link click/return is follow-on
scope, not certified from these bytes. Thread
links use the actual returned thread id. Components proves presentation with
isolated IO, not adoption of a shared conversation controller or live inference.


## ReadingObjectLinks — explicit doors beside editing (2026-10-23)

Public export from desk/surface. Props: source Markdown and host-owned
onOpen(ref). Only real Link nodes with supported qualified object destinations
become Buttons; code, image and HTML pseudo-links are ignored. Destinations are
deduplicated in source order. Labels reuse parsed inline rendering and accessible
text, including escapes and emphasis. Parsing has no fetch or opener effect.
Ordinary editor clicks keep their selection/caret behavior.

ThoughtDocumentPane owns the in-flow Linked items fold beside the editable
body. Its short list scrolls locally without moving the frame off the work
area or clipping editor/footer; narrow targets are 44px. The exact pane in
Components Editing uses local callbacks, not production object opens. Unsupported
refs stay text in the document. This gives saved source/thread destinations a
real door in the active Note route, not the retired NotePullout reader.

Thought-to-Ask captures immutable origin range text plus canonical source
snapshot after flush. Clearing the quote changes prompt material, not the
origin range or source version. Whole-Note Ask can restore a collapsed caret.
The server validates that version and keeps admitted text for the turn while
preserving original About/Memory policy; it does not make Note context exclusive.
Source changed requires an explicit fresh source handoff, never silent retry
with a newly read version. Room saved-task Resume pinning remains separate.
