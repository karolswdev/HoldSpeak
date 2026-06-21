# Evidence — HSM-13-03 (The Companion board)

**Date:** 2026-06-20 · **Status:** done

The agent's question on the iPad — and *which* waiting coder an answer targets, made
unmistakable before you send. This is the last story of Phase 13; with it the phase
is complete.

## What shipped

- **Seam (`IDesktopClient`, HSM-13-03):** `companionStatus()` +
  `selectCompanionTarget` / `dismissCompanionTarget` / `pinCompanionTarget(pinned:)`
  over `/api/companion/status|select|dismiss|pin` (`apple/Sources/Providers`). A loose
  `CompanionStatusDTO` decodes only what the board needs from the rich status payload;
  `pinned` rides as a **JSON bool** (`makeJSONRequest`) because the desktop does
  `bool(body.get("pinned"))` and a string `"false"` would read truthy.
- **Contract types:** `CompanionTarget` (agent, session, the question, project,
  selected/pinned/stale, confidence) + `CompanionBoardState` — honest by construction:
  empty `targets` with `awaiting == false` means *nothing waiting*, never a manufactured
  target. `activeTarget` is the selected session (else the first waiting one).
- **View-model (`CompanionBoard`, RuntimeCore):** `load` / `select` / `dismiss` / `pin`,
  each `Result`-wrapped so an unreachable desktop degrades to a `.failure` the view
  renders (never a throw on the caller path). Selection is **server-side** — `select`
  sets the desktop's active reply target, so the next answer (HSM-13-01/02 →
  `/api/dictation/remote`) delivers to it with **no silent client default**.
- **The board in the app:** `CompanionAnswerApp` now renders the board (Signal language)
  — each waiting coder as a row with its question, project, confidence, pin + stale
  badges; tap **Answer this one** to make it the target ("Your answer lands here").

## Tests (ran)

`swift test` → **129 passed / 6 skipped / 0 failed** (+7 `CompanionBoardTests`): targets
render; `select` makes a target active and the refreshed board reflects it; `pin`/unpin
and `dismiss` (removes the row) round-trip; an **empty board stays honest** (no
manufactured target); an **unreachable desktop degrades to `.failure`** on load + select.
The companion-answer app **builds + signs** for device with the board UI
(`** BUILD SUCCEEDED **`).

## Acceptance

- **Renders the AI PI state in Signal** — waiting sessions, the selected target,
  confidence, freshness (stale), pinned, blockers. (Target *transport* is in the status
  payload; this board surfaces confidence + freshness + pin, the fields that change the
  decision.)
- **Select / dismiss / pin** via the existing endpoints; the selected target is
  unmistakable (filled radio + accent border + "Your answer lands here").
- **Hands the chosen target to the answer flow** — server-side selection means
  HSM-13-02's send delivers to the selected session, no silent default.
- **Unreachable/stale shown honestly** — `.failure` on unreachable; `stale` badge;
  empty board says so plainly.

## Device note

The device path is already proven by the HSM-13-04 gate (the question surfaced on the
iPad and a spoken answer landed in the coder). This story generalizes the single-question
surface to a multi-target board with explicit selection; the multi-target *selection*
logic is host-tested over the seam, and the board UI builds for device.
