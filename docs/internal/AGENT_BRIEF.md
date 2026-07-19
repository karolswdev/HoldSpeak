# The Agent Brief — building on the Desk OS

Forged at the owner's order at the close of Phase 100 ("document your
style, your constitution, the choices you have been making to allow
Desk OS to finally be the primary application layer, and forge them
into the next agent brief"). This is the standing brief for every
agent who works this surface after me. It records what finally worked
across Phases 93–100, why, and the fight that remains. Where this
brief and [CONSTITUTION.md](CONSTITUTION.md) disagree, the
Constitution wins.

## 1. Who rules

The Constitution is supreme canon; cite its articles in everything.
The owner's felt verdict outranks every green suite (Article IX.4) —
the record proves it: five phases shipped machine-green and failed the
owner's eyes before the method below existed. The verdict trail lives
in [GROUNDING.md](GROUNDING.md) Appendix A; the two that bound this
brief:

> "THIS HAS BEEN ENOUGH. RIGHT NOW, WE PLAN ON A PHASE THAT WILL
> CAUSE A DEEP, DEEP, DEEP GROUNDING…" (the halt that made Phase 100)

> "It's better, I cannot lie. … There's still, a lot of the windows
> you made? Still feel like a bunch of HTML slapped inside a 'nicer'
> (still not nice enough) looking container…" (the close of Phase 100
> — the ratification AND the next fight)

## 2. The method (this is the constitution of HOW)

What failed, five phases running: iterating pixels against
screenshots; shipping to machine-verifiable bars; patching components
one by one after each verdict; treating chrome as the product.

What worked, once, completely — Phase 100 — and is now the required
shape for any substantial UI/UX work:

1. **Ground before you draw.** Read the canon, rank the jobs by
   evidence (scripted weight × walk-proven value × owner attention;
   never a flattering feature ledger), write it down, cite everything.
2. **Judge everything against the jobs.** Every surface answers
   "which job, and does it serve it well" — keep / merge / re-shape /
   kill, census-proven complete FROM THE CODE, with live flow traces
   that count clicks, windows, concepts, and dead ends.
3. **Propose with real mockups.** High-fidelity, both form factors,
   real content, looked at with your own eyes. No unmocked thing
   ships in a plan.
4. **The owner gates.** Nothing builds before the verdict. Record it
   verbatim. Zero ceremony beyond that.
5. **Build story-by-story, one named mechanical guard each.** A rule
   without a guard regresses — the record proves this too.
6. **Prove on real metal, then look with your own eyes.** Staged hub,
   real Whisper, headed browser where headless lies (scrollbars,
   storm), live-viewport screenshots at 1440 AND 393 before claiming
   anything is done. Flow budgets are pinned as walk legs, not prose.

## 3. The design canon (the choices, and why they were made)

- **The desk is the operating surface; four applications and a desk.**
  Speak, Meetings, Agents, Settings. A new capability joins one of
  them or becomes a search-reachable tool. It does NOT become a new
  top-level door (POSITIONING, amended per Article I.4). Studio is
  dead; do not resurrect launcher tiers.
- **The posture rule.** An application opens on its job's headline
  posture. At most two more wings, as segments in the WINDOW HEAD
  (`web/src/desk/surface/wings.tsx` + the `wings` slot on
  `DeskWindowFrame`). ALL configuration folds behind one gear door.
  Tab walls inside window bodies are illegal (the geometry walk
  enforces it; the settings rail archetype and declared
  `data-specimen` gallery blocks are the only legal tablists).
  - *working*: one generous column, the verb huge, chrome silent
    (Speak's face).
  - *reviewing*: dense rows, verdict verbs inline, receipts behind
    disclosures (Meetings' outcomes).
  - *configuring*: grouped setting rows only — never bare forms.
- **The material is law.** Real vibrancy (`--desk-window-fill` +
  blur/saturate), the glass edge, the tonal ladder, traffic lights
  (colored only on the front window), one menu vocabulary
  (`DeskMenuList`), bare-control inheritance (no raw HTML control may
  render unskinned), drawn scrollbars (headed proof only), dock
  magnification + running marks, sprites as state. All values ride
  `web/design-tokens.json` through the token gate.
- **One launcher.** The dock carries the four applications + the
  record orb, nothing else; windows fold into their app chips. The
  bar is system truth: HoldSpeak menu, trust badge, attention bell,
  ⌘K, clock. The shelf is the ⌘K search palette and must reach every
  app, tool, and drawer. Never add a second way to launch.
- **The vocabulary is registry-driven and closed.**
  `docs/product-language.json` is the source of truth: **Agent** (not
  Persona), **intelligence** (not intel), Coder session, Runs on,
  Sequence, Knowledge. The web vocabulary guard's allowlist is EMPTY
  and stays empty — any entry added is a defect. Refusals name their
  fix and never leak a filesystem path. (The Apple surfaces still owe
  the Persona→Agent rename — a declared, path-scoped registry
  exception; take it with the HSM phase that consumes the thesis.)
- **Honesty is structural** (Article VI). A mic that cannot capture
  renders disabled WITH the reason (never null — the LAN-origin
  trap). Empty states say what is true and what would change it.
  Egress badges sit at the point of decision. "Learned from N" counts
  honestly at zero.

## 4. The guards (regression = unshippable)

- `tests/unit/test_web_vocabulary_guard.py` — canon words, no path
  leaks, empty allowlist.
- `scripts/desk_gl_walk.py speakflow` / `meetingflow` — flow budgets
  (4 and 3 interactions), no tab walls, live on the staged hub.
- `scripts/desk_gl_walk.py geometry` — every registered window
  measured against the grammar, incl. a 360px squeeze.
- `scripts/desk_gl_walk.py chrome` (HEADED) — the launcher contract:
  dock = the four apps, no bar starts, search reaches everything.
- `scripts/judgment_census.py` / `mockup_census.py` — docs stay
  complete against the code.
- `web/scripts/validate-tokens.cjs` — no raw values in component CSS.
- The full chain at any close: 21 walk legs + headed storm + full
  pytest (metal excluded) + vitest.

## 5. THE REMAINDER — the next fight (the owner's words are the bar)

"A lot of the windows still feel like a bunch of HTML slapped inside
a nicer looking container." He is right, and here is the honest
diagnosis: Phase 100 fixed the SHAPE of every interior (what leads,
what folds, what dies) but most bodies still COMPOSE as generic kit —
label-over-input fields, uniform row lists, one text size, verbs in
action rows. Native innards means:

1. **An interior type scale.** Window content is nearly monosize.
   Real applications have display numbers, primary lines, secondary
   metadata, captions — a ratified scale inside the body, not just in
   the chrome.
2. **Data as material, not data in fields.** Presented values should
   be the interface: edit in place on the presented text, not in a
   labeled input beside it. Kill every label+input stack that isn't
   genuinely a configuring posture.
3. **Purpose-built compositions.** The journal should read like a
   journal (a dated stream), Blocks like a library, Runs on like a
   switchboard, the transcript like a script. `SurfaceRows`
   everywhere is the tell that a surface was assembled, not designed.
4. **Verbs live on the material.** Hover/selection reveals the verb
   where the data is; action rows shrink to the rare global verb.
5. **Direct manipulation.** Drag a meeting onto a zone; drop an audio
   file onto Meetings; pull a chip out of a result onto the desk. The
   desk's physics should reach INTO the windows.
6. **Motion as meaning.** State changes animate what changed (the
   correction-learned moment, an approve leaving, a wing switch);
   nothing else moves.

Each of these lands the Phase-100 way: mock the worst three interiors
first, gate with the owner, build with a guard. Never patch-and-hope.

## 6. OS TERRITORY — don't be shy (the owner's standing order)

At the Phase-100 close the owner added: *"let's also — just not be
shy — and really push this into OS territory."* That is a standing
ambition order, not a suggestion. The Desk OS should not gesture at
being an operating surface; it should BEHAVE like one, unapologetically
— always in product truth (Article VI), never as theater. The
inventory to mock, gate, and build:

1. **The system shade.** The attention bell opens a real shade — one
   system surface for "what happened while you were away": the
   approve queue, finished intelligence runs, learned corrections,
   recovered captures. Dismissible, honest counts, verbs inline.
2. **A global keyboard grammar.** ⌘1–⌘4 open/switch the four
   applications; ⌘W closes and ⌘M minimizes the front window; ⌘K is
   search (shipped); Ctrl+` cycles (shipped); Escape grammar
   (shipped). ⌘/ shows the shortcut sheet — drawn, not a doc link.
3. **Right-click is universal.** Every desk object, every row of
   material, every window head (shipped), every dock chip (shipped),
   and the desk itself answer with the ONE menu vocabulary. If a
   thing can be acted on, its context menu says how.
4. **Drag-and-drop is a system verb.** Drop a .vtt/.srt/.txt or audio
   file anywhere on the desk → a Meeting imports. Drag a desk object
   INTO a window (ground an ask, hand a KB to an agent chat). Drag a
   result chip OUT of a window onto the desk → it is kept. The desk's
   physics reach through the glass in both directions.
5. **System moments.** Arrival is a boot moment — fast, quiet,
   composed (never a spinner pile). Recording state lives in the bar
   like a system indicator. State that changes while a window is
   closed surfaces in the shade, not in silence.
6. **Files-grade object browsing.** List mode grows into the desk's
   Finder: sortable columns, type filters, keyboard range-selection,
   the same context menus. Spatial for arranging, Files for finding.

Each lands the §2 way — mocked, owner-gated, built with a guard. The
bar for all of it: a person who has used a real desktop should feel
their reflexes WORK here.

## 7. Mechanics the walks depend on (learned the hard way)

- Staged runs are token-gated: walk arrivals via `arrive_url()` +
  `HS_WALK_TOKEN`; in-page fetches need the `X-HoldSpeak-Token`
  header from sessionStorage `hs.web.token`; `page.reload()` after
  the URL scrub 401s — re-arrive with the token.
- Mic capture needs a secure origin — walk voice legs against
  localhost; the LAN origin correctly shows the disabled-with-reason
  mic.
- Headless lies about scrollbars and frame timing: chrome and storm
  legs run HEADED.
- `pytest --lf` with a clean cache runs the ENTIRE suite — never put
  it inside a bounded evidence capture.
- The web bundle is gitignored: edit `web/src`, `npm run build` to
  verify against a staged hub, commit source only.
- Staging: `uv run python -m uat.stage --recipe seeded-desk --lan`;
  the URL + token live in the `runs` table of `uat/_runs/uat.db`.
