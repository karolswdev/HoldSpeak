# Phase 73 — The Desk, Inhabited (on the React foundation)

**Status:** **CLOSED — 10/10 (2026-07-02).** See [final-summary.md](./final-summary.md).

**Last updated:** 2026-07-02 (**re-scaffolded** on two owner decisions made
the same day, before any story executed: (1) **the Desk is the main surface**
— "not a shadow of a doubt" — so it becomes the web front door `/`,
formally superseding Phase 70's four-door IA; (2) **React + Vite replaces
the Alpine investment** for interactive surfaces — the Desk is built as a
React island in the existing Astro build, and the `?raw` + `new Function`
pattern is retired. Nine stories became ten: a foundation story leads, the
appendix deletion became the cutover story, and the IA change joined the
arrival story. No story had begun, so IDs were reassigned in place —
nothing shipped under the old numbering.)

## The thesis

Unchanged from open: Phase 71 ported the iPad desk's **renderer** to the
web; every **verb** still lives in the old page paradigm — banned selling
prose in the header (`desk.astro:53`), `role="dialog"` create drawers
(`desk.astro:488+`), no in-world editing, `openObject` (`desk-app.js:400`)
bouncing meetings to `/history` and everything else into the "Browse as a
list" admin appendix (`desk.astro:158–429`), flat text-count zones, no live
verb. The result is the owner's verdict: "a primitive copy, an uninviting
mess."

What changed at re-scaffold is the foundation and the stakes. The Desk is
now the product's web front door, which means the surface must carry years
of future verbs — and the Alpine factory (1,472 lines, string-eval loading,
no component model) was already at its ceiling before the pull-out, inline
editors, orb, and rail were added. Executing the inhabitation in Alpine and
migrating later would pay for the same surface twice; the phase is at 0/N,
so the pivot is free **now** and never again.

## Scope

- **In:** the ten stories below. `web/` only, plus docs and guards:
  the `@astrojs/react` integration, a `web/src/desk/` React+TS app
  (Zustand, `motion`, `@use-gesture/react`), the desk at `/`, in-world
  create/edit/open, zones, the Record orb, the agent rail, the Alpine-desk
  cutover, mechanical no-prose/no-modal locks, the walk.
- **Out:** the iPad app (reference, not target); new backend routes (every
  verb maps to an existing endpoint); browser-microphone capture (the orb
  drives the hub recorder via `POST /api/meeting/start` — the `/live`
  pattern; a browser-mic path is new plumbing + a new egress story);
  migrating `/history`, `/live`, or any other page to React (a later phase;
  HS-72-07 was cut in favor of it); coder presence beyond what the desk
  already shows (`agent` ≠ `coder`); SSR or any node runtime (the bundle
  stays static, served by FastAPI).

## Exit criteria (evidence required)

- [x] The React island builds in the one existing pipeline and renders the
      world at parity with the Alpine desk (side-by-side proof) (HS-73-01).
- [x] `/` is the Desk: full-bleed, immersive chrome, the first-run guard
      preserved, a guiding empty state that answers "what is this"
      (HS-73-02 — the guard proven both ways against the real milestone).
- [x] Note/KB/agent/zone creation is instant and edited in place; zero
      modal patterns in the desk tree (HS-73-03 — the DB round-trip proven,
      tags included).
- [ ] Tapping any object opens an in-world pull-out; meetings show
      lineage-grouped derivatives; "Open full" is the only navigation
      (HS-73-04).
- [x] Zones are painted member-thumbnail trays; drag files via the real
      `PUT`; dive/back is a camera move (HS-73-05).
- [x] The Record orb starts/stops the hub recorder; the finished meeting
      materializes as an object; external state honestly reflected
      (HS-73-06 — the external case driven by real broadcasts; the
      mic-in-hand run is the owner's closeout leg).
- [ ] The agent rail runs a persona with the generation theater; the result
      lands in the world (HS-73-07).
- [x] The Alpine desk is deleted behind a zero-loss verb inventory
      (HS-73-08 — the inventory caught two real gaps and both were closed
      before the deletion landed).
- [ ] Docs record the stack decision + desk-first IA; the no-prose and
      no-modal locks exist and are proven red on the old copy (HS-73-09).
- [ ] The inhabited walk passes with zero route changes (committed
      Playwright); the per-verb table shows every web verb in-world; suite
      + route pre-flight green (HS-73-10).

## Stories

| Story | Title | Priority | Status | Depends on |
|-------|-------|----------|--------|------------|
| HS-73-01 | The React foundation: the world, ported | HIGH | **done** (the island at render parity on /desk-next: same sprites/layout/positions contract, drag+Tidy proven, vitest 9/9, side-by-side committed, zero page errors; Alpine /desk frozen; see [evidence](./evidence-story-01.md)) | — |
| HS-73-02 | The arrival: the Desk is the front door | HIGH | **done** (/ = the island, immersive AppLayout, guard proven both ways, guiding empty state, mark+menu+hub-dot+egress chrome, chips wired to instant-create, /desk→/ + /desk-legacy, nav Desk-first; see [evidence](./evidence-story-02.md)) | 01 |
| HS-73-03 | Create in-world (no modals, ever) | HIGH | **done** (instant POST → spawn at center + NEW beat + focused in-world editor; vignette not scrim; autosave PUTs + optimistic merge; agent More in-card; zone rename-in-place; tap≠drag fixed; DB round-trip proven; see [evidence](./evidence-story-03.md)) | 01 |
| HS-73-04 | Open in-world: the pull-out | HIGH | **done** (tap opens on the stage for every kind; the meeting drawer + one-deep artifact stack + back; lineage ported drift-tolerant; Edit swaps the editor; Move-to files via the real PUT; Open full = the one navigation; location asserted unchanged; see [evidence](./evidence-story-04.md)) | 01 |
| HS-73-05 | Zones as landmarks: file and dive | MED | **done** (stable tints + member mini-sprites + empty hint; drop-ready lift mid-drag; drop files via the real PUT with live thumbs; dive/back camera; + Zone focuses rename; DB rows asserted; see [evidence](./evidence-story-05.md)) | 01 |
| HS-73-06 | The Record orb (the live verb) | HIGH | **done** (bottom-center; /live's calls verbatim, no getUserMedia; state honest via the one bus — external meetings flip it with the whisper, tap = stop only; stop materializes the meeting with the beat; see [evidence](./evidence-story-06.md)) | 02 |
| HS-73-07 | The agent rail: run from the world | MED | **done** (personas-only rail + egress dots; anchored ask; the REAL .43 run from the rail UI answered the instruction; copy affordance; the honest theater finding recorded; see [evidence](./evidence-story-07.md)) | 01, 04 |
| HS-73-08 | The cutover: the Alpine desk dies | HIGH | **done** (the verb inventory caught 2 real gaps — toggle-off + answerCoder — closed BEFORE deletion; one conscious drop recorded (workflow authoring → Workbench); the Alpine desk deleted, /desk-legacy 404s, /desk → /, sprites.js survives; see [evidence](./evidence-story-08.md)) | 02–07 |
| HS-73-09 | Docs + the locks (the docs story) | MED | **done** (GETTING_STARTED speaks the Desk; 5 mechanical locks in tests/unit/test_desk_locks.py — no-modal/no-mic/no-narration/positions-contract/front-door-guard; doc guards 85 green; see [evidence](./evidence-story-09.md)) | 01–08 |
| HS-73-10 | Closeout: the inhabited walk | HIGH | **done** (8 beats in one session, pathname never left /, the real .43 model answered inside the walk, zero page errors; final-summary.md ships; see [evidence](./evidence-story-10.md)) | 01–09 |

Build order: **01 → 02** → **03 / 04** → **05** → **06 / 07** in parallel →
**08** (cutover) → **09** → **10**.

## Where we are

**2026-07-02 — PHASE CLOSED (10/10).** The walk sealed it: one continuous
session — arrive, create+edit, arrange, zone+file by drag, dive/open/
edit/surface, the meeting drawer and artifact stack, the rail ask (the
REAL .43 model answered "inhabited"), the orb flipping on a real external
frame — with location.pathname asserted `/` after every one of the 8
beats and zero page errors. final-summary.md carries the ledger, the
numbers (suite 3071/37; 17 pages; −3,265 legacy lines), and the findings
(the /run frame-broadcast hub follow-up; run results not persisted; the
owner's mic-in-hand + feel pass outstanding by design). The web desk the
owner called "a primitive copy, an uninviting mess" is now the inhabited
front door on the decided stack.

**2026-07-02 — HS-73-09 done (9/10).** The docs tell the truth and the
rules are tests. GETTING_STARTED's arrival + route table speak the Desk
(README/welcome/ARCHITECTURE checked — already true); and
tests/unit/test_desk_locks.py turns the phase's owner-ratified rules into
five instant greps: no dialog takeovers on the desk tree, no browser
microphone, no privacy narration outside the canonical badge strings, the
bare hs.diorama.pos contract (persist middleware banned), and the Desk as
the front door with the inline first-run guard. One story left: the
closeout walk.

**2026-07-02 — HS-73-08 done (8/10).** One desk. The zero-loss verb
inventory gated the deletion and earned its keep: it caught the legacy
toggleFile's toggle-OFF half (Move-to now marks the containing zone and
clicking removes via the real membership DELETE) and answerCoder (the
coder pull-out gains "Answer with voice" on the same POST
/api/coders/select) — both closed BEFORE anything was deleted. One
conscious drop recorded: the drawer's chain/workflow authoring form
(capability graphs belong to Workbench; the workflow pull-out links
there). Then desk-legacy.astro, desk-app.js, and the /desk-legacy route
died; /desk keeps landing home; the shared sprite picker survives. 17
pages; the scoped stop-signal greps are clean on the desk tree. Next:
HS-73-09 (docs + the mechanical locks), then the closeout walk.

**2026-07-02 — HS-73-07 done (7/10).** Personas run from the world. The
right-edge rail holds exactly the agents (a coder is a live session,
never railed), each wearing its profile-derived egress dot; tap opens an
anchored ask; Run fires the real route with a pulsing working state and
the result lands in place with Copy. The crux was proven on real metal:
from the rail UI in a real browser, the ask went through the hub's
configured engine to the .43 endpoint and the REAL model answered
'desk' to "Say the word 'desk' and nothing else" — instruction followed,
prompt demonstrably delivered (the Phase-53 lesson). One honest finding:
the persona-run route emits no intel frames, so the shell theater cannot
fire for rail runs — recorded as a hub follow-up instead of faking frames
client-side. All the world's verbs are now in. Next: HS-73-08, the
cutover.

**2026-07-02 — HS-73-06 done (6/10).** The world has its live verb. The
Record orb sits bottom-center (the DioAmbientRecorder position) driving
the HUB's recorder with /live's exact calls — never a browser microphone.
State is honest by construction: the island subscribes to the one runtime
bus, so a meeting started anywhere (the /live page, the CLI, the iPad)
flips the orb to recording with the `live elsewhere` whisper, and its tap
is a stop — a second start is structurally unreachable. Stopping
materializes the finished meeting with the NEW beat in front of you, its
pull-out one tap away. Proven with real server broadcasts (the
external-truth case and the settle) and the materialize assertion; the
mic-in-hand lifecycle is the owner's real-metal leg of the closeout walk.
Next: HS-73-07 (the rail), then the cutover.

**2026-07-02 — HS-73-05 done (5/10).** Zones are the desk's geography.
Trays wear a stable per-zone tint (the sprite picker's hash family — a
zone keeps its color forever), member mini-sprites with overflow and a
bare count, and the whispered empty hint. The drag lights the hovered tray
mid-move (fresh rects each move, the HS-71-05 rule) and the drop files
through the real membership PUT — the thumbnail and count arrive without
a reload. Dive is a camera move onto the zone's members with a floating
← All to surface; + Zone arrives with its rename focused. All proven with
DB rows asserted and three screenshots. Next: HS-73-06 (the Record orb)
and HS-73-07 (the rail) — the last verbs before the cutover.

**2026-07-02 — HS-73-04 done (4/10).** The bounce-out is dead. Tapping any
object opens its pull-out ON the stage — a motion spring with the kind's
tint, the world alive behind it — and "Open full" (meetings → /history,
header only) is the ONE navigation left on the desk. The meeting drawer
shows the real persisted intelligence (Summary / Actions — the proof run
caught the renderer reading `text` where the wire says `task` / Artifacts)
with the one-deep artifact stack and ← back; artifacts wear the faithfully
ported lineage chips (drift-tolerant, via/from split, resolved refs open in
place); note/kb Edit swaps in the HS-73-03 inline editor; agents carry the
profile egress badge in the drawer header; Run is minimally wired through
the real /run routes; and Move to… — the no-drag filing path — writes the
real membership PUT (the DB row asserted). Location asserted unchanged
through the entire Playwright ritual; zero page errors. Next: HS-73-05
(zones as landmarks) / HS-73-06 (the Record orb).

**2026-07-02 — HS-73-03 done (3/10).** Creation lives in the world. The
chips POST instantly, the object spawns at stage center wearing the
HS-71-06 beat plus a materialize entrance, and the editor opens focused ON
the stage — the DioInlineNoteCard grammar: the world dims AROUND the
object via a radial vignette (which doubles as the click-away catcher),
the float settles while editing, and every keystroke autosaves through the
real PUT routes (450ms debounce, optimistic local merge so labels track
typing). Agent's advanced fields expand inside the same card; zones rename
in place on the tray. The role="dialog" era of desk creation is over — the
grep is zero across the tree. A real interaction bug was caught by the
proof run itself: the first tap-vs-drag pass suppressed plain taps (drag
state set on press, cleared next-tick); fixed so a moved gesture
suppresses and a tap opens. Proofs: the Playwright ritual end-to-end with
the DB row asserted (title AND tags), Escape/click-outside/tap-reopen,
zone rename in the DB, two screenshots; zero page errors. Next: HS-73-04
(the pull-out).

**2026-07-02 — HS-73-02 done (2/10).** The Desk is the front door. `/`
mounts the island under a new `immersive` AppLayout prop (no TopNav — the
island's chrome is the iPad's arrival grammar: the mark opening a compact
rooms menu, the hub dot, the canonical egress badge ported from the Alpine
desk, the create chips wired to instant-create, and one whispered hint),
with Phase 70's first-run guard ported VERBATIM and proven both ways
against the real milestone (fresh profile → /welcome; marked → the world).
A fresh desk shows the guiding empty state: the wordmark, the POSITIONING
short form (no privacy sentence — the badge is the answer), two
next-action chips. `/desk` 307-redirects home, the frozen Alpine desk
lives at `/desk-legacy` until the cutover, and the nav's first door reads
Desk. Owner-decision framing honored: Phase 70's four-door IA is formally
superseded on the front door while the other pages keep their nav. Two
deviations recorded (compact always-visible mark+menu over auto-hide;
chips wired not disabled). Next: HS-73-03 (create in-world) and HS-73-04
(the pull-out).

**2026-07-02 — HS-73-01 done (1/10).** The foundation stands. The Desk is a
React 19 island (`@astrojs/react`, one build, still a static bundle) at the
coexistence route `/desk-next`, rendering the world at parity with the
frozen Alpine `/desk`: the SAME sprite-picker module imported directly
(parity by construction), bit-faithful `looseHome`/glow/float math, the
HS-71 CSS values verbatim, and the exact legacy `hs.diorama.pos` contract
(no persist-middleware envelope) so hand-arranged desks survive the
cutover. Drag replicates HS-71-04 via `@use-gesture`. Proofs: vitest 9/9;
the seeded side-by-side (11 objects + 1 zone) committed; a real drag
persisted across reload and Tidy cleared it; zero page errors; 19 pages;
pre-flight 2 passed; full suite 3066 passed, 37 skipped. Two deliberate calls recorded: the float stays on
the proven CSS keyframes (`motion` enters with the interaction
choreography), and zones are parity-only until HS-73-05. Next: HS-73-02
(the arrival — the Desk becomes `/`).

**2026-07-02 — re-scaffolded (0/10).** The owner resolved the two questions
the original scaffold had left open or wrong: the Desk's role (main
surface, front door — supersedes Phase 70's IA) and the foundation (React +
Vite via `@astrojs/react`; Alpine retired for interactive surfaces; Astro
stays as the document shell). Nine stories re-authored as ten on the new
foundation; the original scaffold's diagnosis, verb inventory, and iPad
reference map carry over intact (see AGENT-BRIEF §2–3). Consequences
recorded in Phase 72: HS-72-07 (decompose `history.astro` in place) is cut
— decomposing an Astro monolith the stack decision now schedules for
migration is wasted motion. Next: an agent starts HS-73-01 on branch
`phase-73-desk-inhabited` under the PMO gate.

**2026-07-02 — opened + scaffolded (superseded same day).** The original
nine-story Alpine-based scaffold; diagnosis unchanged, foundation changed.

## Active risks

| Risk | Mitigation | Stop signal |
|------|------------|-------------|
| The island doesn't reach render parity and the phase stalls in framework plumbing | HS-73-01 is scoped to parity of the EXISTING world (no new verbs); the Alpine desk stays live at `/desk` until the cutover, so nothing regresses mid-phase | HS-73-01 open >3 working sessions, or any user-visible desk regression before HS-73-08 |
| Two desks drift during the phase (Alpine at `/desk`, React growing beside it) | The Alpine desk is frozen (bugfix-only) at re-scaffold; all new verbs land in React only | Any feature commit touching `desk-app.js` after HS-73-01 merges |
| `/` takeover breaks first-run or the route pre-flight | HS-73-02 ports the `index.astro` guard first and updates the pre-flight in the same commit | A fresh-profile arrival that does not land on `/welcome`, or pre-flight red |
| The React bundle bloats the local app | It's a localhost-served desktop product — size is a non-goal; still, one island, no component-library dependency, tokens reused | Any UI component library (MUI etc.) appearing in `package.json` |
| Double-start / dishonest orb state | Orb state derives from `GET /api/state` + `hs-*` events, never local assumption; reuse `/live`'s calls verbatim | Two concurrent `POST /api/meeting/start`, or orb idle while the hub records |
| Deleting the Alpine desk loses a verb | HS-73-08's zero-loss inventory: every control in `desk.astro` (incl. the 158–429 appendix: `openCreate`, "Move to…" `openFile`, `openRun`) mapped to its React home BEFORE deletion | Any legacy `@click` handler with no mapped equivalent at HS-73-08 review |
| Scope magnetism: migrating other pages "while we're at it" | Out list names them; HS-72-07's cut note schedules them for a later phase | Any diff touching `history.astro`/`live.astro` beyond link updates |

## Decisions made

- **The Desk is the web front door** (`/`) — owner call, verbatim quote in
  the brief; supersedes Phase 70's four-door IA. The cockpits remain as
  rooms reached from the world's chrome.
- **React + Vite + TypeScript** for interactive surfaces, as an island in
  the existing Astro build (`@astrojs/react`, `client:only`); Zustand +
  `motion` + `@use-gesture/react`; Signal tokens reused untouched. Astro
  stays for document pages. **No new Alpine, ever** (standing rule, docs'd
  in HS-73-09).
- **The Record orb drives the hub recorder** — no browser mic (no new
  egress, no new plumbing).
- **The rail is personas only** (`agent` ≠ `coder`).
- **HS-72-07 is cut** (recorded in Phase 72's status doc) — `/history`
  migrates to React in a later phase instead of being decomposed in place.
- **Same-day ID reassignment** is legitimate here: no story had started,
  no evidence existed; the cut-IDs-never-reused rule protects executed
  history, of which there was none.

## Decisions deferred

- When `/history` and `/live` migrate to React (a later phase; the standing
  rule forbids new Alpine meanwhile).
- Whether `/companion` (the coder board) merges into the desk as a lane —
  owner call once the rail exists.
- What happens to the old Home's orientation content beyond the guiding
  empty state (HS-73-02 retires the page; if anything proves missed, it
  returns as in-world guidance, not a page).
- Sprite icon-picker parity (`DioIconPicker`) — backlog candidate.
