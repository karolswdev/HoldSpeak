# Night Train fidelity correction — owner feedback, 2026-10-16

DRAFT direction; implementation authorized by the owner. Tuesday: a steady,
convincing place behind work. The existing composition remains; visual quality
and coherence must improve substantially. Root reads actual moving frames and
full-size crops before delivery. Tests alone cannot accept appearance.

## Settled changes

The book lies naturally open, both curved page blocks supported by their cover
and gutter. Remove the upright floating leaf. The camera stays steady across
elapsed time and pointer movement; all journey motion occurs outside.

The real postprocessing targets use up to four hardware-supported MSAA samples.
Night Train opts into a bounded high-resolution Room path, DPR at most2 and
framebuffer at most2560×1600. Other scenes keep their current quality defaults.
Composer target ownership/disposal stays explicit. This fixes the actual
rendering path, not only the default framebuffer antialias flag.

Outside, a few recognizable asymmetric Alpine peaks, connected buttresses,
glacial valleys, craggy rock faces and restrained snow replace generic repeating
rounded ridges. Directional evening light reveals relief; haze separates depth.
The lake reflects the cool sky and dark relief with restrained coherent ripples,
not uniform white dashes. Ground and trees remain coherent through travel.

The passing station is an actual small lakeside rail stop: shore/quay grade above
water, masonry retaining wall and platform edge, plaster/stone waiting room,
pitched roof/eaves, timber canopy/braces, supported bench, warm glazed windows.
Three or four framed/capped glass lanterns have small warm sources and restrained
pools. No glowing white rectangle light bars or unsupported rectangle island.
Use metres, bounded geometry/materials and the existing journey clock.

## Lanes

- Landscape worker: Journey, Landscape, their two focused tests; integrates
  createTrainStation(room,parent) with update(elapsed)/dispose API.
- Interior/render worker: Compartment, Scene, optional high quality Room seam,
  existing Scene test. Camera remains train-local and steady.
- Station worker: new Station module and its focused test only.
- Root: canvas, actual baseline/after shots, moving review, edge crops, hardware
  measurements, shared Room regression checks, final quick check and delivery.

No worker staging/commits. No tests/build/browser until explicit separate GO.
All checks use isolated HOME/native off and the machine lock. No owner data in
walks; normal idle-hub delivery is separate. No new UI/settings/world engine.
