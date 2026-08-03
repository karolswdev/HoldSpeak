# Evidence - HS-101-04

- **Story:** HS-101-04 - Closeout (the owner's sitting)
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T23:49:58Z

- **Command:** `sh -c HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py geometry && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py keys && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py speakflow && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py meetingflow`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 30e21d34c5d2b0612320a843c876ecf816a94dd6

```text
geometry walk: 12 windows measured against the grammar — heads, lights, padded bodies, no sideways scroll, no tab walls, reflow at 360px
keys walk: Meta+1/Meta+4 open the applications, Meta+M minimizes, Meta+W closes, Meta+/ draws the sheet, Escape clears it
speakflow: arrival -> correction in 4 interactions, 1 window, transcript 'Hello world, hello world, hello world, hello world.'
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/scripts/desk_gl_walk.py", line 2035, in <module>
    meetingflow()
    ~~~~~~~~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/scripts/desk_gl_walk.py", line 656, in meetingflow
    row.wait_for(timeout=10000)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py", line 18080, in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_sync_base.py", line 115, in _sync
    return task.result()
           ~~~~~~~~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py", line 710, in wait_for
    await self._frame.wait_for_selector(
        self._selector, strict=True, timeout=timeout, state=state
    )
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py", line 369, in wait_for_selector
    await self._channel.send(
        "waitForSelector", self._timeout, locals_to_params(locals())
    )
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py", line 69, in send
    return await self._connection.wrap_api_call(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py", line 559, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-surface-window .surface-rows .surface-row-open").first to be visible
```

### Captured run — 2026-07-19T23:53:25Z

- **Command:** `sh -c HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py geometry && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py keys && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py speakflow && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py meetingflow`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 30e21d34c5d2b0612320a843c876ecf816a94dd6

```text
geometry walk: 12 windows measured against the grammar — heads, lights, padded bodies, no sideways scroll, no tab walls, reflow at 360px
keys walk: Meta+1/Meta+4 open the applications, Meta+M minimizes, Meta+W closes, Meta+/ draws the sheet, Escape clears it
speakflow: arrival -> correction in 4 interactions, 1 window, transcript 'Hello world, hello world, hello world, hello world.'
meetingflow: arrival -> outcomes face in 3 interactions, 1 outcome concepts, transcript folded, no tab wall
```

### Captured run — 2026-07-19T23:54:52Z

- **Command:** `sh -c HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py chrome && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py storm`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 30e21d34c5d2b0612320a843c876ecf816a94dd6

```text
one-launcher: dock carries the four apps; search reaches every app and tool; the bar is system truth
chrome walk: the bar (two-tone, square verbs, red close), head menu, skinned selects, drawn scrollbar (headed), square maximize corners, dock underline — all present; shots at 1440 and 393
storm: {"gpu": "hardware", "frames": 962, "median_ms": 8.3, "p95_ms": 10.0, "max_ms": 10.4, "layout_events": 0, "paint_events": 0}
```

## The assembled chain (machine half) — from merged main (7c2fdc0b)

- Staged fresh: seeded-desk, run-20260719T234858 on :8792, bundle
  built from main. One meeting imported through the REAL wire
  (POST /api/meetings/import, the same route the glass drop uses) so
  the meeting flow has material — the first capture above records the
  honest empty-world miss.
- Headless legs (second capture): the GROWN geometry leg (12 windows;
  interior assertions on the converted faces), the new keys leg
  (⌘1–⌘4/⌘W/⌘M/⌘//Escape), speakflow (arrival → correction in 4
  interactions, 1 window), meetingflow (arrival → outcomes in
  budget).
- Headed legs (third capture): chrome (the launcher contract — bar,
  verbs, skinned controls, drawn scrollbar, dock underline) and
  storm on REAL GPU: median 8.3 ms, p95 10.0 ms, max 10.4 ms,
  0 layout events, 0 paint events over 962 frames — Article VIII.1's
  60fps budget holds with the fluid desk ON.
- Full pytest (story-03 capture, identical tree): 4122 passed /
  0 failed / 37 environment skips. Web vitest 310/310. Token gate
  clean; vocabulary guard green.

The owner's sitting remains — the phase closes on the felt verdict
(Article IX.4), not on this chain.

## The sitting, round 1 (2026-07-19) — NOT closed

> "Look, decent job. But the innards? The actual windows, and their
> insides? Still full of cases where buttons aren't margined
> correctly. Still feel like a wall of HTML (try ask an agent)...,
> and so on. Like, come on dude! Surely, the next loop will be
> awesome, right"

Named: button margins wrong across interiors; the agent chat is a
wall of HTML. The loop: eyes on the named case, a margin/composition
census over EVERY face, kit-level fixes, re-sit.

## Round 2 — the loop (eyes first, then the kit)

Census: every registered face screenshotted and READ. The named wall
traced to four systematic causes, all fixed at the source:

- **The disclosure had no body.** The desk correctly stripped the
  Signal card (HS-98 rule 1) but left `<summary>` as bare bold text —
  "Grounding scope" (Speak), "Filters" (Meetings), "How it connects"
  (Agents) all read as orphaned labels jammed against buttons. The
  kit now renders every desk disclosure as a quiet chip with a
  turning caret, wash on the summary only. One fix, every face.
- **The chat was a form pile.** PersonaChat's footer stacked a
  RUNS-ON section wall (showing "This device · This device" — a real
  duplication bug in RunsOnPicker, fixed for every consumer), the
  grounding section, a bare composer row, and warnings. Recomposed:
  a composed hello (avatar, name at primary, role caption, centered)
  and ONE composer well — mic, message, Send inline; the route
  folded into the well's foot as captions. The ambient card also
  BURIED the composer (fixed: it yields when a right sheet is open).
- **Raw wire enums in the glass.** The ambient card's eyebrow printed
  `ATTENTION · ACTIVE_APP`; now humanized. Commands said "0 macros"
  beside "voice commands" — one vocabulary now.
- **Buttons without a rhythm.** Speak's run row now centers and gaps;
  Commands' first-command verb centers under its empty state; the
  Speak hint dropped its second prose sentence.

Guards green after: interior canon + vocabulary + desk locks +
null-read (14), web 310/310, token gate clean, geometry + speakflow
legs green on the staged hub.

## The sitting, round 2 (2026-07-19) — NOT closed

> "position absolute, relative... great job there, bud. Then, the
> absolute cacophony of HTML forms over tabs over who knows what —
> not very happy with round-2. Three's the charm."

Named (with screenshots): the Settings window — the floating Save
button overlapping the posture card, the section label clipping
under the sticky bar, a display-sized page heading in the body, a
nested card box, the oversized find-a-setting input, two stacked
worlds in one face. Round 3 rebuilds the configuring archetype.

## Round 3 — Settings becomes an OS pane

The round-2 verdict's screenshots, worked cause by cause:
- **The floating Save is gone because Save is gone.** The configuring
  archetype now saves ON CHANGE (debounced through the same
  PUT /api/settings), and the verb bar whispers Saving…/Saved — no
  button to absolutely-position, no second Save+Discard row buried at
  the bottom, no clipped label under a sticky bar. Proven live: flip
  a switch, the whisper ticks Saved, the wire ran.
- **The page heading died.** .surface-panel-title is a CAPTION now —
  the rail already names the group; display scale is for facts, not
  headings.
- **The find-a-setting wall folded** into the section head, bounded.
- **Rows sit on OS density** (surface row grammar, switches at 32px,
  not 52px form rows).
- **The prose went to captions**: the policy invariants and the
  credentials boundary each state their one fact quietly.
Guards: settings/vocabulary/canon/locks/null-read pytest 129 passed;
web 310/310; token gate clean; geometry leg green on the staged hub.

## Round 4 — the config dump becomes settings

The round-3 screenshot's three sins, at the cause: the RAIL now rides
along (sticky) so a deep scroll never leaves half the window dead;
the sticky bar FROSTS what scrolls beneath it (backdrop blur +
--z-sticky — the orange toggle can't ghost through "Saved" anymore);
and the glass stopped wearing wire keys — a curated FRIENDLY_FIELDS
dictionary for the fields people actually meet ("MLX model",
"llama.cpp model file", "Model (OpenAI-compatible)", "Endpoint URL",
"API key env var", "Runs on profile", "Latency budget (ms)") plus an
acronym dictionary (MLX/OpenAI/API/URL/ID/LLM/env…) for the long
tail. Looked at deep-scrolled in the Runtime group: rail pinned,
labels civilized, bar clean. Token gate clean; web 310/310.

## Round 5 — bespoke components for complex ideas

The owner's restated bar, verbatim: "these things are complicated
enough that they can't just be dumbed down to a bunch of input
boxes… think about bespoke configuration components for those
complex ideas, so we can EASILY set things up."

Built (web/src/pages/cores/settingsBespoke.tsx, hooked through the
same special-case seam the symbol editor uses):
- **RuntimeDestination** — "where does voice typing run" was ONE idea
  smeared across 13 boxes. Now: five choice bays (Automatic / This
  device·MLX / This device·llama.cpp / An endpoint / A saved Runs on
  destination); choosing a bay writes backend/profile_id through the
  same auto-save and reveals ONLY that path's fields; engine details
  (context window, warm on start, idle eviction) fold behind a
  disclosure; the profile bay links straight into the Runs on window.
- **HotkeyCapture** — a key is pressed, not typed: the keycap control
  captures the keydown, maps it to exactly the hub's accepted set
  (holdspeak/hotkey.py — modifiers L/R, ⇪, F1–F12), writes
  key+display in one commit, and refuses unsupported keys BY NAME.
Driven live on the staged hub: chose the endpoint bay → whisper
ticked Saved on the wire; pressed F6 into the keycap → "F6", Saved.
Known trade-off, recorded: the find-a-setting query no longer
surfaces the runtime leaf keys individually (the bespoke owns them).
Token gate clean; web 310/310; shots in the round-5 set.

## Round 6 — opening a Meeting stops feeling assembled

The owner's example ("even opening a Meeting feels like some regard
made it"), eyes-first and rebuilt:
- The meeting's NAME is the material now (primary step + a facts line
  "2h ago · 1 min · 3 segments"); it was a caption-scale eyebrow.
- The hero empty "Nothing waiting on you" for a meeting whose
  intelligence never ran was dishonest weighting: intelligence-off
  now says ONE quiet line ("Intelligence is off — no outcomes were
  made for this meeting") — the detail's intel_status arrives as an
  OBJECT {state}, which the old check silently missed.
- The transcript — the only substance of an intel-less meeting —
  OPENS by default when there are no outcomes and reads like a
  SCRIPT: a tabular time gutter (0:00 / 0:06 / 0:12 from start_time
  seconds; the old code read a nonexistent `timestamp` key and drew
  a blank column), body-size lines at reading leading.
- Export stopped being a form Select wearing a verb's clothes: a
  caption + four dense verbs (Markdown / Text / JSON / SRT).
- Delete separated from export by a spring gap.
Looked at on the staged hub before/after; token gate clean; build
green.

## Round 7 — the sweep (my eyes, not the owner's)

Every reachable deep state screenshotted and read (scratchpad sweep
set). Fixed this round:
- **The Record wing's import form** (File/Title/Speaker/Tags label
  stacks + two prose hints + a raw file input) is now a DROP WELL —
  the same verb the desk already answers (B7), with browse on click,
  one caption of formats, and the detail fields appearing quietly
  only once a file is chosen (a well-level drop keeps the file local
  so title/speaker can be added; the desk-level drop still imports
  directly).
- **Setup's raw enum chip** (`needs_attention`) reads as words.

INVENTORIED, recorded as the standing remainder (each is a
sitting-loop candidate, worked eyes-first like the above):
1. **Live meeting is a plumbing dashboard on a working face**: six
   zero-count wire stats (DEFERRED PLUGIN JOBS), a bare Preview-route
   textarea, a bookmark label+input stack — all visible BEFORE any
   meeting runs. Needs the working posture: Start huge, transcript
   the material, plumbing folded behind the gear.
2. **Wake Word is a bespoke candidate**: model "hey_jarvis" as a raw
   value, threshold 0.5 as a bare number (a sensitivity idea), action
   "preview" — one wake-word component (phrase · sensitivity ·
   what-it-does), like RuntimeDestination.
3. **Transcription/Presence/Mesh groups**: same class — raw values
   in generic rows; candidates for curation or bespoke.
4. **Artifacts wing when populated**: Disclosure+SurfaceCode dumps —
   should be the library composition (the artifact body as the face).
5. **Session pullout deep states** (armed/steer) — unverifiable
   without a live tmux session on this stage; the couch walk covers.
Token gate clean; builds green; before/afters looked at.

## Round 8 — the object cards (the owner's double-click walk)

The owner's ask, in substance: double-click every desk object and
look at what opens — "inexplicably confusing and ugly." Eyes first:
every object double-clicked on a staged hub (seeded-desk + one
meeting imported through the real wire), all five opens screenshotted
and READ (scratchpad object-walk sets, before/after). The verdict was
right: every kind opened into ONE generic HS-73 template that the
native-innards work never touched. The systematic causes, fixed at
the source:

- **Raw markdown source in the glass.** Notes, artifacts, and agent
  instructions rendered literal `**asterisks**` in a bordered pre —
  there was NO markdown renderer in the codebase. Built one
  (`web/src/desk/surface/Material.tsx`): a deliberately small,
  dependency-free markdown→React renderer (headings, lists,
  paragraphs, bold/italic/code/links — React nodes, no innerHTML).
  Written material now reads as a document on the window material
  (`.surface-material`, reading leading, no box).
- **One template regardless of kind.** Recomposed per kind: the
  meeting leads with its facts line (round-6 phrasing: when · length ·
  segments) and the honest intelligence line; the note IS its
  rendered body; a Knowledge collection lists its members as rows
  (resolved titles + sprites, each opens); the agent is an identity
  card — avatar/name/role composed hello, ONE primary verb (Chat),
  instructions folded behind a disclosure, the run lane as the ONE
  chat-well composer (mic · material · Ask/Run) with Runs on in the
  well foot and the contract as a caption. The old capability wall
  (Persona heading, Ready chip, three prose paragraphs, boxed picker,
  second orange CTA) is dead.
- **The label walls fold into ONE disclosure.** WHERE IT BELONGS /
  KNOWLEDGE / PROJECTS (three eyebrow sections, always rendered, zeros
  and all) became one "Filed · <truth>" disclosure whose summary
  states the fact (zone or Desk root, honest counts); the foot's
  separate "Move to…" folded into it; a Knowledge collection no
  longer offers ITSELF as a home. Driven live: filing the glossary
  note into the Decisions zone flipped the summary on the wire and
  back.
- **The two-thirds void.** The card was a fixed full-height sheet no
  matter how little it held. `fitContent` on the window physics
  (DeskWindow): a content-sized card keeps its CSS height (the
  HS-97-09 max-height seed inflation is skipped) until the user
  arranges it — an empty KB now opens as a small honest card that no
  longer swallows the world. Working pull-outs (chat, sessions,
  terminals) keep the full-height sheet.
- **"Persona" in the glass, and WHY the guard missed it.** Three
  display labels said Persona (Pullout capability heading, shelf/list
  KIND_LABEL, editor eyebrow) plus a load-error label ("Personas:").
  All now say Agent. The vocabulary guard's prose heuristic required
  a SPACE in the string, so single-word labels were exempt — widened:
  a lone Capitalized alphabetic string is copy (wire keys stay
  lowercase-exempt), seeded both ways in the guard's own test. A
  DeskListView test that had enshrined "Persona" as expected copy now
  expects Agent.
- **OS chrome is not selectable.** Double-click was smearing text
  selection across the card's labels; `user-select: none` on the
  card, re-enabled on the material (note body, transcript, inputs).
- **A latent walk break found and fixed.** meetingflow still waited
  for "Needs you" — round 6 replaced that with the honest line on
  intelligence-off meetings, and the leg had not been re-run against
  such a world since. The leg now accepts the honest face or the
  needs-you face.

Proof: web vitest 310/310; token gate clean (one stale allowlist
entry deleted — the list shrank); vocabulary + interior-canon guards
7/7 with the widened rule; targeted desk/web pytest 443 passed;
geometry + keys + speakflow + meetingflow legs green on the staged
hub (:8792, bundle rebuilt from this tree); the double-click walk
re-run and all five opens looked at again at 1440.

## The sitting, round 8 (2026-07-20) — NOT closed; agent relieved

> "You had 3 strikes. You're out. Concept? Generally good. Exact
> execution, around OS-primitive and experience behavior? A fucking
> D-."

The concept (per-kind cards, material-first) stands; the EXECUTION
failed on OS-primitive and experience BEHAVIOR — verified by stills,
never by hands. The outgoing agent's honest defect list and handover
for the next round: `/tmp/help-please-my-story.md` (single-vs-double
click semantics unknown; card teleports to a fixed dock with no
origin; async fitContent growth pops with no motion; resize/maximize
of fit-content cards never driven; 393 never shot; nothing headed;
Edit still a detour, not in-place; caret/select/jargon shrugs; card
coexistence untested). Next round starts with a headed, hands-on
reflex walk — not a screenshot census.

### Captured run — 2026-07-20T05:51:24Z

- **Command:** `sh -c HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py smoke && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py geometry && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py keys && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py speakflow && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py meetingflow && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py windows && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py shell`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d6aa68eea1274fc4a93a1be0be2969355516d576

```text
smoke: tap-open ok, drag ok (330px), lasso bar=1, zone drag 319px
geometry walk: 12 windows measured against the grammar — heads, lights, padded bodies, no sideways scroll, no tab walls, reflow at 360px
keys walk: Meta+1/Meta+4 open the applications, Meta+M minimizes, Meta+W closes, Meta+/ draws the sheet, Escape clears it
speakflow: arrival -> correction in 4 interactions, 1 window, transcript 'Hello world, hello world, hello world, hello world.'
meetingflow: arrival -> outcomes face in 3 interactions, 0 outcome concepts, transcript folded, no tab wall
windows walk 1440: 3 windows, drag to {'x': 179, 'y': 189}, tray parks+restores, rect+maximize survive reload, reopen presents
windows walk 393: sheet form ok
shell walk 1440: dock, snap, cycle, park/restore, close, reset, menu dispatch in place
```

### Captured run — 2026-07-20T05:53:00Z

- **Command:** `sh -c HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py chrome && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py storm`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d6aa68eea1274fc4a93a1be0be2969355516d576

```text
one-launcher: dock carries the four apps; search reaches every app and tool; the bar is system truth
chrome walk: the bar (two-tone, square verbs, red close), head menu, skinned selects, drawn scrollbar (headed), square maximize corners, dock underline — all present; shots at 1440 and 393
storm: {"gpu": "hardware", "frames": 961, "median_ms": 8.3, "p95_ms": 10.3, "max_ms": 10.4, "layout_events": 0, "paint_events": 0}
```

## Round 9 — the reflex round (hands first, headed, both viewports)

Method inversion, per the round-8 relief note: before touching a line,
the desk was OPERATED in a headed browser — single click, double
click, drag, resize, maximize, Escape, ⌘W, two objects, right-click,
Edit, 1440 AND 393, touch context — and every reflex failure was
measured (scratchpad reflex-walk sets, before/after). What the hands
found, and what was built at the cause:

- **The click grammar was upside down.** ONE click opened the card;
  nothing selected; double-click had no meaning. Now (engine tap arm):
  a mouse click SELECTS (the ring + the ask bar answer), a
  double-click within 400ms/8px OPENS; modifier-click keeps toggle;
  touch and pen keep tap-to-open (the iPad's grammar — verified with a
  real touch context). The smoke leg now pins select-vs-open.
- **The card teleported to a fixed top-right dock** (object at x=174 →
  card at x=1022, a right-slide entrance; the CSS `position: fixed`
  home). Now the open gesture carries its point through the store
  (`pullouts[{id, origin}]`), the window SEATS ITSELF BESIDE the
  object (origin-seeded placeWindow, right flank first), and the
  motion is the minimize grammar pointed at the world: the card FLIES
  OUT of its object on open and back INTO it on close. Measured:
  object (174,202) → card (202,146); note (666,334) → card (694,278).
- **Windows never painted at their CSS home first** — placement moved
  to a LAYOUT effect (pre-paint), killing the one-frame teleport flash
  every window had.
- **Cards now COEXIST.** `pulloutId` (one slot + a back chip) became
  `pullouts[]` — each object card is its own window
  (`pullout:<id>`), with its own dock chip, rect, and stacking seat;
  reopening focuses instead of duplicating; the back chip died
  (drilling opens a second card, like an OS). Escape closes the FRONT
  card only (desk-scoped listener; focused windows keep their own);
  ⌘W takes the front window as before. Proven: two cards at once,
  each beside its object, then closed one by one.
- **Growth pops became motion.** The fit-content card grew +105px
  ~130ms after open (async detail/relationships) with zero animation.
  A ResizeObserver now settles unarranged fit-content growth through a
  200ms height animation; pinned/live-resize/maximized heights are
  never animated under the user.
- **Right-click answers.** The canvas had NO context menu (§6.3
  violation). Objects answer Open (+ Edit for editable kinds), zones
  answer Open/Rename, through the ONE menu vocabulary (DeskMenuList);
  the empty desk keeps the browser's own menu.
- **The note edits IN PLACE** (canon rule 1). Edit no longer kills the
  card and opens the third-chrome overlay editor: the material swaps
  to a same-geometry editor in the card (mic to fill, Cancel, Done;
  Escape reverts, ⌘Enter commits through the real PUT). Driven live:
  commit re-rendered the material on the wire; revert kept the card.
  (kb/agent/workflow keep their structured editor — recorded
  remainder.)
- **Copy works like an OS.** The card body is selectable text (facts
  lines, receipts, rendered bodies); only chrome (chips, summaries,
  eyebrows) stays unselectable. The disclosure caret that rendered as
  a 9px faint dot reads as a caret now.
- **A real z defect surfaced by the new legs:** the ⌘K search shelf
  rendered inside the chrome bar's z-30 stacking context, so ANY open
  window covered the search results. The shelf now portals to the
  desk root and sits above the window band, always.
- **Latent walk breaks found and fixed** (all pre-dating this round):
  the windows/shell legs still launched drawers from the dock
  (HS-100-11 moved them to the bell + search shelf — legs repointed
  through the real affordances); the head-grab offset landed on the
  HS-99 traffic lights; boxes were measured mid-entrance-motion
  (`settled_box` waits like a hand does).

Proof: the hands-on verification walk (headed, 1440 + 393 + touch
context) re-run against the staged hub after the build — every
behavior above driven and screenshotted, all shots READ; web vitest
312/312 (two new coexistence/origin tests); token gate clean;
vocabulary + interior-canon guards 7/7; targeted desk/web pytest 438
passed; the captured chains above: smoke + geometry + keys +
speakflow + meetingflow + windows + shell, then chrome + storm HEADED
on real GPU (median 8.3 ms, p95 10.3 ms, 0 layout events, 0 paint
events — the fluid grammar costs nothing at idle).

Considered and kept: the Runs-on caption's "sends Instruction,
Selected context, Grounding" is the Article VI egress disclosure at
the point of decision (humanized wire values, badge-grade) — it
stays. Standing remainder: kb/agent/workflow structured editors still
open the old overlay; zone dive remains single-click (navigation,
reversible), a deliberate deviation from the object grammar.
