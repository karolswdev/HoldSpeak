# HS-202-05 - The type-scale ruling, then the tokens

- **Project:** holdspeak
- **Phase:** 202
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

From the surface inventory of 2026-09-20 (`docs/internal/SURFACE-INVENTORY-2026-09-20.md`, §6 story 05; appendices 01–04; Astra's check `docs/internal/checks/surface-inventory-astra.md`). The Seven Tenets govern: first-use first (2), one obvious move (3), the component framework (5), Workbench 2.0+ (6); Articles III and VI; UX-CANON A.

## Scope

- **In:** A design beat first: settle the 11 px caption allowance, the 12 px floor, and the three type roles (display/body/mono) between canon and the census rule, with counsel; then apply at the tokens (floor, muted-token contrast, the dense Button's hit ownership at 393 verified by hit testing, not rectangles); the broad M7/M8/M10 numbers re-measured as diagnostics
- **Out:** everything the inventory's §6 ledger records; faces the five owner jobs do not touch; the broad census numbers as gates (they are diagnostics re-run at phase close).

## Acceptance criteria

- [ ] the ruling recorded in UX-CANON and DESIGN_SYSTEM; the first-use screens pass AA and the hit test
- [ ] Every change has a fence proven red first on a real isolated hub; shots at 1440 and 393 in this story's assets; the first-use smoke (story 01) green after the change.
- [ ] Every verb the library Button; no prose; no modal; no counter of zero; one filled primary per window; labels in ASD-STE100.

## Test plan

- **Unit:** the fences the story names; vitest for face rules.
- **Integration:** the first-use smoke at both widths; the focused rigs the story touches.
- **Manual / device:** shots; story 06 is the owner's sitting.

## Notes / open questions

Lanes are assigned at build time under TWO-BRAINS §4 (default: Astra takes the backend and verification-harness work, Muad'Dib the faces; either brain checks the other's built lane before merge).

### The 126 ember contrast pairs — the build ledger

The ruling (§4) hands this story the 126 ember observations that a gray
change cannot fix: 105 light-on-ember and 21 ember-on-dark. Source:
`docs/internal/surface-inventory-2026-09-20/census.json` at head
`93f9524f`. Counts are observations, not unique controls.

**The arithmetic first, because it decides every line below.** On
`--accent` `#a86e4a` (relative luminance 0.1997) NO light foreground
reaches 4.5:1: `--text-on-accent` `#f2f3f5` gives 3.79:1 and pure white
gives 4.20:1. Only near-black passes — `#14161c` gives 4.30:1 and pure
black 4.99:1. On `--accent-hover` `#bc8058` white gives 3.30:1 and black
6.37:1. So every light-on-ember line has exactly two lawful exits: make
the label dark, or stop painting the ember behind small text. Ember AS a
text colour never passes either: on the four recorded dark grounds it
reads 3.50, 3.92, 4.01 and 4.30:1.

| Consumer | Obs | Pair | Ratio | Faces | Decision |
| --- | ---: | --- | ---: | --- | --- |
| `button.btn.btn--primary` | 59 | `#f2f3f5` on `#a86e4a` | 3.79:1 | 16 faces incl. `app-chair`, `app-live` | LEAVE — needs an owner ruling. The library Button is this lane's species, but the only fix is a dark `--accent-on`, which repaints every filled primary in the product. The ruling keeps the ember palette (§5) and the owner sees shots before a look change. Ready for the sitting with the arithmetic above. |
| `span.gadget-transport-word` | 16 | `#f2f3f5` on `#a86e4a` | 3.79:1 | `app-chair`, `app-components`, `win-switcher` | LEAVE — the Talk key's word rides the same accent fill; it moves with the `--accent-on` ruling, not before it. |
| `span.desk-sortable-table-direction` | 6 | `#a86e4a` on `#1c1f27` | 3.92:1 | `app-floor`, `win-repository`, `pullout-repository` | LEAVE — a sort arrow on a face no first-use job touches. The exit is `--text` for the glyph, decided with the table's own story. |
| `button.desk-chip.is-primary` | 6 | `#f2f3f5` on `#a86e4a` | 3.79:1 | `win-workbench`, `pullout-workbench`, `pullout-workflow` | LEAVE — same accent fill, same owner ruling; and the desk chip is not a first-use control. |
| `span.desk-ask-glyph` | 4 | `#a86e4a` on `#242833` | 3.50:1 | `app-ask` | LEAVE — a `✦` glyph with no first-use reach. |
| `span.gadget-transport-glyph` | 4 | `#f2f3f5` on `#a86e4a` | 3.79:1 | `app-components` | LEAVE — the component catalog, not a product face. |
| `button.surface-choice-confirm-btn` | 4 | `#f2f3f5` on `#a86e4a` | 3.79:1 | `app-components` | LEAVE — same catalog. |
| `span.gadget-chip.gadget-chip-egress` | 4 | `#a86e4a` on `#1a1d25` | 4.02:1 | `state-delivery` | LEAVE — the egress chip's ember IS the egress signal (UX-CANON: egress where egress happens). Changing its colour is a signal decision, not a contrast fix. |
| `span.desk-panepicker-id` | 4 | `#a86e4a` on `#14161c` | 4.29:1 | `state-terminal` | LEAVE — the terminal pane id; no first-use reach. |
| `span.desk-deck-glyph` / `-label` / `-kind` | 12 | `#f2f3f5` on `#a86e4a` | 3.79:1 | `state-palette` | LEAVE — the palette's selected row wears the accent fill; it moves with the `--accent-on` ruling. |
| `strong` | 4 | `#ffffff` on `#a86e4a` | 4.20:1 | `app-floor`, `win-switcher` | LEAVE — already pure white and still short; proof that no light foreground can close this pair. |
| `span.desk-list-attention` | 3 | `#a86e4a` on `#1c1f27` | 3.92:1 | `app-floor` | LEAVE — the desk floor's attention token; no first-use reach. |

No line was changed. Every one of the 126 sits on a face this lane does
not touch, or behind the one accent ruling the owner must make. The
ruling's own words: "They are not fixed by gray."

### The 12 px floor ledger — what a token change could not move

The ruling (§4) says it plainly: "Raw 6–11 px declarations do not change
when a token changes." `tests/e2e/test_hs202_05_first_use_type_floor.py`
measures the six first-use screens at both widths and records 24
consumers (58 screen × consumer signatures) whose readable text still
computes under 12px. None of them reads a type token; each is a raw
`font-size` or `font:` in a face this lane does not own. The fence FAILS
on any consumer outside the recorded set and PRINTS what heals, so the
set can only shrink.

| Consumer | px | File | Decision |
| --- | ---: | --- | --- |
| `h3` (section head) | 10 | `desk/surface/surface.css:60` (`.surface-section-head h3`) | LEAVE — the section label grammar, `--font-mono` 10px raw. The largest single line in this ledger; its own story. |
| `kbd` (menu bar keycap) | 10 | `desk/components/chrome-menus.css:750` | LEAVE — the menu bar is HS-202-03's lane. The tool-shelf keycap beside it already reads `--font-size-xs` (`chrome-menus.css:363`), so the token is right and only this one rule is raw. |
| `.arrival-meeting-badge` | 10 | `desk/chair/chair.css:443` | LEAVE — the Chair's first-use control markup is HS-202-03's. |
| `.gadget-chip.gadget-chip-egress` | 10 | `desk/surface/gadgets.css:845` | LEAVE — the egress chip; same species story as its ember pair above. |
| `.gadget-transport-word` | 9 | the Talk key | LEAVE — the lowest reading on the path, and the loudest candidate for the next story. |
| `.desk-wing`, `.desk-wing.is-on` | 10 | `desk/components/pullout.css:334` | LEAVE — the wings are HS-202-03's lane by the brief. |
| `.desk-dock-label` | 10 | `desk/components/dock.css:128` | LEAVE — the Dock is HS-202-03's lane. |
| `.surface-footer-receipt-line` | 10 | `desk/surface/surface-footer.css:72` | LEAVE — the receipt line. |
| `.meetings-stream-fact`, `.meetings-stream-no-transcript`, `.meetings-stream-compact-facts` | 10 | `desk/surface/surface.css:3806,3822,3855` | LEAVE — the Meetings row grammar. |
| `.surface-well-head` | 10 | `desk/surface/surface.css:354` | LEAVE — the well's caption. |
| `.surface-token`, `.surface-token-axis` | 10/11 | `desk/surface/surface.css:1444` and the `.surface-token` family | CANDIDATE — the closest thing to the caption step the ruling moved; binding it to `--desk-surface-label-size` is a one-line token binding per rule. |
| `.prefs-receipt` | 10 | `desk/surface/surface.css:2518` | LEAVE — Settings' receipt line. |
| `.surface-state-chip` | 10 | `desk/surface/patterns/state-chip.css:5` | LEAVE — the state chip species. |
| `.concierge-section-label`, `-receipt`, `-hardware-token`, `-checked-at` | 11 | `features/concierge/concierge.css:61,454,29,40` | CANDIDATE — four raw `font: … 11px …` declarations on the Models face, all captions; the caption step is now 12px. |
| `.thought-note-ask-label` | 11 | `desk/thought-workspace/thought-workspace.css:187` | CANDIDATE — the Thought band's caption. |
| `.thought-note-reads` | 10 | `desk/thought-workspace/thought-workspace.css:343` | LEAVE — a reads receipt. |

Seven CANDIDATE consumers are pure 11px caption bindings and would close
on one token each. They are named here rather than changed: the brief
for this lane names `global.css:152` and `surface.css:2979,3016` as its
touched consumers, and 196 raw 9/10/11px declarations exist across the
CSS. That sweep is its own story.

### The diagnostic re-run — before → after

Two instruments, because one could not finish.

**1. The census walk, COLD desk** (`scripts/surface_census_walk.py --desk
cold --widths 1440,393 --no-shots --only <the nine first-use face ids>`).
BEFORE is `docs/internal/surface-inventory-2026-09-20/census.json` at head
`93f9524f`; AFTER is this branch. The two heads are 10 commits apart, so
a delta below carries stories 01–04 as well as this one.

| Face @ width | M7 small text | M7 small targets | M8 fails / assessed | M10 stacks |
| --- | ---: | ---: | ---: | ---: |
| `app-chair` @393 | 6 → **4** | 6 → 6 | 1/13 → 1/14 | 3 → 3 |
| `app-chair` @1440 | 6 → **4** | — | 1/13 → 1/14 | 3 → 3 |
| `app-meetings` @both | 0 → 0 | 2 → 2 | 0/2 → 0/2 | 2 → 2 |
| `app-models` @both | 0 → 0 | 2 → 2 | 0/2 → 0/2 | 2 → 2 |
| `app-settings` @both | 0 → 0 | 2 → 2 | 0/2 → 0/2 | 2 → 2 |
| `settings-settings` @both | 6 → 0 | 6 → 2 | 0/39 → 0/2 | 2 → 2 |
| `wing-meetings-review` @both | 6 → 6 | 7 → 7 | 0/9 → 0/9 | 2 → 2 |

Read it honestly:

- **`app-chair` 6 → 4 is this story's token change.** The three library
  Buttons the Chair leads with — `Connect calendar`, `Choose an engine`,
  `Generate` — measured 11px before and 12px after. That is
  `global.css:152` bound to `--font-size-xs`. Their painted widths grew
  with the type (124 → 133, 71 → 76 px) and their heights did not
  (24 and 28 px, unchanged).
- **M7 small targets does not move, and cannot.** The check measures the
  painted rectangle; the 44px area is a transparent halo. The ruling
  said this in advance: "Pseudo-elements can leave rectangles unchanged
  while hit ownership passes." `test_hs202_05_button_hit_ownership.py`
  is the instrument that can see the area, and it proves nine points per
  Button with `elementFromPoint` and a real pointer.
- **The one M8 fail left on the Chair is an ember pair, not a gray one.**
  It is `Talk` at 3.79:1, `#f2f3f5` on `#a86e4a` — row 2 of the ember
  ledger above, left by decision.
- **`settings-settings` is not comparable.** Assessed text leaves fell
  from 39 to 2, so the leg opened a different face; the 6 → 0 is a
  content change, not a type fix.
- **M10 never moved.** The `--font-sans` alias revives declarations that
  already named `--font-ui`, so no stack count changed on these faces.

**2. The census walk, RICH desk: NOT RUN.** Three attempts hung in
`seed_rich` at `POST /api/inference/model-library/define-endpoint`
(`scripts/surface_census_walk.py:610`), which probes the LAN engine at
`192.168.1.43:8080`. The endpoint answers `200` to a direct `curl` from
this lane, so the block is in the hub's own probe, not in reachability.
`Api.call` uses `page.evaluate` with no timeout, so the seed waits
forever. This is a rig limit, not a result. The diagnostic is not a
gate; the measured substitute below covers the same six screens.

**3. The measured substitute — the first-use screens, at this head.**
`test_hs202_05_first_use_type_floor.py` reads the same M7/M8 logic on
the six screens the owner's first-use path actually crosses, and writes
`assets/story-05-shots/first-use-type-floor-{1440,393}.json`.

| Screen | Text leaves 1440 / 393 | Under the 12px floor | `--text-faint` under 4.5:1 |
| --- | ---: | ---: | ---: |
| arrival | 42 / 28 | 6 / 5 | **0 / 0** |
| meetings-ledger | 58 / 44 | 14 / 13 | **0 / 0** |
| meetings-record | 66 / 50 | 17 / 15 | **0 / 0** |
| thought | 57 / 43 | 12 / 11 | **0 / 0** |
| models | 60 / 46 | 14 / 13 | **0 / 0** |
| settings | 86 / 72 | 22 / 21 | **0 / 0** |

The contrast column is the story's result: **zero** `--text-faint`
observations under 4.5:1 on any first-use screen, at either width. The
same rig with `HS202_05_FAINT_OVERRIDE=#767e8d` — the pre-ruling gray
painted onto the same live screens — records 2 failures at 4.38:1 on
Models at each width. That is the red-then-green for the colour change,
taken on the real faces.

The floor column is the ledger above: raw declarations a token change
cannot reach.

### Reading the evidence file

Nine captures. Three exit non-zero on purpose or by accident, and each
is named here so no one reads a failure as a result:

1. `exit 1` — the RED leg of the hit-ownership and disabled fences, run
   against `git show HEAD:web/src/styles/*` in a scratch directory via
   `HS202_05_CSS_DIR`. The shared tree was never moved.
2. `exit 0` — the same two fences plus the first-use fence, GREEN.
3. `exit 1` — the RED leg of the contrast rule:
   `HS202_05_FAINT_OVERRIDE=#767e8d` paints the pre-ruling gray on the
   six live first-use screens and records 4.38:1 on Models at both
   widths.
4. `exit 0` — the four named rigs, 27 passed.
5. `exit 0` — HS-202-01's first-use smoke (copied in from
   `feat/hs-202-01-fence`, run, removed), 2 passed, zero `FAIL:` lines.
6. `exit 1` — **a flake, not a result.** `npm run check` recorded
   `1 failed | 2721 passed` while three browser processes from a wedged
   census walk were still on the machine. A clean re-run of `test:web`
   immediately after was `290 passed (290) / 2722 passed (2722)`.
7. `exit 0` — `npm run check` again on a quiet machine, every step
   green, including `2722 passed (2722)`.
8. `exit 0` — the cold census walk, 12/12 legs measured.
9. `exit 0` — the three fences green after the last edit.

## Counsel round

Astra's verdict on #597 was **DO-NOT-RATIFY**. Five findings; all five
are answered below, each red first.

### 1. The ember on the first-use screens — the ledger was too wide

The counsel is right. The ruling requires readable pairs ON TOUCHED
FACES before closure; a blanket deferral of all 126 contradicts it.
The first contrast gate read `--text-faint` alone, so green established
nothing about first-use AA.

**The gate now reads every text leaf on every first-use screen** and
splits each failure into `faint`, `ember` or `other`. Faint and ember
are gated; anything else prints as measured residue. RED before the
fix, at both widths:

```
arrival@393        M8[ember] 3.79:1 < 4.5 at  9px on rgb(168,110,74): 'Talk'
models@393         M8[ember] 3.79:1 < 4.5 at 12px on rgb(168,110,74): 'Continue'
thought@1440       M8[ember] 3.79:1 < 4.5 at 12px on rgb(168,110,74): 'Finish'
… 20 observations across six screens × two widths
```

**The decision: option (a), a darker ember for text-bearing fills.**
Option (b) cannot work. `--accent-press` `#936041` is DARKER than
`--accent`, so a near-black foreground fails there (3.99:1 with pure
black) while a light one passes (4.74:1). No single foreground clears
all three accent states. Moving the plate does.

`--accent-ink` is one stop down the same forge-ember ramp, and the
ramp already held two of the three steps it needs:

| Token | Value | Ramp step | With `--text-on-accent` |
| --- | --- | --- | ---: |
| `--accent` (unchanged, non-text duties) | `#a86e4a` | orange.500 | 3.79:1 |
| `--accent-ink` (**new step**) | `#8a5a3d` | orange.650 | **5.24:1** |
| `--accent-ink-hover` | `#936041` | orange.600 | **4.74:1** |
| `--accent-ink-press` | `#834f32` | orange.700 | **6.04:1** |

Hover is still lighter than rest and press still darker, so the
interaction grammar is intact. One new hex enters the palette.

Bound at three text-bearing fills: the filled Button
(`web/src/styles/global.css`, rest / hover / active), the Chair's Talk
key (`web/src/desk/chair/chair.css` — its hover was
`color-mix(… var(--accent) 85%, white)`, which lifted the plate back
over the ceiling), and the transport key's key-down state
(`web/src/desk/surface/gadgets.css`). `--text-on-accent` does not move.

**This is the look the owner reviews at the sitting.** Shots:
`filled-primary-before-after-1440.png`, `…-393.png` — the same three
controls on both plates, with the measured ratio printed on each row.
He may overrule the look; the numbers pass now.

Off-path ember pairs stay ledgered in the table above.

**A second colour defect fell out of the same gate.** Five consumers
spelled `var(--faint, #767e8d)` — and `--faint` is not a token in this
product. The fallback won, so those labels were pinned to the
pre-ruling gray and the ruling could not reach them:
`features/concierge/concierge.css:43` (the Models face, 4.38:1),
`features/project-room/door/door.css:43,51,179,276`, plus a stale
fallback at `desk/surface/gadgets.css:194`. All six now read
`var(--text-faint)`.

**And a third, in the instrument.** The census's own M8 block
(`scripts/surface_census_measure.js`, `bgOf`/`over`) composites a
translucent layer onto a translucent backdrop as if the backdrop were
opaque, then marks the result opaque. A dark chip fill over a white
hairline wash therefore read as `rgb(184,184,184)` and produced a
1.29:1 that does not exist on the glass. This rig gates on the number,
so it does source-over properly and keeps walking until the stack is
actually opaque. Any census M8 figure for stacked translucent layers
carries that error.

After all three: **zero gated contrast failures and zero residue** on
the six screens at both widths.

### 2. "Each library Button" vs the chrome species

The canon over-promised. `Signal.tsx` has four variants today
(`primary | secondary | ghost | danger`) and HS-202-03 adds `chrome`
for the rows that replace raw wing tabs, menu rows and dock chips. A
44 px halo on a strip row would reach over its neighbours.

Canon now says **plated** Button, and states the chrome contract:
the strip owes the row its target, at least 44 px high at 393; measure
the row, never add the halo. `docs/internal/UX-CANON.md` §C rule 4 and
`docs/internal/DESIGN_SYSTEM.md` rule 4.

The fence measures the real strips at 393, and the product does NOT
keep that promise yet:

| Strip | Rows seen | Min | Max |
| --- | ---: | ---: | ---: |
| dock chip | 86 | **22px** | 44px |
| wing tab | 10 | **23px** | 23px |

Named rows under 44: the wing tabs `Outcomes` / `Review` / `Record` /
`Artifacts` (23px), and the dock's `Overview` / `Reset layout` (22px),
`◌Hide the menus` / `Change places` (36px), `Record a meeting` (40px).
Recorded, not gated: those three strips are HS-202-03's lane. The
fence prints them every run so the list can only shrink.

### 3. The third `font:` shorthand consumer

Found and probed: `web/src/desk/surface/surface.css:3117`,
`.model-library-add-choices > button`. (Astra cited `:3109`; the
comments this round added shifted it eight lines. Line numbers below
are the ones in the tree now; the probe script prints its own
pre-comment labels.)

| Consumer | BEFORE | AFTER |
| --- | --- | --- |
| `surface.css:2985 .model-library-row-copy strong` | 13px / 400 / Inter | 13px / **600** / Inter |
| `surface.css:3026 .model-library-repair` | 13px / 400 / Inter | **12px / 500** / Inter |
| `surface.css:3117 .model-library-add-choices > button` | 13px / 400 / Inter | 13px / **600** / Inter |
| `surface.css:2990 .model-library-row-copy small` (control) | 12px / 500 / JetBrains Mono | unchanged |

The third is the only one on a raw `<button>`, and it answers an open
question from the first round: a raw `<button>` with an author font
declaration inherits when that declaration dies — it does NOT fall to
the UA's Arial. The Arial in the census's M10 counts comes from raw
buttons with **no** declaration at all.

### 4. The viewport exception, written into UX-CANON D

Recorded as a shape, not a licence: ONE device rule that sets a target
size and stacks no content. `docs/internal/UX-CANON.md` §D names the
file, the query, the allowlist entry
(`web/src/desk/__tests__/containerQueryLaw.test.ts`) and the reason —
the Dock, the menu bar, the Chair shell and the first-use pages sit
outside every named `surface` container. Content layout still answers
to the window.

### 5. The combined revision and `btn--chrome`

The floor rig keyed its ledger on every class, so HS-202-03's new
`btn--chrome` marker would have minted twelve fresh wing signatures and
failed the combined run. The rig now drops that ONE marker when it
builds a signature; every other class and the size stay in the key.
Verified both ways: `.desk-wing.is-on` and
`.desk-wing.is-on.btn--chrome` normalize to the same signature.

### The hit contract, inside the real first-use layouts

Astra's MISSED: the fixture proves CSS, not live ownership. The floor
rig now runs `elementFromPoint` over the nine points of every visible
plated Button ON the six screens at 393. It does not click — a real
pointer on a live first-use face fires real verbs, and the pointer half
of the proof stays in the isolated fixture.

```
HIT CONTRACT 393: 42 reachable plated Button observations, every one
owning its nine points at 44x44; 27 skipped as occluded by a window in
front
```

**This claim was wrong; Round 2 below replaces it.** One of those 42
does not own all nine points, and the reader that produced the line
could not fail on a body hit.

Two readings are facts, not defects, and the rig says which is which:

- **Occluded** — 27 Chair Buttons sit behind an open Desk window. They
  do not own their own centre, and the halo is not what is in their
  way. Skipped, counted, reported.
- **Covered** — one halo reaches under the layer in front:
  `meetings-ledger@393 'Generate'`, three of its nine points on the
  Meetings window's title bar. That is the layer order working, not a
  clip. Ledgered, printed every run.

A point lost to an ANCESTOR CLIP or to an ADJACENT CONTROL in the same
layer still fails. Both of those are what the ruling rejects.


## Round 2

Astra's second verdict was **DO-NOT-RATIFY on two instrument defects**,
under the scar this repo already carries: a check that cannot fail
proves nothing. Both were real. Both are repaired, each proven by
reintroducing the exact defect and watching the fence go red.

### 1. The hit reader filed a lost point as coverage

The live reader split a lost point two ways — same layer meant a
neighbour stole it (fail), a different layer meant a window covered it
(ledger). `document.body` has no layer ancestor, so for any Button
inside a window a BODY hit landed in the ledger. A body hit means
nothing is painted there: the halo is absent, not covered. The reader
could not go red on the one condition it exists to catch.

Both readers now share ONE classifier
(`tests/e2e/test_hs202_05_button_hit_ownership.py`, `OWNERSHIP_JS`),
and every outcome is named:

| Outcome | Meaning | Verdict |
| --- | --- | --- |
| `own` | the Button, or something inside it, answered | pass |
| `miss:nothing` | no element at the point | fail |
| `miss:body` | the body or root answered — the halo is absent | fail |
| `miss:ancestor` | an ancestor answered — it CLIPPED the halo | fail |
| `miss:sibling` | a box in the SAME layer answered | fail |
| `covered` | a box in a DIFFERENT layer, in front, answered | ledger |

Two permanent negative controls in the fixture rig (a halo clipped by a
short `overflow: hidden` well, and a halo suppressed with only the page
behind it) must lose their points, must never lose them as `covered`,
and between them must exercise BOTH `miss:body` and `miss:ancestor`, or
a branch is unproven. The live rig plants the same two shapes INSIDE
the front window every run — the exact layer condition that hid the
defect — and asserts they are caught.

RED, with the defect reintroduced:

```
NEGATIVE CONTROL: no control produced 'miss:body' (saw ['miss:sibling']); that branch is unproven
NEGATIVE CONTROL: no control produced 'miss:ancestor' (saw ['miss:sibling']); that branch is unproven
1 failed, 1 passed
```

GREEN, live:

```
SELF-TEST: hit probes lost their points as {'clipped': ['own', 'miss:ancestor'],
'bare': ['miss:ancestor']}
```

### 2. The ember gate did not cover the plate this story added

The gate's accent list was four hardcoded hexes written before
`--accent-ink` existed, so a failing pair on the NEW plate fell into
ungated `other`. Astra reproduced 2.22:1; the exact pair is
`--text-muted` `#9ba2b0` on `--accent-ink` `#8a5a3d` = **2.27:1**.

The list is now read from the running token layer — `--accent`,
`--accent-hover`, `--accent-press`, `--accent-ink`,
`--accent-ink-hover`, `--accent-ink-press` and the gradient head — so
it cannot drift from `design-tokens.json` again. Seven fills.

The self-test paints a muted label on `--accent-ink` every run and
asserts the gate classifies it `ember` and fails it.

RED, with the hardcoded list restored:

```
SELF-TEST ink: a muted label on --accent-ink classified as 'other' at 2.27:1
(accent fills seen: ['#a86e4a', '#bc8058', '#936041', '#da9868']); the ember
gate does not cover the new plate, so it cannot fail on it
```

GREEN:

```
SELF-TEST: ember probe rgb(155, 162, 176) on rgb(138, 90, 61) classified
ember at 2.27:1 (gate covers 7 accent fills)
```

**Withheld, not fixed:** no real muted-on-ink pair exists on the six
first-use screens today — the probe is synthetic. The gate now catches
one the moment a face paints it. `--text-muted` and `--text-faint` must
never sit on an accent fill; only `--text-on-accent` may.

### 3. The hit claim, corrected

The counsel round said "42 reachable plated Button observations, every
one owning its nine points". That was false for one of them, and the
reader could not have seen a body hit anyway. The repaired reader
computes the line instead of asserting it:

```
HIT CONTRACT 393: 69 visible plated Button observations = 27 occluded
(centre not owned, skipped) + 42 probed. Of the probed: 41 own ALL nine
points of their 44x44 area, 1 owns fewer because a layer in front covers
the rest (ledgered below). Misses (body, ancestor clip, same-layer
neighbour): 0 — any would have failed.
```

The one is `meetings-ledger@393 'Generate'`: three of its nine points
sit on the Meetings window's title bar.

### 4. The PR and the ruling document

PR #597 is retitled `HS-202-05: the type-scale ruling, then the tokens`
and its body now describes the build, the ember decision for the
sitting, the ledgers and the verification. The ruling document's status
moved from `PROPOSAL` to `RATIFIED AND BUILT`, points at the canon that
now holds the rules, and records the two places the build departed from
§3 and §4 (plated versus chrome; the first-use ember pairs gated rather
than ledgered).
