# Night Train fidelity correction — root review

Implementation authorized by the owner; final owner aesthetic judgment and
formal Muad’Dib postmerge review remain open. This is a correction of #1234.

## Actual appearance and motion

Root inspected the real 1440/393 GL compositions and unscaled book/lamp and
station crops. Earlier landscape renders were rejected: terrain had cut edges
and downward normals. The final mesh has closed low boundaries, upward normals,
connected asymmetric relief, cooler shaded rock and restrained upper snow.
The book has two supported curved page blocks; the floating upright leaf is gone.
The station has masonry, roof/eaves, braced canopy, recessed glazed windows,
bench and framed warm lanterns with local pools and shadows.

Final captures: `.tmp/night-train-fidelity/edge-final/` (retina frames and raw
crops), `after-final/` (both widths, elapsed0/30/90/180), and `motion-review/`.
The latter uses the actual shared host with an explicit demo offset165s, then
records several seconds of natural motion. Five changing exterior frames have
identical book/interior crop hashes even with changed pointer positions.
Reduced motion freezes the frame. This does not claim a natural165s wait.
No page or console errors were observed in final captures.

## Actual AA and resolution

The old postprocessing targets had samples0 despite the renderer AA flag.
Final actual EffectComposer targets report4/4 samples on this M2Max. Night Train
opts into the bounded high-quality Room path; defaults for other scenes stay
unchanged. At1440×1000/DPR2 the buffer is2304×1600; at393×852/DPR3 it is738×1600.
Both camera matrices remain unchanged across elapsed time and pointer extremes.

## Focused checks

Root read collect outputs and run tails, not just worker claims:

- Scene:10 passed (`fidelity-interior-collect.log`, `fidelity-interior-run.log`).
  Exercises actual composer cloning/resize/disposal through a mocked GPU,
  sample clamps0/2/4, default Room quality, steady camera and supported book.
- Journey/Landscape:9 passed (`landscape-material-collect.log`,
  `landscape-material-run.log`), including36 actual upward-normal assertions,
  low boundaries, periodic journey and tree/ground coherence.
- Station:5 passed (`station-polish-collect.log`, `station-polish-run.log`),
  including structural placement, lights, travel and owned resource disposal.
- Final TypeScript: exit0 (`landscape-material-tsc.log`). The earlier interior
  type check saw a sibling test literal-type error, corrected before this pass.

All run records above live in `.tmp/night-train-fidelity/`. Product hashes were
frozen after final captures in `final-product-hashes.json`.

## Local performance and limits

On actual ANGLE Metal Apple M2Max,30 measured frames per size/quality case:
normal journey108/106 desktop/phone submitted calls; visible station133/131.
Submitted triangles are about760–767k including reflection/shadow passes.
Direct render-to-GL-finish median0.8–0.9ms, p90≤1.3ms.120 natural RAF intervals
have median8.3ms and p90≤9.7ms (`performance-final/`, `performance-station/`).
These are local measurements, not phone hardware or battery guarantees.
Mountains are authored relief; lake reflections approximate the skyline.

## Production and delivery

Pending final quick check, real picker walks, PR merge and idle-hub delivery.
