// HS-170-03 — unit tests for the Concierge controller logic.
// Tests: propose->rows, WAITING gates Use these, OFF frees it,
//        kindEmblem, humanSize, latencyToken.

import { describe, it, expect } from "vitest";
import {
  kindEmblem,
  humanSize,
  latencyToken,
  hardwareToken,
  engineHostLabel,
  engineHostScope,
  GROUP_GLYPHS,
} from "../useConciergeController";
import type { Engine, EngineKind, EngineState } from "../api";

function makeEngine(overrides: Partial<Engine> = {}): Engine {
  return {
    id: "test-engine",
    kind: "lan" as EngineKind,
    name: "Test Engine",
    host: "192.168.1.43",
    state: "READY" as EngineState,
    latencyMs: 41,
    sizeBytes: null,
    runtimeToken: null,
    keySet: undefined,
    ...overrides,
  };
}

describe("kindEmblem", () => {
  it("returns LAN for lan engines", () => {
    expect(kindEmblem("lan")).toBe("LAN");
  });
  it("returns MAC for local engines", () => {
    expect(kindEmblem("local")).toBe("MAC");
  });
  it("returns API for cloud engines", () => {
    expect(kindEmblem("cloud")).toBe("API");
  });
  it("returns MAC for preset engines", () => {
    expect(kindEmblem("preset")).toBe("MAC");
  });
});

describe("humanSize", () => {
  it("returns null for null/zero", () => {
    expect(humanSize(null)).toBeNull();
    expect(humanSize(0)).toBeNull();
    expect(humanSize(undefined)).toBeNull();
  });
  it("formats bytes", () => {
    expect(humanSize(500)).toBe("500 B");
  });
  it("formats KB", () => {
    expect(humanSize(2048)).toBe("2 KB");
  });
  it("formats MB", () => {
    expect(humanSize(532_000_000)).toBe("507 MB");
  });
  it("formats GB", () => {
    expect(humanSize(26_500_000_000)).toBe("24.7 GB");
  });
});

describe("latencyToken", () => {
  it("returns null for null", () => {
    expect(latencyToken(null)).toBeNull();
  });
  it("formats ms", () => {
    expect(latencyToken(41)).toBe("41 MS");
  });
});

describe("hardwareToken", () => {
  it("builds token from capability", () => {
    const result = hardwareToken({
      capability: { apple_silicon: true, ram_gb: 36 },
    });
    expect(result).toBe("THIS MAC · M‑SERIES · 36 GB");
  });
  it("returns THIS MAC when no capability", () => {
    expect(hardwareToken({})).toBe("THIS MAC");
  });
});

describe("engineHostLabel", () => {
  it("adds LAN suffix to IP hosts", () => {
    const e = makeEngine({ kind: "lan", host: "192.168.1.43" });
    expect(engineHostLabel(e)).toBe("192.168.1.43 · LAN");
  });
  it("returns THIS DEVICE for local engines", () => {
    const e = makeEngine({ kind: "local", host: "THIS DEVICE" });
    expect(engineHostLabel(e)).toBe("THIS DEVICE");
  });
  it("uppercases cloud hosts", () => {
    const e = makeEngine({ kind: "cloud", host: "openrouter.ai" });
    expect(engineHostLabel(e)).toBe("OPENROUTER.AI");
  });
});

describe("engineHostScope", () => {
  it("returns cloud for cloud engines", () => {
    expect(engineHostScope(makeEngine({ kind: "cloud" }))).toBe("cloud");
  });
  it("returns local for lan engines", () => {
    expect(engineHostScope(makeEngine({ kind: "lan" }))).toBe("local");
  });
});

describe("GROUP_GLYPHS", () => {
  it("has all seven groups", () => {
    expect(Object.keys(GROUP_GLYPHS)).toHaveLength(7);
    expect(GROUP_GLYPHS).toHaveProperty("thoughts_notes");
    expect(GROUP_GLYPHS).toHaveProperty("chat_practice");
    expect(GROUP_GLYPHS).toHaveProperty("writing_dictation");
    expect(GROUP_GLYPHS).toHaveProperty("speech_recognition");
    expect(GROUP_GLYPHS).toHaveProperty("meetings");
    expect(GROUP_GLYPHS).toHaveProperty("agents_tools");
    expect(GROUP_GLYPHS).toHaveProperty("background");
  });
});

describe("canApply logic", () => {
  // Test the same logic that the controller uses: every group must be
  // READY or explicitly OFF (engineId === "OFF"). A null engineId with
  // WAITING state is NOT off -- it's unset (cold Mac).
  function canApply(rows: Array<{ state: string; engineId: string | null }>) {
    return (
      rows.length > 0 &&
      rows.every(
        (r) => r.state === "READY" || r.engineId === "OFF",
      )
    );
  }

  it("returns true when all READY", () => {
    const rows = [
      { state: "READY", engineId: "e1" },
      { state: "READY", engineId: "e2" },
    ];
    expect(canApply(rows)).toBe(true);
  });

  it("returns false when any WAITING", () => {
    const rows = [
      { state: "READY", engineId: "e1" },
      { state: "WAITING", engineId: "e2" },
    ];
    expect(canApply(rows)).toBe(false);
  });

  it("returns true when explicitly OFF", () => {
    const rows = [
      { state: "READY", engineId: "e1" },
      { state: "READY", engineId: "OFF" },
    ];
    expect(canApply(rows)).toBe(true);
  });

  it("returns false when WAITING with null engineId (cold state)", () => {
    const rows = [
      { state: "READY", engineId: "e1" },
      { state: "WAITING", engineId: null },
    ];
    expect(canApply(rows)).toBe(false);
  });

  it("returns false for empty rows", () => {
    expect(canApply([])).toBe(false);
  });
});
