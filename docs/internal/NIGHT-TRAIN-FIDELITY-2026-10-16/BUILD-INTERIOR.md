# Night Train interior and render fidelity

DRAFT — HOLD FOR SHIP. Built after root design GO in
`wt-night-train-fidelity-20261016`. The owner rejected the upright book leaf,
aliasing and camera bobbing. Tuesday: a steady seated view with supported
physical objects and clean edges. Root judges actual moving frames and crops.

The upright leaf is removed. Two solid page blocks rise gently from their cover
and gutter, with printed top surfaces that follow the same curves and fine page
edge textures. The cover rests at the table's 0.7775 m top; the book group is at
`[-0.08, 0.7805, -0.44]`. Total book height is below 0.03 m. No unsupported paper
card remains. The train-local lamp pool shadow map is 1024 square, retaining the
existing PCF soft-shadow path and bias.

The train camera has no elapsed-time vibration, roll or pointer parallax.
Responsive desktop/portrait positions still apply after Room update and resize;
exterior scenery and glass rain continue through the existing motion guards.
No landscape, journey, station or glass source changes were made in this lane.

Room has one optional `renderQuality: "high"` argument, selected only by Night
Train. That path passes an actual HalfFloat render target with
`min(4, renderer.capabilities.maxSamples)` samples into EffectComposer. The
installed addon clones that target for its second buffer and owns final disposal
of both. Room does not register or separately dispose those targets. RenderPass,
UnrealBloomPass and OutputPass retain their existing order. The high path caps
DPR at 2 and framebuffer size at 2560 × 1600; the default Room path retains its
original DPR 1.5 and 1600 × 1000 caps and zero-sample composer targets.

## Focused proof

All commands used the supplied `.tmp/night-train-fidelity/locked.py`, shared
machine lock, isolated HOME and native-state-off environment.

- `fidelity-interior-collect.log`: only existing
  `src/desk/gl/__tests__/nightTrainScene.test.ts`; 10 named checks collected,
  exit 0.
- `fidelity-interior-run.log`: same exact file with `--maxWorkers=2`; 1 file /
  10 tests passed, 638 ms, exit 0.
- `fidelity-interior-tsc.log`: exit 2, only
  `nightTrainJourney.test.ts:28:43` TS2367 (sibling lane's literal-union
  comparison); no interior/render diagnostics. Finding sent to that worker.
  Recheck pending sibling correction.

The focused file now uses the real installed EffectComposer for target creation,
cloning, resizing and disposal, with its GPU renderer and postprocessing passes
mocked. Checks assert HalfFloat targets and samples 4/2/0, pass order, 2304 × 1600
canvas/buffer dimensions for a 1440 × 1000 DPR 2 viewport, bounded large-screen
and phone sizes, the vanilla Room defaults, fixed desktop/portrait camera matrices
across elapsed time and pointer movement, book support and bounded height, 1024
lamp shadow map, motion freeze, and exactly-once final target/scene teardown.

No browser, build, broad suite, staging or commit ran in this worker lane. Unit
checks cannot prove GPU output, actual edge appearance, moving scene coherence,
hardware sample support or frame cost. Root owns those actual observations and
the final acceptance.
