# HS-56-03 — The actuator card (the marquee; absorbs G)

- **Project:** holdspeak
- **Phase:** 56
- **Status:** done
- **Depends on:** HS-56-02
- **Unblocks:** HS-56-06, HS-56-07
- **Owner:** unassigned

## Problem
An actuator proposal awaiting approval is the highest-stakes, least-visible
moment in the product — it sits in a dashboard panel the user may not have
open. And nowhere does the product answer, at the decision point itself, what
data is involved, whether anything leaves the machine, and what control the
user has (backlog candidate G).

## Scope
- **In:**
  - **Backend:** the aftercare file-issue route gains the same
    `actuator_proposed` broadcast the live in-meeting path already has; a new
    `actuator_result` broadcast where the executor records
    `executed`/`failed` and where a decision lands `rejected` (payload: the
    proposal summary + result/error).
  - **The cards:** `actuator_proposed` → the `alert` card ("A decision needs
    you"; target · action · reversible; the mono payload preview;
    **Approve / Decline** buttons POSTing to the existing decision route and
    then mirroring the dashboard's exact post-approval behavior — no new
    execution path, no different inputs); `actuator_result` → `approve` ✓ /
    `decline` ✗ / `error` cards with the composited glyphs and short result
    detail. Proposed-cards linger until resolved or dismissed (never
    auto-deciding, never auto-expiring); dismissing is safe (the proposal
    stays in the dashboard).
  - **The G panel:** every actionable card carries the three plain-language
    answers — *what data is used* (the preview/payload summary), *does
    anything leave this machine* (the named target, e.g. "creates an issue on
    GitHub" — or "nothing leaves this machine" for local-only moments),
    *what control do I have* (the buttons + dismiss, named).
- **Out:** changing the executor, the decision route, the permission
  manifests, or proposal persistence in any way.

## Acceptance criteria
- [x] The aftercare route's proposal creation broadcasts `actuator_proposed`;
      executor executed/failed and decision-rejected broadcast
      `actuator_result` (integration tests on all three; wire-safe — the
      machine payload never rides a broadcast, asserted).
- [x] The alert card presents on the broadcast; Approve/Decline POST the
      identical request the dashboard sends (byte-asserted against
      dashboard-app.js); an unapproved proposal still never egresses (the
      existing executor tests untouched and green; the dashboard's Approve
      is decision-only, and so is the card's).
- [x] Result cards render with the right glyph + detail (executed/failed/
      rejected; the failed card states "Nothing egressed.").
- [x] The three privacy answers appear on every actionable card
      (verbatim-locked: "Data used:", "If you approve, this goes to",
      "Your controls:").
- [x] Live proof: a real proposal → the card → Approve → status=approved,
      decided_by recorded, no side effect (dogfood 4/4, zero page errors,
      two reviewed screenshots — see `evidence-story-03.md`).

## Test plan
- Integration: broadcast emission on all three transitions; the card's POST
  shape vs. the dashboard's. Playwright: present → approve → result card.
  Full suite.

## Notes / open questions
- Investigate first how the dashboard triggers execution after approval and
  copy it exactly; the card is a faster front door, not a second door.
