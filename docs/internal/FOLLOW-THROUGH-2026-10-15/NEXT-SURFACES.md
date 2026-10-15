# Next attention surfaces — bounded audit, 2026-10-15

**DRAFT · read-only input for the next iteration. Does not gate this release.**

Tuesday: can the architect read a decision, change it, and send the current
record while keeping the active window clear? Inspected the two supplied
production shots and current source. No product/test edits, test runs,
browser work, or owner-state access. Only this record was written.

All four mechanisms below already exist at base `420a0eb28`. The current
release makes some of them easier to see; it did not introduce them.
`git show 420a0eb28:<path>` confirms the unconditional Decision Send host,
automatic built-in pick, divider z formula, immediate edit dismissal, and
missing desk-decision preview version. Relevant compositor/Send/store files
have no release diff. The DecisionPullout release diff changes status and
material, retaining these older paths.

## 1. P1 — A shared resize divider can paint through the active window

**Observed:** `.tmp/follow-through/neighbors-after-retry-1440/brief-old-request-refused.png`
shows a thin vertical steel line near x=783 crossing Today's active title,
tabs, Brief period and content, continuing from the Settings/Decision seam.
The other supplied decision shot shows the same seam. These are image
observations, not measured DOM rectangles or pointer ownership.

**Source:** this is consistent with the shared compositor divider, rather
than a Settings-specific resize handle. `web/src/desk/compositor/sharedResize.ts:46`
derives touching pairs from rectangle contacts; it does not subtract a
third window's occluded area. `web/src/desk/compositor/CompositorLayer.tsx:34`
draws the entire six-pixel boundary. At `:95`, its z is the maximum of the
participant windows plus one. Window ranks occupy consecutive z values
(`web/src/desk/compositor/live.ts:121`), so the divider can tie the next
unrelated window in front. `web/src/desk/DeskApp.tsx:300` mounts the divider
after the windows; its own comment explicitly depends on later painting
at a tie (`CompositorLayer.tsx:93`). The steel is painted by
`web/src/desk/components/window-chrome.css:1086`.

**Next flow:** Settings and Decision may remain side by side; bringing Today
in front must cover their seam, including its pointer target. Keep shared
resize available on the exposed part and retain its existing drag/key
behavior. Correct the existing layer relationship or exposed span; no new
window framework. **Tenets 3, 5, 6; Constitution VIII.**

**Unknown:** the pictured DOM element was not probed. Actual pointer
interception and other overlap arrangements remain unverified. Confirm the
element and one three-window overlap before choosing the surgical fix.

## 2. P2 — Reading a decision automatically opens a second full copy in Send

**Observed:** `.tmp/follow-through/neighbors-after-retry-1440/decision-status-refused.png`
shows the decision/context, then SEND → HoldSpeak folder → PREVIEW with the
title, Status, Context and Decision repeated. The preview extends below the
window body. This is duplicate reading material before a Send intent.

**Source:** `web/src/desk/pullouts/DecisionPullout.tsx:191` mounts the full
DeskDecisionSendWells whenever edit mode is off. `web/src/desk/documentSends.tsx:77`
directly composes SendWells. With only the built-in destination,
`web/src/desk/surface/send/SendWell.tsx:509` automatically selects it; `:518`
fetches its preview and `:646` renders the open preview. PreviewWell renders
the entire returned body (`:214`). This is an existing intentional SendWell
default, not evidence of an accidental dispatch.

**Next flow:** read the decision once; explicit Send opens the same existing
destination/preview/dispatch flow in place. Brief already implements that
host pattern at `web/src/desk/pullouts/views/BriefView.tsx:649`, including
unmounting the full well until opened. Preserve discoverable prepared sends,
their receipts and Discard path; do not hide outstanding work merely to
reduce height. Keep the channel authority and point-of-send egress unchanged.
**Tenets 2, 3, 5, 6; UX-CANON A.5 and D.**

**Unknown:** no Send/Hide/dispatch interaction was executed in this audit.
The supplied shot proves excess preview material, not a broken Send button.

## 3. P2 — A refused decision text save dismisses its editor before the outcome

**Source only:** `web/src/desk/pullouts/DecisionPullout.tsx:76` builds the text
patch, then `:88` ignores updatePrimitive's promise and `:89` exits edit mode
immediately. `web/src/desk/store/dataSlice.ts:544` already returns a boolean:
it rolls a refused optimistic patch back at `:625`, publishes an exact Retry
at `:639`, and returns false at `:660` / `:672`. Reopening Edit resets the
local draft from that rolled-back record (`DecisionPullout.tsx:72`).

The store retains the rejected patch in its Retry closure, so this is not
proof of irreversible data loss. It is a concrete break in edit continuity:
the editor closes before success, and the next Edit can replace the rejected
local values with the old record.

**Next flow:** Done keeps the current fields and pending state until that
existing boolean result arrives. Success returns to the reader; refusal
keeps the draft editable with its existing failure/Retry. Prevent duplicate
save presses while that write is pending. Apply the same bounded outcome
discipline just adopted for the status choice; no new save controller.
**Tenet 3; Constitution VI; UX-CANON A.10.**

**Unknown:** no rejected body-save press was performed. Current status-write
success/refusal proof does not verify this separate text writer. Do not
report Done as live-broken until the focused refusal case is exercised.

## 4. P2 — An open ordinary Send preview has no decision revision signal

**Source only:** `web/src/desk/documentSends.tsx:38` builds deskDecisionDoc
from id/title and supplies no version. The same file already supplies a
version for Brief (`:28`) and Note (`:88`). SendWell refreshes its ordinary
destination preview only on ref, destination, retry or doc.version changes
(`web/src/desk/surface/send/SendWell.tsx:514`–`:527`). Decision status changes
leave the same mounted document id/title (`DecisionPullout.tsx:106`, `:191`).
The server's rendered decision document includes Status and current body
(`holdspeak/services/document_sources.py:350`, especially `:360`). Therefore
a successful status change can leave the open preview describing the prior
status until the well remounts or retries.

This is a display freshness gap, not proof that stale text leaves the
machine. The channel service explicitly rejects a changed document/digest
(`holdspeak/services/channel_service.py:549`, `:558`) and the existing well
can fetch a fresh preview after that refusal (`SendWell.tsx:530`).

**Next flow:** while ordinary Send is open, a known successful record change
invalidates its preview through the existing document-version mechanism;
the user then sees the current payload before dispatch. Keep prepared-send
payloads frozen, as their existing contract requires. Coordinate with the
folded host in target 2 so closing/reopening naturally reads current state.
**Tenets 3 and 5; Constitution VI; UX-CANON A.10.**

**Unknown:** no status-change → open-preview comparison was walked here.
The screenshot is a refused status attempt, so it does not prove this
successful-change condition.

## Bounded next proof and exclusions

Future implementation can extend existing app/species tests: one denied
text-save custody case in `web/src/desk/__tests__/decision.app.test.tsx`, one
explicit folded Send host case, one document-version preview case in
`web/src/desk/surface/send/__tests__/SendWell.test.tsx`, and one three-window
divider-order case beside the compositor tests. The resize target needs a
real geometry/pointer probe; a rectangle-only unit check cannot prove it.
No tests were collected or run for this audit.

The new named status choice/refusal, Brief's latest selection ownership,
requested-record failure/retry and Follow-through outcomes are outside this
next-target list. The Brief shot's Ewa failure names an earlier request while
the current selection remains Platform review; that shot alone is not proof
that today's footer verbs act on Ewa. Retain that distinction when testing
late failures. No owner HOME/DB, microphone, egress, or hidden button behavior
was inspected.

**Read-only audit complete. Release remains root's current task.**
