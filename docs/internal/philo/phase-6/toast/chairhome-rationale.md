# ChairHome seam proposal

**PROPOSAL ONLY · NOT APPLIED · OWNER RATIFICATION PENDING**

[`chairhome.patch`](chairhome.patch) is an actual unified diff against the
current `web/src/desk/chair/ChairHome.tsx`. `git apply --check
docs/internal/philo/phase-6/toast/chairhome.patch` passed without changing the
target file.

The seam adds one empty slot immediately before the real `<CaptureBar />` in
the Arrival render. In the current source that insertion is at
`ChairHome.tsx:1442`; `ChairHome.tsx:685` is the measured CaptureBar-related
anchor used by the canvas evidence, not the patch insertion point. The owning
lane must add an AmbientLayer portal to put the existing card in that slot. The slot stays in normal document flow, so the card follows the
readable Arrival content. The patch alone places nothing. At 393 the sticky
CaptureBar can still cover the card during intermediate scrolling. The
proposed auto-scroll must bring the card to the measured clear position or
end-of-scroll clearance; the empty slot alone does not solve that transition.
The current ChairHome source already
measures the real CaptureBar height in `--arrival-capture-clearance`; this
proposal does not add a second guessed height or a viewport-specific constant.

The canvas measures the phone flow target with summary open as:

* summary text ends at `y 331.6`;
* the card occupies `y 373.6–553.6`;
* the CaptureBar starts at `y 573`.

The proposal leaves the transition behavior open for owner decision: the
aftercare transition may scroll to the measured slot, or the product may ask
the user to scroll. The canvas recommendation is auto-scroll to the measured
slot when the signal arrives. This moves the owner’s reading position and
scrolls the Arrival head off the phone. The owner must ratify this trade-off
before lane A builds it. The future build also needs the off-Arrival shell
slot and focus routing for the active Meetings and Floor surfaces; this patch
alone does not provide those placements.

The nonzero canvas card keeps its existing words, kinds and verbs; its
data slice and producer remain unchanged. The separately fenced 0/0 render
correction omits Open proposals. This lane did not edit ChairHome, and this proposal does not grant
permission to apply the patch.
