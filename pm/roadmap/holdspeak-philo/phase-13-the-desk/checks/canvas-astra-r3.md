# Check — Astra (Codex `gpt-6-astra`, xhigh): PHILO-13-11 canvases, round 3

Session `01a0fa73-d58f-73c0-9c7e-93ab9a42a262`. Verbatim.

VERDICT: DO-NOT-RATIFY

FINDINGS:
1. The footer collision is visibly fixed: in `C1-5a-meeting-selected-park-393.png`, the warning is on its own row above MD, SRT, and Park. `C1-5b` and `C1-5d` show the parked and restored receipts without overlap. The receipt checks run after the click transitions (`harness/shoot.py:597–610`). The red-before record shows the old collision and Dock overlaps on four boards (`shots/red-before-r3b.json:2–4, 22–55`); current run reports exit 0 (`shots/run.log:52–53`).

2. The stale proof text condition is paid. README’s R3 rule and current CSS comment agree on the 393 menu Button (`README.md:48–50, 65`; `harness/canvas.css:657–660`). I recomputed the generated Measurements block from the committed facts with the builder; it matches exactly (`README.md:7–35`; `harness/build_review.py:54–91`).

3. The overlap fence’s three waivers are broader than the named exceptions. The sticky rule skips every pair whose nearest sticky/fixed ancestor differs, without establishing that the other element is scrolling content beneath that bar (`harness/shoot.py:279–288`). The mic rule checks for an input and a mic-class element, but not that they share the same field (`:290`). The More rule skips every pair involving an element inside `.p13-dock-more`, without checking that the other element is an icon actually scrolled under More (`:291–292`). The four red-before failures are credible evidence for those rendered cases, but the fence can miss other overlaps.

CONDITIONS: Narrow each waiver to the stated relationship, then rerun all 50 boards. Keep the existing four-board red-before evidence and show the corrected fence still catches unrelated overlaps while allowing the three intended cases.

MISSED: Highest cost: the fence’s exception checks do not prove the specific relationships their names claim, so “0 rendered overlaps” is not yet reliable across all pairs. I found no new overlap in the revised phone footer or the Dock states shown in the reviewed shots.

TUESDAY: Yes on the selected-meeting phone screen: Park is clear to tap, and the parked/restored outcomes remain visible; I would hold owner ratification until the overlap fence is trustworthy.

UNKNOWN: I did not test this on the owner’s device or verify live C2/C3/A1-F behavior; these are C1 canvas captures, with later-story behavior still represented by the named stand-ins.