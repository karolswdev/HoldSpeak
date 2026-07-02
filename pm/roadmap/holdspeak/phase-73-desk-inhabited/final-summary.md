# Phase 73 — The Desk, Inhabited: final summary

- **Closed:** 2026-07-02 — **10/10 stories done**, all in ONE working day.
- **Branch:** `phase-73-desk-inhabited` (merged to `main` by PR).
- **Why it existed:** the owner's verdict on the web desk — "a primitive
  copy, an uninviting mess" — plus two standing decisions ratified the
  same day: **the Desk is the main surface** users run on their
  computers, and **React + Vite replaces further Alpine investment**.

## What shipped, in one paragraph

The web Desk is now a React 19 island and IS the front door (`/`). You
arrive in the world (first-run guard intact, proven both ways); a fresh
desk answers "what is this" in the world's own voice. Everything you do
daily happens ON the stage: create materializes an object at center with
the beat and its in-world editor (no dialog ever again); tap opens the
pull-out (meetings: summary/actions/artifacts with a one-deep stack;
artifacts: drift-tolerant lineage chips); zones are tinted landmark trays
with member thumbnails — drag files through the real membership PUT, dive
is a camera move; the Record orb drives the HUB recorder with `/live`'s
exact calls and reflects external truth via the one runtime bus; the
agent rail runs personas through the real routes — proven on the `.43`
endpoint with instruction-following checks. The Alpine desk (3,265
lines) was deleted behind a zero-loss verb inventory that caught two real
gaps first; the docs speak the shipped desk; and five mechanical locks
keep the rules from regressing.

## The closeout walk (HS-73-10)

One continuous browser session on one seeded hub:
arrive → create+edit a note → arrange → zone (arrives renaming) → file by
drag → dive → open → edit → surface → the meeting drawer → the artifact
stack → back → the rail ask (**the real `.43` model answered
"inhabited"**) → the orb flipping on a real external live frame and
settling. **`location.pathname` was asserted `/` after every one of the 8
beats.** Zero page errors. `10-the-inhabited-desk.png` is the world at
the end of the walk.

## The numbers

- Suite: **3071 passed, 37 skipped** (3066 at phase open + the 5 locks);
  vitest 9/9; pre-flight green throughout; the api-surface guard caught
  one organic drift mid-phase (HS-73-03's new call sites) — working as
  designed.
- Web build: **17 pages** (was 18: `desk-legacy` deleted, `desk-next`
  retired into `/`).
- Net: the legacy page + factory (−3,265 lines) replaced by a typed
  island (`web/src/desk/`, ~1,600 lines incl. tests).

## Findings a future phase should know

1. **The persona `/run` routes emit no intel frames**, so the shell
   GenerationTheater cannot fire for rail runs (the rail carries its own
   working state). Broadcasting frames from `/run` is the recorded hub
   follow-up.
2. **Run results are not persisted** by the hub — the rail/pull-out
   render output with Copy; the materialize beat is ready the day the hub
   persists.
3. The **owner's real-metal leg** remains: a mic-in-hand recording from
   the orb and a hands-on feel pass of the arrival (requested at 2/10,
   still worth doing on main).
4. The persisted action-item wire key is **`task`** (not `text`);
   the meeting detail payload is the **bare** `to_dict` with
   `intel_status` nested.
5. `.desk-next` stays as the island's CSS namespace (cosmetic; renaming
   is churn).

## Story ledger

| Story | Verdict |
|---|---|
| 01 React foundation | done — parity by construction (shared sprite picker; bit-faithful math; the exact positions contract) |
| 02 The arrival | done — `/` is the Desk; guard proven both ways; immersive chrome; guiding empty state |
| 03 Create in-world | done — instant POST + beat + in-world editor; the modal era over; tap-vs-drag fixed properly |
| 04 The pull-out | done — the bounce-out dead; meeting drawer + lineage; Move-to; location never changed |
| 05 Zones | done — landmark trays; drag files via the real PUT; dive camera |
| 06 The Record orb | done — /live's calls verbatim; external truth via the one bus; materialize on stop |
| 07 The agent rail | done — personas only; the REAL `.43` model followed instructions from the rail UI |
| 08 The cutover | done — the inventory caught 2 gaps first; then −3,265 lines |
| 09 Docs + locks | done — GETTING_STARTED speaks the Desk; 5 mechanical locks |
| 10 The walk | done — 8 beats, one pathname, zero page errors |
