export interface AtmospherePointer {
  /** Normalized viewport coordinates in the range -1…1. */
  x: number;
  y: number;
}

export interface AtmosphereViewport {
  width: number;
  height: number;
  devicePixelRatio: number;
}

export interface AtmosphereFrame {
  delta: number;
  elapsed: number;
  pointer: AtmospherePointer;
}

export interface AtmosphereScene {
  resize(viewport: AtmosphereViewport): void;
  update(frame: AtmosphereFrame): void;
  setReducedMotion?(reducedMotion: boolean): void;
  render(): void;
  dispose(): void;
}

export interface AtmosphereSceneContext {
  canvas: HTMLCanvasElement;
  /** Stable per-atmosphere seed. Scenes may derive independent weather RNGs. */
  seed: number;
  reducedMotion: boolean;
}

export type AtmosphereSceneFactory = (
  context: AtmosphereSceneContext,
) => AtmosphereScene;

export interface MountAtmosphereOptions {
  seed: number;
}

/** Browser lifecycle shared by every HoldSpeak atmosphere.
 *
 * Scene modules only build and animate their world. This host consistently
 * owns visibility suspension, reduced motion, pointer normalization, resize,
 * frame clamping, and teardown so adding another background cannot quietly
 * invent a second lifecycle contract.
 */
export function mountAtmosphereScene(
  canvas: HTMLCanvasElement,
  factory: AtmosphereSceneFactory,
  options: MountAtmosphereOptions,
): () => void {
  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  let reducedMotion = motionQuery.matches;
  let destroyed = false;
  let animationFrame = 0;
  let elapsed = 0;
  let lastFrame = performance.now();
  const pointer: AtmospherePointer = { x: 0, y: 0 };
  const scene = factory({ canvas, seed: options.seed, reducedMotion });

  const viewport = (): AtmosphereViewport => ({
    width: Math.max(window.innerWidth, 1),
    height: Math.max(window.innerHeight, 1),
    devicePixelRatio: Math.max(window.devicePixelRatio || 1, 1),
  });

  const resize = () => {
    scene.resize(viewport());
    scene.render();
  };

  const stop = () => {
    if (animationFrame) cancelAnimationFrame(animationFrame);
    animationFrame = 0;
  };

  const renderFrame = (now: number) => {
    if (destroyed || reducedMotion || document.hidden) return;
    const delta = Math.min(Math.max((now - lastFrame) / 1_000, 0), 0.05);
    lastFrame = now;
    elapsed += delta;
    scene.update({ delta, elapsed, pointer });
    scene.render();
    animationFrame = requestAnimationFrame(renderFrame);
  };

  const start = () => {
    if (animationFrame || destroyed || reducedMotion || document.hidden) return;
    lastFrame = performance.now();
    animationFrame = requestAnimationFrame(renderFrame);
  };

  const onPointerMove = (event: PointerEvent) => {
    if (reducedMotion) return;
    pointer.x = (event.clientX / Math.max(window.innerWidth, 1)) * 2 - 1;
    pointer.y = (event.clientY / Math.max(window.innerHeight, 1)) * 2 - 1;
  };

  const onVisibilityChange = () => {
    if (document.hidden) stop();
    else start();
  };

  const onMotionChange = (event: MediaQueryListEvent) => {
    reducedMotion = event.matches;
    scene.setReducedMotion?.(reducedMotion);
    if (reducedMotion) {
      stop();
      scene.render();
    } else {
      start();
    }
  };

  window.addEventListener("resize", resize, { passive: true });
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  document.addEventListener("visibilitychange", onVisibilityChange);
  motionQuery.addEventListener("change", onMotionChange);
  resize();
  scene.update({ delta: 0, elapsed: 0, pointer });
  scene.render();
  start();

  return () => {
    if (destroyed) return;
    destroyed = true;
    stop();
    window.removeEventListener("resize", resize);
    window.removeEventListener("pointermove", onPointerMove);
    document.removeEventListener("visibilitychange", onVisibilityChange);
    motionQuery.removeEventListener("change", onMotionChange);
    scene.dispose();
  };
}
