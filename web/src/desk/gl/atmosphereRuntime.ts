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
  /** Passive product truth; decorative scenes never acquire a microphone. */
  activity?: AtmosphereActivity;
}

export interface AtmosphereActivity {
  recording: boolean;
  speaking: boolean;
  level: number;
  /** Monotonic count of actual newly added Desk objects, excluding initial load. */
  arrival: number;
}

export interface AtmosphereActivitySource {
  read(): AtmosphereActivity;
  subscribe(listener: () => void): () => void;
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
  activity?: AtmosphereActivitySource;
  motion?: boolean;
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
  let reducedMotion = motionQuery.matches || options.motion === false;
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
    scene.update({
      delta,
      elapsed,
      pointer,
      activity: options.activity?.read(),
    });
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
    else if (reducedMotion) {
      // A paused scene may have missed real capture changes while hidden.
      scene.update({
        delta: 0,
        elapsed,
        pointer,
        activity: options.activity?.read(),
      });
      scene.render();
    } else start();
  };

  const onMotionChange = (event: MediaQueryListEvent) => {
    reducedMotion = event.matches || options.motion === false;
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
  // Reduced motion freezes scenery, while real state changes still update the
  // lamps. Capture-level samples intentionally do not wake a frozen canvas.
  const unsubscribeActivity = options.activity?.subscribe(() => {
    if (!reducedMotion || destroyed || document.hidden) return;
    scene.update({
      delta: 0,
      elapsed,
      pointer,
      activity: options.activity?.read(),
    });
    scene.render();
  });
  resize();
  scene.update({
    delta: 0,
    elapsed: 0,
    pointer,
    activity: options.activity?.read(),
  });
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
    unsubscribeActivity?.();
    scene.dispose();
  };
}
