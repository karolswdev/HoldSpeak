# Round-two full-suite verification — integration pending

The first serial run was interrupted after **106 passed, 69 skipped in 1247.51 s**, exit 2, to integrate main `5de5d0c3` and resolve PR conflicts. This is not a full-suite result. [Raw partial output](full-python.pre-main-interrupted.raw.log) and [capture receipt](full-python.pre-main-interrupted.capture.txt) are retained. No failure or flake classification is inferred from that partial run. Final integrated full verification follows.

The earlier complete full-suite run and independently reproduced inherited failures remain in [the initial classification](../integration/full-suite-classification.md).

235 reviewed tracked evidence paths were restored from successful HEAD reads; pre-existing untracked bytes were checked unchanged. Three unrelated newly generated shots were parked by explicit path. Receipts: [tracked](partial-restored-tracked-evidence.json), [parked](partial-parked-test-shots.json).
