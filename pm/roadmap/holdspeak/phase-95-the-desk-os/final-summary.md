# Phase 95 — The Desk OS: final summary

**Closed:** 2026-07-18, ten stories in two days, at machine-verifiable
scope under the owner's standing close directive (the Phase 93/94
pattern): every machine-provable behavior shipped and walked green on the
production bundle; the live owner sitting is preserved verbatim as UAT
Campaign 13 and a BACKLOG row, because that verdict cannot be delegated —
it is the point of the phase.

## What the phase was

Born from the owner's first live UAT sitting (2026-07-17): the desk was a
front door that kept ejecting to sixteen flat pages under an alien shell,
over a DOM/CSS world that felt clunky. The owner's charter became the
[Constitution](../../../docs/internal/CONSTITUTION.md): **features do not
own surfaces; the OS owns surfaces and features plug into them.**

## What shipped

- **The engine (HS-95-01).** The world renders on a pixi v8 WebGL scene
  graph fed by the desk store; the DOM world renderer is deleted.
  Production storm on real GPU: median 8.3ms, p95 9.9ms; 1 layout + 2
  paint events across 8s of continuous drags. Interactions ported at
  HS-71 semantics; a visually-hidden layer keeps the keyboard contract.
- **The windows (HS-95-02).** `DeskWindowFrame` is the one container
  (icon/eyebrow/title/actions; minimize/maximize/close) over the Phase 93
  physics; all nine panels migrated; lifecycle persists beside the rects;
  phones get bottom sheets. Opening always presents (no stranded parked
  surfaces).
- **The shell (HS-95-03).** The dock, MRU cycling (Ctrl+`), edge-snap
  half/quarter tiles, layout reset; the chrome menu became a surface
  dispatcher. Windows are regions — the Phase 73 no-modal locks hold.
- **The pattern (HS-95-04).** Host-agnostic cores in `pages/cores/`
  (guard-enforced: no router coupling, no page chrome, scope by prop)
  with a hero slot; `SurfaceWindows` hosts them; documented in
  web/README.md.
- **The surfaces (HS-95-05..08).** Dictation (with a REAL voice proof:
  a say-generated wav through Chromium's fake mic into the hub's real
  Whisper), meetings (a PHYSICAL proof: the meeting spoken through the
  speakers, heard by the hub's real microphone, transcribed by Whisper,
  titled and summarized live by the .43 model, "Intelligence ready" worn
  in-world), configuration (a real settings change round-tripping and
  surviving reload), and the studio tier (Workbench maximized, saving a
  real desk-created workflow; the sessions surface reconciled to one
  roster + one chat + one session window).
- **The demotion (HS-95-08).** Fifteen flat routes became deep links that
  land on the desk with the right window at the right scope; AppShell's
  header, PRIMARY_NAV, PageHero, and WorkroomBar are deleted; the no-exit
  mechanical lock (`test_desk_no_exit_guard.py`) keeps the desk from ever
  navigating again — the evidence shows it firing on a planted violation.
- **The docs (HS-95-09).** POSITIONING amended under Article I; every
  entry doc teaches windows and deep links; ARCHITECTURE redrawn; fresh
  1440/393 screenshots from the shipped build; all doc guards green.
- **The closeout (HS-95-10).** The assembled storm holds the budget with
  the heaviest window open; the assembled walk chains every story walk on
  the production bundle; UAT Campaign 13 ("The Desk OS — the owner's
  verdict", seven scenarios) is authored, ledger-backed, and loaded by
  the live conductor.

## Deferrals, named honestly

- **The live owner walk** — preserved verbatim as UAT Campaign 13
  (`uat/campaigns/owner-13-desk-os.yaml`) and the BACKLOG Desk OS owner
  leg; the machine cannot cast this verdict.
- **The Dialog grammar inside re-homed cores** (meeting detail, editors)
  is an Article VII drift carried from the flat pages; triage with the
  owner's findings.
- **Mics on historically mic-less inputs** (settings fields) — Article IV
  polish for the triage.
- **The golden-43 deck's intel keys shadowed by DB-backed settings** on a
  staged run (the walk enabled intel through the product's own settings
  route) — a UAT-rig observation worth a rig fix.
- **Feature-detail doc captures** (journal, digest, aftercare) refresh
  opportunistically; entry captures are already from the shipped build.

## Handoff

The Swift Desk (HSM belt) now trails the Web Desk OS: windows, dock,
surface dispatch, and demotion have no native counterparts yet. The
contracts are the shell dispatcher's surface keys and the SURFACES table;
the HSM catch-up phase should consume exactly those.
