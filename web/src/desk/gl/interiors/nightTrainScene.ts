import type { AtmosphereFrame, AtmosphereScene, AtmosphereSceneContext, AtmosphereViewport } from "../atmosphereRuntime";
import { Room, THREE } from "./sceneKit";
import { createTrainCompartment } from "./nightTrainCompartment";
import { createTrainGlass } from "./nightTrainGlass";
import { createTrainLandscape } from "./nightTrainLandscape";

/** Seated cabin view. The host owns scheduling; this wrapper owns the pause. */
export function createNightTrainScene(context: AtmosphereSceneContext): AtmosphereScene {
  const room = new Room(context, {
    camera: [-0.50, 1.15, 0.65], target: [0.03, 1.30, -1.30],
    background: 0x253b4d, fog: 0.007, ambient: 0.68, exposure: 1.15, fov: 49,
  });
  // Keep the oblique view of the wide distant sky inside the frustum.
  room.camera.far = 400;
  room.camera.updateProjectionMatrix();
  room.scene.environmentIntensity = 0.15;
  createTrainCompartment(room);
  const glass = createTrainGlass(room);
  const landscape = createTrainLandscape(room);
  const base = room.finish();
  let reduced = context.reducedMotion, disposed = false;
  let aspect = 1.6, elapsed = 0, pointerX = 0, pointerY = 0;
  const target = new THREE.Vector3();
  const initialFrame: AtmosphereFrame = { elapsed: 0, delta: 0, pointer: { x: 0, y: 0 } };
  // The world and glass start from the same still, including with Motion off.
  base.update(initialFrame);
  landscape.update(0);
  glass.update(0);

  function applyCamera() {
    const portrait = aspect < 0.8;
    const x = portrait ? -0.40 : -0.50;
    const z = portrait ? 0.98 : 0.65;
    const vibrationX = Math.sin(elapsed * 11.3) * 0.00055 + Math.sin(elapsed * 23.7) * 0.00018;
    const vibrationY = Math.sin(elapsed * 13.1) * 0.00045;
    room.camera.position.set(x + pointerX * 0.014 + vibrationX, 1.15 - pointerY * 0.009 + vibrationY, z);
    target.set(portrait ? 0.10 : 0.03, portrait ? 1.25 : 1.30, -1.30);
    room.camera.lookAt(target);
    room.camera.rotateZ(Math.sin(elapsed * 9.7) * 0.00028);
    room.camera.updateMatrixWorld();
  }
  applyCamera();
  return {
    resize(viewport: AtmosphereViewport) {
      if (disposed) return;
      base.resize(viewport);
      aspect = Math.max(1, viewport.width) / Math.max(1, viewport.height);
      applyCamera();
    },
    update(frame: AtmosphereFrame) {
      if (disposed || reduced) return;
      elapsed = Math.max(0, frame.elapsed);
      const delta = Math.min(Math.max(frame.delta, 0), 0.05);
      const ease = 1 - Math.exp(-delta * 1.6);
      pointerX += (frame.pointer.x - pointerX) * ease;
      pointerY += (frame.pointer.y - pointerY) * ease;
      base.update({ ...frame, elapsed, delta });
      landscape.update(elapsed);
      glass.update(elapsed);
      // Room restores its private target on every update; our framing comes last.
      applyCamera();
    },
    setReducedMotion(value) {
      if (disposed) return;
      reduced = value;
      base.setReducedMotion?.(value);
      applyCamera();
    },
    render() { if (!disposed) base.render(); },
    dispose() {
      if (disposed) return;
      disposed = true;
      glass.dispose();
      landscape.dispose();
      base.dispose();
    },
  };
}
