/** Standalone direction preview; the product uses the same scene and host. */
import { createJupiterOrbitScene } from '@w/desk/gl/jupiterOrbitScene';
import { mountAtmosphereScene } from '@w/desk/gl/atmosphereRuntime';
const release = mountAtmosphereScene(document.querySelector<HTMLCanvasElement>('#scene')!, createJupiterOrbitScene, { seed: 0x4a555049 });
addEventListener('pagehide', release, { once: true });
