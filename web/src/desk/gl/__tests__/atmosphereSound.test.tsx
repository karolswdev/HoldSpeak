import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const state = vi.hoisted(() => ({
  enabled: false,
  recording: false,
  phase: "closed",
  listener: undefined as (() => void) | undefined,
  dispose: vi.fn(),
}));
vi.mock("../atmosphereControls", () => ({
  useAtmosphereControls: () => ({ sound: state.enabled }),
}));
vi.mock("../../../lib/micSession", () => ({ micPhase: () => state.phase }));
vi.mock("../atmosphereActivity", () => ({
  observeAtmosphereActivity: () => ({
    read: () => ({ recording: state.recording }),
    subscribe: (listener: () => void) => {
      state.listener = listener;
      return () => {
        state.listener = undefined;
      };
    },
    dispose: state.dispose,
  }),
}));
import { useAtmosphereSound } from "../atmosphereSound";

function audioContext() {
  const gains: Array<{
    gain: {
      value: number;
      cancelScheduledValues: ReturnType<typeof vi.fn>;
      setTargetAtTime: ReturnType<typeof vi.fn>;
    };
  }> = [];
  const sources: Array<{ stop: ReturnType<typeof vi.fn> }> = [];
  const node = () => ({
    connect: vi.fn(function (this: unknown) {
      return this;
    }),
    disconnect: vi.fn(),
  });
  const source = () => {
    const value = {
      ...node(),
      start: vi.fn(),
      stop: vi.fn(),
      frequency: { value: 0 },
    };
    sources.push(value);
    return value;
  };
  const context = {
    sampleRate: 100,
    currentTime: 0,
    destination: {},
    createGain: () => {
      const value = {
        ...node(),
        gain: {
          value: 0,
          cancelScheduledValues: vi.fn(),
          setTargetAtTime: vi.fn(),
        },
      };
      gains.push(value);
      return value;
    },
    createBuffer: () => ({ getChannelData: () => new Float32Array(400) }),
    createBufferSource: source,
    createOscillator: source,
    createBiquadFilter: () => ({
      ...node(),
      frequency: { value: 0 },
      Q: { value: 0 },
    }),
    resume: vi.fn(async () => undefined),
    suspend: vi.fn(async () => undefined),
    close: vi.fn(async () => undefined),
  };
  const constructor = vi.fn(function () {
    return context;
  });
  vi.stubGlobal("AudioContext", constructor);
  return { context, constructor, gains, sources };
}

afterEach(() => {
  state.enabled = false;
  state.recording = false;
  state.phase = "closed";
  state.dispose.mockClear();
  vi.unstubAllGlobals();
});

describe("atmosphere room sound", () => {
  it.each(["radio-station", "rainy-city", "lantern-garden"] as const)(
    "%s allocates no audio unless the user opts in",
    (id) => {
      const audio = audioContext();
      renderHook(() => useAtmosphereSound(id));
      expect(audio.constructor).not.toHaveBeenCalled();
    },
  );

  it.each(["night-train", "rainy-city", "lantern-garden"] as const)(
    "%s mutes all capture and releases every source",
    async (id) => {
      state.enabled = true;
      Object.defineProperty(document, "hidden", {
        configurable: true,
        value: false,
      });
      const audio = audioContext();
      const hook = renderHook(() => useAtmosphereSound(id));
      await Promise.resolve();
      const master = audio.gains[0].gain.setTargetAtTime;
      expect(master).toHaveBeenLastCalledWith(0.8, 0, 0.5);
      state.phase = "open";
      state.listener?.();
      expect(master).toHaveBeenLastCalledWith(0, 0, 0.015);
      state.phase = "closed";
      state.recording = true;
      state.listener?.();
      expect(master).toHaveBeenLastCalledWith(0, 0, 0.015);
      hook.unmount();
      expect(audio.sources).toHaveLength(id === "night-train" ? 3 : 2);
      audio.sources.forEach((source) =>
        expect(source.stop).toHaveBeenCalledOnce(),
      );
      expect(audio.context.close).toHaveBeenCalledOnce();
      expect(state.dispose).toHaveBeenCalledOnce();
      expect(state.listener).toBeUndefined();
    },
  );
});
