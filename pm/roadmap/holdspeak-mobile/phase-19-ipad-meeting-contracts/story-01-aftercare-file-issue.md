# HSM-19-01 — Meeting aftercare: the file-issue action closes the loop

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** in-progress — the read half is merged and sim-proven (PR #155: `aftercare(meetingId:)`
  client + the close-the-loop card in `CompanionShellApp.swift`, screenshot
  `screenshots/aftercare-card-ipad.png`). This story finishes the loop: the file-issue action.
- **Depends on:** the shipped `HTTPDesktopClient+Aftercare.swift` (both verbs); the hub route
  `POST /api/meetings/{id}/aftercare/file-issue` (`holdspeak/web/routes/meetings/aftercare.py:162`).
- **Unblocks:** HSM-19-05 (a filed issue is a proposal in the review queue — the full loop).
- **Owner:** unassigned

## Problem

`fileAftercareIssue(meetingId:actionItemId:repo:)` exists (`HTTPDesktopClient+Aftercare.swift:37`)
and has **zero callers**. The aftercare card shows what's still open but the user cannot act on
it from the iPad; the card's note ("Accepted actions become issue proposals you approve") is
prose describing an affordance that does not exist — exactly the pattern the no-prose rule
kills: replace the sentence with the button.

## The design

1. **A "File issue" action on accepted open items.** The hub requires
   `review_state == "accepted"` and a target `repo` ("owner/name"); items not accepted get no
   button (honest — the hub would 400).
2. **The repo field, inline on the card** (no modal): a compact "owner/name" text field that
   appears when the action is tapped, remembered per session so filing three items types the
   repo once.
3. **The honest result:** filing records a *proposal* (`proposed` state) — nothing executes.
   The confirmation states that and points at the review queue (19-05). A 400 surfaces the
   hub's own reason.
4. **Kill the prose note** — the affordance replaces the sentence.

## Scope

- **In:** the file-issue flow on the aftercare card; the accepted-only gating; the inline
  repo field; the honest proposed-state confirmation; sim proof.
- **Out:** approving the proposal (19-05's queue); hub-side changes (route shipped, HS-49);
  the metal walk (19-07).

## Test plan

- `swift test` (existing `*ClientTests` stay green; the client is already covered).
- Sim proof: seeded demo (`HS_SHELL_DEMO=aftercare` extended with an accepted item) →
  screenshot of the action + the proposed-state confirmation.
