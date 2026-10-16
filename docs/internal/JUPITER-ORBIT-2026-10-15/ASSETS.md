# Jupiter scene assets and references

**Size correction 2026-10-16:** natural moon bodies now use physical radius
ratios. See [current correction](../ORBITAL-PLACES-2026-10-16/SCALE-CORRECTION.md);
this supersedes the historical cinematic-size description below.

## Local image

`web/src/desk/gl/textures/jupiter-cassini.jpg` is NASA Photojournal PIA07782,
Cassini’s Best Maps of Jupiter (Cylindrical Map).

Credit: **NASA/JPL/Space Science Institute**.

- Source: https://science.nasa.gov/photojournal/cassinis-best-maps-of-jupiter-cylindrical-map/
- Original: https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia07/pia07782/PIA07782.jpg
- Retrieved2026-10-15, original441285bytes, unmodified local JPEG.
- SHA256: `6b835ddd8036ea9efd25def04f75aa60b69b096025a37eeae5e9b6978e0a2281`.
- NASA imagery guidance: https://www.nasa.gov/nasa-brand-center/images-and-media/

The source map contains actual observed cloud detail. The scene applies its
own lighting, tone, camera and rotation; it is an artistic composition, not a
claim about the present appearance or actual physical scale/timing of Jupiter.
No NASA logo or endorsement is used. The runtime reads this bundled image;
it makes no request to NASA or another external origin.

## Generated preview and geometry

`web/public/desk/atmospheres/jupiter-orbit.webp` is a1440×1000 still rendered
from the actual production Three.js scene at elapsed0, with the local map
loaded. This is the Settings preview and loading/WebGL-failure fallback.
Root exported it directly from a freshly rendered framebuffer; the original
first export read a cleared buffer and was discarded before product build.
The final preview was visually inspected. No model image generation was used.

Star geometry, moon surface shaders, spacecraft geometry, glint texture and
the dark monolith are code-authored locally. There are no downloaded spacecraft
models, external fonts, audio, analytics or network dependencies for the scene.
Moons have cinematic sizes and orbital periods. The Pioneer/Voyager visitors
are artistic silhouettes, not engineering models or real-time locations.

Visual references:

- Galilean moons: https://science.nasa.gov/jupiter/jupiter-moons/
- Pioneer: https://science.nasa.gov/3d-resources/pioneer/
- Pioneer10 mission: https://science.nasa.gov/mission/pioneer-10/

## Owner-requested richer sky

`web/src/desk/gl/textures/jupiter-starfield.jpg`: NASA Deep Star Maps,
galactic-coordinate4k map. Credit: **NASA/Goddard Space Flight Center
Scientific Visualization Studio**, visualization by Ernie Wright and Tom
Bridgman. Source https://svs.gsfc.nasa.gov/3895/; original
https://svs.gsfc.nasa.gov/vis/a000000/a003800/a003895/starmap_g4k.jpg.
Retrieved2026-10-15, unmodified2310496bytes,4096×2048.
SHA256 `1f2a3df79a6540f9a5d93299affa5969bdc109407804c5209c6ce31005204599`.
No constellation overlay is used. The map grounds the scene's star density
and galactic band; extra procedural depth and framing are artistic, not a
claim of the current sky from a specific spacecraft location. It is bundled
locally, with no runtime NASA request. It supersedes the initial sparse sky.

The final Settings/fallback preview was regenerated after the sky and weather
amendment, from the same actual elapsed0 scene; it is200766bytes.
