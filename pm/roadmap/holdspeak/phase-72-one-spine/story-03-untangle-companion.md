# HS-72-03 — One name per concept: untangle "companion"

- **Status:** todo
- **Priority:** HIGH (the worst naming collision in the product)
- **Depends on:** HS-72-02

## Goal

Make "companion" mean exactly one thing. Today the single `/api/companion/*`
prefix carries three unrelated concepts: (1) the **coder session picker**
(`system.py:151,388,405,422,441` — which live Claude/Codex session receives
dictation), (2) the **desk actuator relay** (`meetings.py:1202–1444` — the
iPad desk's slack/webhook/github propose/decision routes), and (3) in the
docs, the **iPad app itself**. The Primitive Framework already settled the
vocabulary: `agent` is a persona, `coder` is a live session. The routes and
surfaces follow the nouns.

## Scope

- **In:** the session-picker routes move to `/api/coders/*` (status, select,
  dismiss, pin, clear-stale); the desk actuator relay moves out of
  `meetings.py` into its own router (`holdspeak/web/routes/desk_actuators.py`)
  at `/api/desk/actuators/{slack,webhook,github}/*`; the Swift client
  (`HTTPDesktopClient.swift:175+` and friends) and the web callers
  (`desk-app.js`, `companion-desk.js`, dictation modules) move in the same
  commit; the `/companion` page's identity is reconciled with `/desk` (one is
  "the Desk", the other is the coder board — labels and page copy say so);
  tests updated; the HS-72-02 manifest regenerated with the new consumer map.
- **Out:** any behavior change inside the moved handlers (byte-identical
  bodies, new paths); merging `/companion` into `/desk` (a product call, not
  a naming fix — note for the owner if the build makes it look right);
  reserving "companion" as the iPad app's marketing name (POSITIONING's call,
  handled in HS-72-10).

## Tasks

- [ ] Move the five picker routes to `/api/coders/*`; grep-kill every old
      path across `holdspeak/`, `web/src/`, `apple/`, `tests/`,
      `dogfood/` — no aliases, no redirects (nothing is released on the
      Apple side; greenfield discipline).
- [ ] Extract the six relay routes into `desk_actuators.py` under
      `/api/desk/actuators/*`; `meetings.py` shrinks accordingly (the full
      split is HS-72-06).
- [ ] Update `HTTPDesktopClient` + its tests; rebuild via
      `gen-meeting-capture.rb`; full `xcodebuild` for the Simulator.
- [ ] Update web callers + labels (`companion.astro` presents the coder
      board; nav/Studio copy consistent).
- [ ] Regenerate the API manifest; the diff shows exactly the eleven moved
      routes and nothing else.

## Proof required

Manifest diff = exactly the moved routes; zero grep hits for the old paths
outside the roadmap/history docs; Simulator screenshot of the coder board
working against the renamed routes (live hub on LAN or seeded); web
`/companion` and Qlippy card approve path walked with screenshots; full suite
green; Swift build green.
