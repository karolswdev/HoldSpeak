# Orbital places assets

## Mars terrain

`web/src/desk/gl/textures/mars-viking.jpg` is an unmodified local copy of the NASA Mars color map.

- Source: https://science.nasa.gov/3d-resources/mars/
- Download: https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/mars/Mars.jpg
- Credit: NASA/Jet Propulsion Laboratory and Caltech; Viking images processed at USGS.
- Size: 972896 bytes.
- SHA256: `12ec6bf02ebd42a246edc778cb2ce8c595b4d9f0892badf0bfff8abb2303c780`.

## Sky and previews

Both scenes reuse the local NASA deep star map already credited in `../JUPITER-ORBIT-2026-10-15/ASSETS.md`. No runtime remote image requests. Saturn's bands, rings and moon surfaces are procedural.

`web/public/desk/atmospheres/{mars,saturn}-orbit.webp` are 1440×1000 framebuffer exports from the actual scene factories after local textures loaded, at authored elapsed zero. They are the picker and WebGL failure stills. These are not direction sketches.

Moon body sizes now use physical relative radii; see [size correction](SCALE-CORRECTION.md). Orbit distances and periods remain authored. This is not an astronomical ephemeris.
