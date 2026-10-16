/** Observation rig only: direct authored-time samples, no product debug API. */
import { createJupiterOrbitScene } from '@w/desk/gl/jupiterOrbitScene';
import * as model from '@w/desk/gl/jupiterOrbitModel';
const canvas = document.querySelector<HTMLCanvasElement>('#scene')!;
const scene = createJupiterOrbitScene({ canvas, seed: 0x4a555049, reducedMotion: false });
scene.resize({ width: innerWidth, height: innerHeight, devicePixelRatio: devicePixelRatio });
const frame = (elapsed: number, x=0, y=0) => {
 scene.update({ delta: 0.016, elapsed, pointer: { x, y } });
 scene.render();
};
frame(0);
Object.assign(window, { orbitObservation: { scene, model, frame } });
