/**
 * HS-135-12 — sfx.ts unit tests.
 *
 * Uses a mocked AudioContext to assert:
 * - play fires per trigger
 * - pool cap 3 evicts oldest
 * - toggle mute silences all
 * - reduced-motion mutes regardless of toggle
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  play,
  setSfxEnabled,
  isMuted,
  toggleSfx,
  subscribeSfxEnabled,
  _resetForTest,
  _setAudioContext,
  _setBuffer,
  _getPool,
  _setReducedMotion,
  type SfxName,
} from "../sfx";

// ---- mock AudioContext machinery ----

function mockBuffer(): AudioBuffer {
  return {
    duration: 0.05,
    length: 1102,
    numberOfChannels: 1,
    sampleRate: 22050,
    getChannelData: vi.fn(() => new Float32Array(1102)),
    copyFromChannel: vi.fn(),
    copyToChannel: vi.fn(),
  } as unknown as AudioBuffer;
}

interface MockSource {
  buffer: AudioBuffer | null;
  onended: (() => void) | null;
  connect: ReturnType<typeof vi.fn>;
  start: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
}

let createdSources: MockSource[] = [];

function mockAudioContext(): AudioContext {
  const ctx = {
    state: "running" as AudioContextState,
    destination: {},
    resume: vi.fn(),
    createBufferSource: vi.fn(() => {
      const source: MockSource = {
        buffer: null,
        onended: null,
        connect: vi.fn(),
        start: vi.fn(),
        stop: vi.fn(),
      };
      createdSources.push(source);
      return source;
    }),
    decodeAudioData: vi.fn(),
  } as unknown as AudioContext;
  return ctx;
}

// ---- tests ----

describe("sfx", () => {
  let ctx: AudioContext;

  beforeEach(() => {
    _resetForTest();
    createdSources = [];
    ctx = mockAudioContext();
    _setAudioContext(ctx);
  });

  describe("play", () => {
    it("fires a source for a cached buffer", () => {
      const buf = mockBuffer();
      _setBuffer("key-down", buf);

      play("key-down");

      expect(ctx.createBufferSource).toHaveBeenCalledTimes(1);
      expect(createdSources[0].connect).toHaveBeenCalledWith(ctx.destination);
      expect(createdSources[0].start).toHaveBeenCalledTimes(1);
      expect(createdSources[0].buffer).toBe(buf);
    });

    it("plays each trigger independently", () => {
      const names: SfxName[] = ["key-down", "key-up", "latch", "land", "file", "error"];
      for (const name of names) {
        _setBuffer(name, mockBuffer());
      }

      for (const name of names) {
        play(name);
      }

      expect(ctx.createBufferSource).toHaveBeenCalledTimes(6);
      for (const source of createdSources) {
        expect(source.start).toHaveBeenCalledTimes(1);
      }
    });
  });

  describe("pool cap", () => {
    it("evicts oldest when pool exceeds 3", () => {
      const buf = mockBuffer();
      _setBuffer("key-down", buf);

      // Play 4 times
      play("key-down");
      play("key-down");
      play("key-down");
      play("key-down");

      // 4 sources created
      expect(ctx.createBufferSource).toHaveBeenCalledTimes(4);

      // First source was stopped (evicted)
      expect(createdSources[0].stop).toHaveBeenCalledTimes(1);

      // Pool has at most 3
      expect(_getPool("key-down").length).toBeLessThanOrEqual(3);
    });

    it("pool tracks per sound name", () => {
      _setBuffer("key-down", mockBuffer());
      _setBuffer("key-up", mockBuffer());

      // 3 key-down + 2 key-up = 5 total, no eviction
      play("key-down");
      play("key-down");
      play("key-down");
      play("key-up");
      play("key-up");

      expect(_getPool("key-down").length).toBe(3);
      expect(_getPool("key-up").length).toBe(2);

      // No stop calls -- all within cap
      for (const source of createdSources) {
        expect(source.stop).not.toHaveBeenCalled();
      }
    });
  });

  describe("toggle mute", () => {
    it("setSfxEnabled(false) silences play", () => {
      _setBuffer("land", mockBuffer());
      setSfxEnabled(false);

      play("land");

      expect(ctx.createBufferSource).not.toHaveBeenCalled();
      expect(isMuted()).toBe(true);
    });

    it("setSfxEnabled(true) re-enables play", () => {
      _setBuffer("land", mockBuffer());
      setSfxEnabled(false);
      setSfxEnabled(true);

      play("land");

      expect(ctx.createBufferSource).toHaveBeenCalledTimes(1);
      expect(isMuted()).toBe(false);
    });

    it("toggleSfx notifies listeners", () => {
      const cb = vi.fn();
      const unsub = subscribeSfxEnabled(cb);

      toggleSfx(false);
      expect(cb).toHaveBeenCalledWith(false);

      toggleSfx(true);
      expect(cb).toHaveBeenCalledWith(true);

      unsub();
      toggleSfx(false);
      // Should not receive after unsub
      expect(cb).toHaveBeenCalledTimes(2);
    });
  });

  describe("reduced-motion mute", () => {
    it("mutes when reduced-motion is active regardless of toggle", () => {
      _setBuffer("file", mockBuffer());
      _setReducedMotion(true);

      play("file");

      expect(ctx.createBufferSource).not.toHaveBeenCalled();
      expect(isMuted()).toBe(true);
    });

    it("un-mutes when reduced-motion clears", () => {
      _setBuffer("file", mockBuffer());
      _setReducedMotion(true);
      _setReducedMotion(false);

      play("file");

      expect(ctx.createBufferSource).toHaveBeenCalledTimes(1);
      expect(isMuted()).toBe(false);
    });
  });

  describe("source cleanup", () => {
    it("removes ended sources from the pool", () => {
      _setBuffer("latch", mockBuffer());

      play("latch");
      expect(_getPool("latch").length).toBe(1);

      // Simulate the source ending
      const source = createdSources[0];
      source.onended?.();

      expect(_getPool("latch").length).toBe(0);
    });
  });
});
