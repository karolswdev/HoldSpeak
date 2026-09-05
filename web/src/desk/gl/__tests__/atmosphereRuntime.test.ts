import { afterEach, describe, expect, it, vi } from "vitest";
import {
  mountAtmosphereScene,
  type AtmosphereScene,
} from "../atmosphereRuntime";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("atmosphere runtime", () => {
  it("keeps paused scenes still but refreshes real activity on visibility return", () => {
    const requestFrame = vi.fn();
    vi.stubGlobal("requestAnimationFrame", requestFrame);
    vi.stubGlobal("cancelAnimationFrame", vi.fn());
    Object.defineProperty(document, "hidden", {
      configurable: true,
      value: false,
    });
    vi.spyOn(window, "matchMedia").mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as unknown as MediaQueryList);
    let listener: (() => void) | undefined;
    const unsubscribe = vi.fn();
    const activity = {
      recording: false,
      speaking: false,
      level: 0,
      arrival: 0,
    };
    const scene: AtmosphereScene = {
      resize: vi.fn(),
      update: vi.fn(),
      render: vi.fn(),
      dispose: vi.fn(),
    };
    const factory = vi.fn(() => scene);
    const cleanup = mountAtmosphereScene(
      document.createElement("canvas"),
      factory,
      {
        seed: 91,
        motion: false,
        activity: {
          read: () => ({ ...activity }),
          subscribe: (next) => {
            listener = next;
            return unsubscribe;
          },
        },
      },
    );
    expect(factory).toHaveBeenCalledWith(
      expect.objectContaining({ reducedMotion: true }),
    );
    expect(requestFrame).not.toHaveBeenCalled();
    activity.recording = true;
    listener?.();
    expect(scene.update).toHaveBeenLastCalledWith(
      expect.objectContaining({
        delta: 0,
        elapsed: 0,
        activity: expect.objectContaining({ recording: true }),
      }),
    );
    const renders = vi.mocked(scene.render).mock.calls.length;
    Object.defineProperty(document, "hidden", {
      configurable: true,
      value: true,
    });
    document.dispatchEvent(new Event("visibilitychange"));
    activity.recording = false;
    listener?.();
    expect(scene.render).toHaveBeenCalledTimes(renders);
    Object.defineProperty(document, "hidden", {
      configurable: true,
      value: false,
    });
    document.dispatchEvent(new Event("visibilitychange"));
    expect(scene.update).toHaveBeenLastCalledWith(
      expect.objectContaining({
        delta: 0,
        elapsed: 0,
        activity: expect.objectContaining({ recording: false }),
      }),
    );
    expect(scene.render).toHaveBeenCalledTimes(renders + 1);
    expect(requestFrame).not.toHaveBeenCalled();
    cleanup();
    expect(unsubscribe).toHaveBeenCalledOnce();
  });

  it("owns shared frame, pointer, motion, resize, and disposal lifecycle", () => {
    let frame: FrameRequestCallback | undefined;
    let motionListener: ((event: MediaQueryListEvent) => void) | undefined;
    const requestFrame = vi.fn((callback: FrameRequestCallback) => {
      frame = callback;
      return 17;
    });
    const cancelFrame = vi.fn();
    vi.stubGlobal("requestAnimationFrame", requestFrame);
    vi.stubGlobal("cancelAnimationFrame", cancelFrame);
    vi.spyOn(performance, "now").mockReturnValue(1_000);
    Object.defineProperty(document, "hidden", {
      configurable: true,
      value: false,
    });
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1_200,
    });
    Object.defineProperty(window, "innerHeight", {
      configurable: true,
      value: 800,
    });
    vi.spyOn(window, "matchMedia").mockReturnValue({
      matches: false,
      media: "(prefers-reduced-motion: reduce)",
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_name, listener) => {
        motionListener = listener as (event: MediaQueryListEvent) => void;
      }),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    });

    const scene: AtmosphereScene = {
      resize: vi.fn(),
      update: vi.fn(),
      setReducedMotion: vi.fn(),
      render: vi.fn(),
      dispose: vi.fn(),
    };
    const factory = vi.fn(() => scene);
    const canvas = document.createElement("canvas");
    const cleanup = mountAtmosphereScene(canvas, factory, { seed: 91 });

    expect(factory).toHaveBeenCalledWith({
      canvas,
      seed: 91,
      reducedMotion: false,
    });
    expect(scene.resize).toHaveBeenCalledWith(
      expect.objectContaining({ width: 1_200, height: 800 }),
    );
    expect(scene.update).toHaveBeenCalledWith(
      expect.objectContaining({ delta: 0, elapsed: 0 }),
    );

    window.dispatchEvent(
      new MouseEvent("pointermove", { clientX: 900, clientY: 200 }),
    );
    frame?.(1_016);
    expect(scene.update).toHaveBeenLastCalledWith(
      expect.objectContaining({
        delta: 0.016,
        pointer: { x: 0.5, y: -0.5 },
      }),
    );

    motionListener?.({ matches: true } as MediaQueryListEvent);
    expect(scene.setReducedMotion).toHaveBeenCalledWith(true);
    expect(cancelFrame).toHaveBeenCalled();

    cleanup();
    expect(scene.dispose).toHaveBeenCalledOnce();
  });
});
