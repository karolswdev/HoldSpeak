# Phase 167 settled design — the whole Room on the surface library

Drafted by the orchestrator 2026-09-03 after reading all eight faces'
verdict shots (drift-audit.md) and the 166 reference design
(phase-166 assets/settled-design-face.md). The mockups the owner
judges BEFORE any rebuild: the Room in Use canvas
(https://claude.ai/code/artifact/1dd81936-2c1a-484f-a78e-f56e5a5cf22b —
sixteen artboards, eight faces × 1440/393; sources under
assets/mockups/, shots under assets/story-01-shots/). Status: counsel read 2026-09-03 —
RATIFY-WITH-CONDITIONS, eighteen findings (3 M, 9 S, 6 N) ALL paid
below before the owner sees it. Awaiting the owner's word.

## The one sentence

Every Rooms face is composed ONLY from the surface library — one
identity band, one ledger grammar, one chip vocabulary, one plan
species for anything that runs, one scroll-hint, one footer — so the
eight faces built in eight sittings read as ONE Room, and none of
them ever speaks a sentence the user did not write.

## D0 — the spine (what every face shares)

- **The window** is unchanged chrome: gems, mono title, the WINGS
  (SurfaceWings: `TIMELINE · DECISIONS · SEARCH · ASK` — all four
  KEPT with their keyboard handlers, empty states and the decision
  promotion/supersede verbs; nothing retires). The Room OWNS the
  body; the three postures (Review · Updates · Steward — the verbs
  the Room chrome already carries) replace the working field under
  the identity band; wizards own the whole body while open.
- **SurfaceIdentity** (new species, §D9): the project's name (the
  Primary step, 15px/600), then ONE chip row built ONLY from what
  the wire carries (model.ts:40-57: `lifecycle`, `posture`,
  `postureReason`, `revision`, read time) — StateChip lifecycle
  (`Active` success / `Archived` idle) · StateChip posture (the
  posture word; `postureReason` as its title, never a sentence on
  the face) · token `REV 9` (uppercase, as today, only when > 0) ·
  humanTime of the read — then the owner's own purpose as one line
  and the outcome as a target token row (`◎ zero-downtime cutover by
  Q1`). NO health chip: the Room has no health field (Article VI —
  nothing fabricated when absent). The user's sentences are his
  content; they stay, folded past two lines (Disclosure `more`).
  Purpose/outcome NEVER appear as two paragraphs again.
- **The ledger grammar**: every list is SurfaceLedger →
  SurfaceLedgerRow with its REAL props (Surface.tsx:727-742): `lead`
  (a kind emblem from the ratified mold: risk ▲, dependency ⫘,
  milestone ◆, watch ◉, run ▶, source ⌁, update ✎), `primary` (never
  truncated to "Schedu…" — at 640 the row owns the width and the
  cells wrap under), `time=` ALWAYS passed (the 52px-column law),
  `cells` (the chips and tokens, in order), and ONE new prop
  `trailing` (§D9: a quiet verb or a chevron, right-aligned, outside
  `cells`). Sections are SurfaceSection with a count chip.
- **The chip vocabulary** — the only ways to say state, source and
  egress: StateChip (the seven states, icon + text, never color
  alone; severities `Critical/High/Medium/Low` map to failure/
  warning/idle/idle with the word), ProvenanceChip (`gh ·
  github.com`, `acli · <site>`, `model · <host>`, `deterministic`),
  EgressChip on every control whose press leaves the machine, count
  chips on sections, quiet tokens (`rev 9`, `ai-delta-002` only
  inside a Disclosure — no raw ids on chips, the 162 law).
- **ProgressPlan is the species for anything that runs**: a wizard's
  steps, a connection test, a steward run. Each step = name +
  rate/count + a done bar; a failing step carries its StateChip and
  its recovery in a well with COPY. Never a column of identical
  status words.
- **ScrollHint** on every scrolling well (one species, axis prop),
  the Door's fade + chevron, both widths.
- **SurfaceFooter** on every face: egress slot (ProvenanceChip /
  EgressChip) · receipt slot (Receipt `Read 13:28:04`) · verbs (one
  primary, the rest quiet). Back lives here, never floating.
- **Absent, loading, degraded**: every face keeps its SurfaceState
  `loading` / `empty` / `error` (with Retry) and the per-section
  DegradedNotice exactly as today (ProjectRoomCore.tsx:384-401,
  556-564; ReviewPosture.tsx:601-604; StewardPosture.tsx:546-555) —
  the redesign changes composition, never a state.
- **Keyboard**: every posture's grammar is UNCHANGED (Review's
  j/k/a/e/l/x/z, the layered Escape, Cmd+Enter; roving rows on
  every ChoiceCardGroup and ProgressPlan).
- **MicButton** in every text well (a face with no text well — the
  Review queue — has none; its Edit fields carry it). **No prose**:
  labels are tokens,
  states are chips, commands are wells with COPY, help is a
  placeholder inside the well. **393**: one column; cards stack;
  ledgers drop the time cell; identities wrap, never ellipsize.
- **The mold**: bevelled wells, mono uppercase labels with tracking,
  the ember accent for the one primary verb and the selected card,
  hover = the well lifts, pressed = the bevel inverts. Emblems from
  phase-135 assets/icon-palette.png (pixflux).

## D1 — the Room (ProjectRoomCore)

- Body = SurfaceIdentity → the posture strip (SurfaceVerbs with the
  new `active` prop, §D9: `Review` with count chip 3 · `Updates` ·
  `Steward`; status slot = StateChip of the steward's last run) →
  SurfaceColumns (2 at 640, 1 at 393):
  - Left **FOCUS**: SurfaceSection per kind (`RISKS 2`,
    `DEPENDENCIES 1`, `MILESTONES 2`), rows: emblem lead · primary ·
    StateChip severity · due token (`2026-09-15`, warning when
    within 7 days) · time · trailing chevron (opens the item's
    Disclosure in-flow).
  - Right **THE WEEK**: MetricStrip (`MEETINGS 0 · RESOURCES 0 ·
    WATCHES 2 · CHANGES 8`) then SurfaceStream → SurfaceStreamDay →
    SurfaceStreamEntry for CHANGES — an entry is `emblem · what
    changed · ProvenanceChip (steward/you/model) · time`; eight
    "Item created · kind · just now" lines collapse to one entry
    `8 items created · REV 9` with a Disclosure.
- The ASK wing keeps ProjectAsk whole (its runAsk, grounding
  receipt, contextual assignment, error handling); only its markup
  moves onto the desk chat well species (the Thread pullout's
  composer) — its EgressChip is COMPUTED from the run's model
  assignment at runtime (ProjectRoomCore.tsx:151-155), never a
  static host. TIMELINE, DECISIONS and SEARCH wings keep their
  ledgers, verbs and mic; their rows adopt the ledger grammar.
- Footer: ProvenanceChip `project · payments-platform` · Receipt
  `Read 13:28:04` · `Refresh` quiet.

## D2 — the interview (SetupRoot + SetupInterview + SetupBrief + ClarifyStep)

- Top: ProgressPlan `Outcome · Notice · Sources · Review` (the step
  you are on lit; "STEP 2 OF 4" is gone).
- The question is a SurfaceSection label (`OUTCOME`, `NOTICE`,
  `SOURCES`), the helper is the well's placeholder (`What would you
  want noticed without being asked?`), the answer is ONE StringGadget
  well (multi-line, mic, COPY absent) with the primary verb `Next`
  in the footer.
- Answered steps collapse to ledger rows above: lead = step emblem,
  primary = the answer, trailing = `Edit` quiet. Clarify questions
  (ClarifyStep) are the same rows with a StateChip `Needs an
  answer`.
- Right column (640) / below (393): **THE BRIEF** as SurfaceFacts
  that fill as you answer (`OUTCOME`, `NOTICE`, `SOURCES`), each an
  editable fact (EditInPlace) — the brief IS the record.
- Suggestions (SuggestionCards): ChoiceCardGroup, one card per
  proposed watch (emblem = provider, label = the watch, facts =
  cadence token · action chip · ProvenanceChip); GitHub/Jira cards
  open their wizard in place (D3/D8).
- Footer: receipt line `2 of 4` (the footer's receipt-line text —
  a LampGadget is boolean, never a counter) · `Cancel setup` quiet ·
  primary `Next`.

## D3 — the GitHub wizard (ProviderWizardStep) reaches Jira parity

- Connection = ONE ChoiceCard (emblem gh, label `github.com`, summary
  the gh login, facts StateChip `Connected`/`Sign in`/`gh missing` ·
  ProvenanceChip `gh · github.com`); `Sign in` opens the fold: the
  exact `gh auth login` in a well with COPY + one verb `Recheck`.
- Repository = ChoiceCards (emblem owner initial, label
  `owner/repo`, facts `default branch` · `open issues` · `open PRs`
  counts · ProvenanceChip); a search StringGadget with mic above.
- Population = ONE gadget sheet: ITEMS (issues · pull requests ·
  releases CheckGadgets), LABELS (StringGadget), BRANCH
  (CycleGadget), ADVANCED (a query StringGadget, mono).
- The test = ProgressPlan `Auth · Read owner/repo · Fetch N items ·
  Baseline ready` + Receipt; matches = display step `12 items · 2
  calls · 0.7s` + ledger rows (`#412 · title · StateChip · time`).
- A conflict proposal (the 161 evaluation) renders as a row
  `Conflicting sources · 2` with two ProvenanceChips and a
  Disclosure holding the hashes in a mono well — never a wall.
- Footer: EgressChip `github.com` on Check/Discover/Test · Back ·
  primary `Review and activate`.

## D4 — the activation review (ActivationReview)

- One SurfaceLedger **WHAT WILL RUN**: a row per watch — lead
  provider emblem, primary the watch name, tokens cadence · action
  chip · ProvenanceChip, trailing a CheckGadget (on by default) — no
  `<dl>`, no raw buttons.
- **THE BRIEF** SurfaceFacts (outcome · notice · sources) with
  EditInPlace.
- The baseline: ProgressPlan one-step `Baseline` per provider that
  lights at finalize (the 166 false-baseline law visible).
- Footer: EgressChips per provider host · Back · primary `Activate`.

## D5 — the Review posture (ReviewPosture)

- The posture strip shows `Review` lit with the count chip; the
  queue is a full-width SurfaceLedger: SurfaceSection per kind
  (`RISK ATTENTION 2`, `REVIEW FLAGS 1`, `OBSERVATIONS 5`), rows =
  StateChip severity lead · primary in full · ProvenanceChip source
  · time · chevron.
- Selecting a row expands it IN FLOW (Disclosure): SurfaceColumns
  (2 → 1 at 393) holding two SurfaceFacts titled `CURRENT` and
  `PROPOSED` (`Text`, `Owner`, `Due`, `Lane`) with the changed fact
  carrying the accent — no SurfaceSplit (that species is
  master/detail and hides its detail when narrow); chips
  `Materiality High` · `Kind Risk attention`; the id inside the fold
  as a quiet mono token.
- Verbs on the expanded row: primary `Accept` · `Edit` (its fields
  carry the mic) · `Defer` (two-step as today: arms, a date well
  appears in flow, confirm) · `Dismiss` (SurfaceVerbs); undo (z)
  restores; the next row lights after a verb. Keyboard grammar
  unchanged from 160.
- Footer: the receipt-line tally as today (`3 left · 2 accepted ·
  1 dismissed`) · Receipt after each verb · `Close`.

## D6 — the Update posture (UpdatePosture)

- **DRAFTS** ledger: lead ✎, primary title, tokens ProvenanceChip
  `deterministic`/`model · <host>` · StateChip `Draft`/`Published`,
  time, chevron.
- The document: DeskEditor (desk/components — the one sanctioned
  import outside the barrel, noted in contract.md by 03) above a
  **SOURCES** well — ledger rows (emblem · source · ProvenanceChip ·
  time); each document section carries a CitationChips row (the
  species takes a `refs` array per section — the 162 claim-chips
  grammar, not one chip per word); an unverified claim is an
  ActionNotice in flow, never a banner across the editor.
- Footer: EgressChip (`model · <host>` only when the model drafter
  ran; `deterministic` otherwise — the 164 badge law) · Receipt
  `Published rev 2 · 09:02:11` · verbs `Save` · `Copy` · primary
  `Publish` (three separate honest commands).

## D7 — the Steward posture (StewardPosture)

- **Attention first**: an open circuit renders at the top as an
  ActionNotice + the circuit ledger (source · StateChip
  `Unreachable` · streak token · `Retry` quiet) — before any
  configuration.
- **THE RUN**: ProgressPlan of the six phases `Observe · Compare ·
  Propose · Act · Verify · Record`, each with its count and duration
  (`Observe · 2 sources · 3 calls · 0.9s`; `Propose · 7`; `Act · 2
  effects`) and its receipt refs as chips; a stopped run shows the
  step it stopped on with StateChip `Stopped`. Eleven COMPLETED
  words never again.
- **RUNS** ledger: lead StateChip, primary `Run 12 · manual` /
  `Run 13 · scheduled`, tokens `2 effects` · `1 door item`, time,
  chevron (opens that run's plan).
- **POLICY** as one GadgetGroup: `Unattended` SurfaceToggle · `Every`
  StepperGadget (unit: min; WIRED BY 02 — inert until the cadence
  write lands; the change then shows as a `next 14:05` token) ·
  EFFECTS CheckGadgets · `Max actions` · `Retries` · `Cooldown`
  Steppers. The grant (today a prose sentence, StewardPosture.tsx:
  283-361) STAYS as the ledger entry of what unattended means, but
  as a SurfaceFacts row of tokens under the toggle: `WHILE ENABLED ·
  every 60 min · create items · update items · max 5 / run` — the
  disclosure kept, the sentence retired. Save is the footer's
  primary while dirty.
- Footer: EgressChip per source host · Receipt `Last run 13:28:04`
  · verbs `Stop` quiet · primary `Run now`.

## D8 — the Jira wizard (JiraWizard): the reference, kept

Unchanged in composition (166 D1-D5 hold). Only :74-77's raw px
become tokens (03). It appears in the mockups so the whole-Room sheet
shows the grammar the rest now speak.

## D9 — the new species (the 03 list)

New species and props, with their contracts (03 builds exactly these):

| Species / prop | Shape | Composes |
| --- | --- | --- |
| `SurfaceIdentity` (new) | `name: string` · `chips: ReactNode` (StateChips + tokens, one row, wraps at 393) · `purpose?: string` (one line, folds past 2) · `outcome?: string` (rendered as a target token row) · `fold?: ReactNode` (Disclosure body) · `trailing?: ReactNode` (the read-time token) | StateChip, Disclosure, the Primary type step |
| `SurfaceLedgerRow.trailing` (new prop) | `ReactNode` — one quiet Button or a chevron, right-aligned after `cells` | — |
| `SurfaceVerbs.active` (new prop) | `string` — the verb key rendered lit (`aria-current`), with an optional count chip per verb via children | — |
| `ScrollHint` (promoted) | `axis: "x" \| "y"` · `scrollRef` — one implementation from DoorBoardLane.tsx:255-268 + steward/model.ts:253-267 | — |
| the posture strip | a composition: SurfaceVerbs(active) — no species | — |
| the comparison | a composition: SurfaceColumns → 2 × SurfaceFacts — no species | — |
| the policy sheet | a composition: GadgetGroup → GadgetRow × (SurfaceToggle, StepperGadget unit=min, CheckGadget×n, StepperGadget×3) + SurfaceFacts (the grant tokens) — no species | — |

Everything else already exists in the barrel. EgressBadge
(desk/setup.ts) delegates to EgressChip. DeskEditor stays where it is
and is named in contract.md as the one sanctioned non-barrel import.

## D10 — laws

No sentences the user did not write. Egress exactly where egress
happens. Numbers over adjectives (counts, rates, durations). A face
that needs a species no other face composes is a finding. 393 =
one column, nothing ellipsizes an identity. Feature CSS lays out,
never restyles. Every glass rig re-shoots; the orchestrator reads
every PNG against these mockups before the owner does.
