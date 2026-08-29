# Phase 148 — The Menu Grammar

**Status:** complete (6/6). Close counsel RATIFY-WITH-CONCERNS,
zero must-fix ("The craft is real"); two of three should-fixes done
in-round, the third (a web-unit baseline) on the next-arc menu. The
branch HOLDS for the owner's shot verdict and merge word.

**Last updated:** 2026-08-29.

## Owner mandate

2026-08-29, in the owner's words: the system is "a little too
sterile… it's always been the intent that… we are making a tribute
to the incredible Amiga OS… if you now go and expand the top menu
toolbar such as Desk, Object, Go, Window and so on, they are really
poor, right?" — ruled a good next step and chartered on "OK, go for
it." Graduates the BACKLOG candidate **AA** row "window-head menus
and keyboard equivalents on the verb registry" alongside the craft
pass. Branch `feat/hs148-menu-glyphs` from main `16477660`.

Standing laws with extra weight: **beautify Workbench 2.0, never a
POS** (this phase IS the beauty pass; the owner sees the MOCK
exhibit before live rollout and the shot exhibit before merge);
deep design not mechanical (three audits ran first; the Amiga
reference grammar is cited canon); sprites never emoji; 2px =
radius not borders; no prose in the UI. The standing questions:
*tired Tuesday?* and *does this operate with joy?*

## Evidence base

- [`assets/audit-census.md`](./assets/audit-census.md) — every seam
  file:line. Headline: **the glyph slot is plumbed but empty
  everywhere**; no toggle type exists; the head menu is hardcoded
  off-registry; the DESK_TOOLS glyphs are data waiting for one
  wiring line.
- [`assets/audit-menus-live.md`](./assets/audit-menus-live.md) +
  [`assets/audit-menu-shots/`](./assets/audit-menu-shots/) (16
  before-shots). Headline: **eight measured defects** — zero glyphs
  in any dropdown while ⌘K renders the same verbs WITH them; a REAL
  keyboard bug (D3: ArrowDown never enters an opened bar menu);
  near-invisible ghosting; keycap chaos.
- [`assets/audit-amiga-reference.md`](./assets/audit-amiga-reference.md)
  — the cited Workbench grammar: text-only items, stipple ghosting
  in the shadow color, the fancy-A keycap glyph flush-right, the
  checkmark lane, HIGHCOMP hover, `»`/`…`; icon columns are a
  Windows 95 import, not Amiga.
- [`assets/settled-design.md`](./assets/settled-design.md) — D1–D5.
  The one open input is the OWNER's: the glyph-column variant
  (A Purist / B Tribute-Plus / C Hybrid, orchestrator recommends C),
  ruled at the story-03 mock exhibit on truthful screenshots.

## Settled design

See the spec. In one breath: the full Amiga grammar lands
variant-independent (stipple ghosting + the verbatim ghosting law,
ghost-reason collapse, drawn keycap wells column-aligned, the
checkmark lane with real aria, the lane alignment law, recessed
separators, `»` and `…`, the D3 keyboard repair, casing + Go
grouping); the glyph column is attribute-driven so A/B/C are all
truthful one-flag states; vocabularies have jurisdictions (unicode
text-glyphs for text surfaces, VerbGlyph SVG for window mechanics,
sprites for objects/dock only — no new sprites, no emoji, and at
last an emoji guard); head + dock menus join the verb registry with
keycaps via a windowId-scoped dispatch (the AA row); no new key
bindings this phase.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-148-01 | The grammar core (DeskMenu + material) | done | [story-01](./story-01-grammar-core.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-148-02 | The content sweep (glyphs, groups, casing, …) | done | [story-02](./story-02-content-sweep.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-148-03 | The mock exhibit (the owner's variant gate) | done | [story-03](./story-03-mock-exhibit.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-148-04 | Head + dock menus on the registry (AA) | done | [story-04](./story-04-head-dock-registry.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-148-05 | The record book + the emoji guard | done | [story-05](./story-05-record-book-guards.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-148-06 | The walk and the close | done | [story-06](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

**COMPLETE — 6/6.** HS-148-06 closed it: the cold walk (nine legs
now) 9/9 THREE times with the menus leg green cold — and the leg
EARNED the phase its best catch first (the D3 focus repair passed
jsdom and failed real Chromium; fixed with a double-rAF past the
browser's native click-focus, proven three ways on glass). Close
sweep baseline-subset, zero real branch-new (the one non-baseline
name = an xdist conductor flake, serial proof captured as a paired
log). Close counsel: RATIFY-WITH-CONCERNS, ZERO must-fix, Amiga
fidelity verified point by point, all five orchestrator judgment
calls ACCEPTED. final-summary.md is the exit record; the after
exhibit rides the close delivery. THE BRANCH WAITS FOR THE OWNER:
the shot verdict (incl. the standing A/B/C variant flip) and the
merge word. Earlier — **5/6.** HS-148-05 (the record book + the emoji guard) is DONE —
DESK_GRAMMAR §7 is the menu law (lanes, the stipple law with the
Commodore quote, majority-collapse, checkable roles, jurisdictions,
the variant attribute, registry derivation), the USER_GUIDE says
its one honest new sentence, and the sprites-never-emoji doctrine
finally has teeth (the guard fails on an injected emoji, proven
both ways). Meanwhile story 06's walk leg caught a REAL
jsdom-vs-Chromium gap in the D3 focus repair (native post-click
focus lands after React's sync effect) — fixed with a double-rAF
deferral, proven on real glass three ways, and the list-view
context-menu ledger item is CLOSED on the walk (object rows wire
it; zone rows honestly do not). Remaining: the full walk ×2, the
sweep, the counsel, the after-exhibit. Earlier — **4/6.** HS-148-03 (the mock exhibit) is DONE — the owner's gate is
served: nine truthful shots off the real hub (the rig flips the
variant before app boot), cross-read clean, DELIVERED to the owner
with the before-shot, the A/C/B Go triptych, the Object and Desk
comparisons, and C at 393. C ships as default; the verdict is a
one-attribute flip forever. Remaining: 05 (record book + emoji
guard), 06 (walk + close). Earlier — **3/6.** HS-148-02 (the content sweep) is DONE — the data joined the
grammar: 24 verbs carry glyphs (the 13 Go programs reuse their deck
chars, dock-parity pinned; seven new kind glyphs argued one line
each; a restrained verb set keeps variant B truthful; window verbs
glyphless by ruled choice — the wells carry their identity), panel
contexts declared launcher|verb, the root data-menu-glyphs
attribute defaults to launcher with a localStorage override for the
exhibit rig, Go wears its 4/9 separator, Window casing is uniform,
the ellipsis audit found the two dialog-openers already honest, the
mark menu gains Intelligence and People. 52 focused green
orchestrator-read; bound-key set byte-identical. DISCOVERY
ledgered: three inherited web-unit failures (byte-identical to
main; one dating to HS-135-07) are invisible to the pytest sweep
baseline — the protocol has a web blind spot, named for the close
counsel. Next: the story-03 exhibit rig (orchestrator hands)
delivers A/B/C to the owner. Earlier — **2/6.** HS-148-04 (head + dock on the registry) is DONE — the AA
graduation: the hardcoded window menus are dead; one adapter builds
WorkMenuEntry rows FROM the registry (labels + keycaps — ⌘W/⌘M
finally visible where they act), dispatched to the CLICKED window
(two-window scoping pinned), VerbGlyph glyphs kept, snap
directionals staged for story 02, zero hardcoded labels (grep pin).
55 focused green orchestrator-read. Earlier — **1/6.** HS-148-01 (the grammar core) is DONE in two rounds — the
menus have their grammar: ground-color stipple ghosting (2×2, picked
on real glass), drawn keycap wells (visible even when ghosted),
the checkable entry type with honest aria and conditional roles,
the lane alignment law, recessed separators, the true `»`, the
majority-collapse ghost-reason footer (round 2 — the orchestrator's
eyeball caught the all-identical rule missing the audit's own
motivating panel), and the D3 keyboard repair gated to intentional
opens. 52 focused green orchestrator-read; the reforged Object
panel is the exhibit (story-01-shots/). Next: 02 (content) ∥ 04
(head+dock) in disjoint lanes, then the owner's mock exhibit.

## Decision log

- **2026-08-29 — owner direction:** the menus are the next step
  ("go for it"); the Amiga tribute is the explicit frame; AA's
  menus row graduates into this phase (recorded in BACKLOG.md).
- **2026-08-29 — orchestrator rulings (the spec):** text-surface
  glyphs are the existing unicode set (dock-parity for nouns, one
  glyph language across menu/deck/palette); VerbGlyph owns window
  mechanics; NO new sprites, NO new key bindings; the ghosting law
  adopted verbatim from the Commodore Style Guide; ghost-reason
  collapse (my addition — eight "Select an object" echoes become
  one footer hint); keycaps stay visible when ghosted; variants
  A/B/C are one-attribute states so the owner's verdict is cheap
  forever. The owner may overrule any row.
- **2026-08-29 — counsel design ruling: RATIFY-WITH-CONCERNS,
  zero MUST-FIX ("Build it").** Three should-fixes ABSORBED into the
  spec before any builder rides: (1) the stipple punches holes in
  the panel's own ground color, never black-on-dark — "the Amiga
  stipple ERASED to background" — with a 2×2 vs 3×3 real-glass
  checkpoint; (2) DeskMenuItem's hardcoded role becomes conditional
  so the primitive path can't emit a wrong checkable role; (3) the
  variant-C discrimination sentence (panel-level
  data-menu-context + one render check). Three items LEDGERED
  below. Human-compliance: "the owner finds Settings by its gear
  glyph instead of reading 13 labels… It operates with joy."

## Ledger (counsel, carried openly)

- The `▸`→`»` submenu indicator is a discrete story-01 criterion,
  not just spec prose (folded).
- The ellipsis audit is scoped to story 02's sweep (folded).
- List-view context-menu reachability gets explicit walk coverage
  in story 06 (the before-walk could not trigger it via Playwright)
  (folded).

## Risk register

- The verbRegistry bound-key-set pin and workMenu DOM pins WILL
  need honest updates (named in the census; builders update tests
  WITH the grammar, never weaken).
- The walk's `go-menu-393.png` pair changes by design — the pair
  review is the point, not a regression.
- Glyph column widens panels ~24px; 393 clamp verified in census
  (innerWidth − 232).
- Unicode glyph rendering varies by platform font; the mock exhibit
  is the check (mono stack pins the set already used by deck/⌘K —
  proven surfaces).
- Asset-clobber law stands for glass runs (141–148 dirs).
